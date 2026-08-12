import sys
import time

from config_loader import load_config
from komga.client import KomgaClient
from progress import ProgressTracker
from sources.fallback import FallbackSource
from sources.registry import build_sources


class FailedSeries:
    def __init__(self, series_id, name, title):
        self.id = series_id
        self.name = name
        self.title = title


def update_series(komga, source, series_id, name, title):
    metadata = source.fetch(name)
    if not metadata.isvalid and title and title != name:
        print("No match for \"" + name + "\", retrying with Komga title \"" + title + "\"")
        metadata = source.fetch(title)
    if not metadata.isvalid:
        return None, metadata
    response = komga.patch_series_metadata(series_id, metadata)
    if metadata.volumes:
        update_volumes(komga, series_id, metadata.volumes)
    return response, metadata


def update_volumes(komga, series_id, volumes):
    try:
        books_page = komga.get_books_by_series(series_id)
    except Exception as e:
        print(e)
        print("Failed to fetch books for series, skipping volume metadata")
        return

    books_by_number = {}
    for book in books_page.get("content", []):
        number_sort = book.get("metadata", {}).get("numberSort")
        if number_sort is not None:
            books_by_number[float(number_sort)] = book

    for volume in volumes:
        try:
            book = books_by_number.get(float(volume.number))
        except (TypeError, ValueError):
            book = None
        if book is None:
            continue

        response = komga.patch_book_metadata(book["id"], volume)
        label = book.get("name", book["id"])
        if response.status_code == 204:
            print("Updated volume metadata for " + str(label))
        else:
            print("Failed to update volume metadata for " + str(label))
            print(response.status_code)
            print(response.text)


def process_series(komga, source, progress, failed_file, series_id, name, title):
    response, metadata = update_series(komga, source, series_id, name, title)

    if not metadata.isvalid:
        print("----------------------------------------------------")
        print("Failed to update " + str(name) + ", trying again at the end")
        print("----------------------------------------------------")
        failed_file.write(str(series_id) + name)
        time.sleep(10)
        return False

    if response.status_code == 204:
        print("----------------------------------------------------")
        print("Successfully updated " + str(name))
        print("----------------------------------------------------")
        progress.mark_done(series_id)
    else:
        print("----------------------------------------------------")
        print("Failed to update " + str(name) + ", trying again at the end")
        print("----------------------------------------------------")
        print(response.status_code)
        print(response.text)
        failed_file.write(str(series_id) + name)

    time.sleep(10)
    return response.status_code == 204


def retry_series(komga, source, progress, series_id, name, title):
    response, metadata = update_series(komga, source, series_id, name, title)

    if not metadata.isvalid:
        print("----------------------------------------------------")
        print("Failed again to update " + str(name) + ", not trying again")
        print("----------------------------------------------------")
        time.sleep(10)
        return

    if response.status_code == 204:
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Successfully updated " + str(name))
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
    else:
        print("----------------------------------------------------")
        print("Failed again to update " + str(name) + ", not trying again")
        print("----------------------------------------------------")

    progress.mark_done(series_id)
    time.sleep(10)


def run_once(config, force=False):
    komga = KomgaClient(config.komgaurl, config.komgaapikey)
    if komga.using_api_key():
        print("Using Komga API key authentication")

    try:
        series_page = komga.get_series(library_ids=config.libraries)
        expected = series_page["numberOfElements"]
    except Exception:
        print("Failed to get list of mangas, are the login infos correct?")
        return False

    print("Series to do: ")
    print(expected)

    source = FallbackSource(build_sources(config))
    progress = ProgressTracker(enabled=config.keep_progress)

    failed = []
    series_number = 0

    with open("failed.txt", "w") as failed_file:
        for series in series_page["content"]:
            series_number += 1
            name = series["name"]
            series_id = series["id"]
            title = series.get("metadata", {}).get("title") or name

            if config.mangas and name not in config.mangas:
                continue

            print("Number: " + str(series_number) + "/" + str(expected))

            if progress.is_done(series_id) and not force:
                print("Manga " + str(name) + " was already updated, skipping...")
                continue

            print("Updating: " + str(name))
            if not process_series(komga, source, progress, failed_file, series_id, name, title):
                failed.append(FailedSeries(series_id, name, title))

    for entry in failed:
        retry_series(komga, source, progress, entry.id, entry.name, entry.title)

    source.close()
    return True


DAEMON_TICK_SECONDS = 60 * 60


def run_daemon(config):
    full_rescan_seconds = config.interval_days * 24 * 60 * 60 if config.interval_days > 0 else None

    message = "Running in daemon mode: checking for new series every hour"
    if full_rescan_seconds:
        message += ", full library rescan every " + str(config.interval_days) + " day(s)"
    print(message)

    elapsed_since_full_rescan = 0
    while True:
        if full_rescan_seconds is not None and elapsed_since_full_rescan >= full_rescan_seconds:
            print("Running full library rescan")
            run_once(config, force=True)
            elapsed_since_full_rescan = 0
        else:
            run_once(config)

        time.sleep(DAEMON_TICK_SECONDS)
        elapsed_since_full_rescan += DAEMON_TICK_SECONDS


def main():
    config = load_config()

    if config.daemon:
        run_daemon(config)
        return

    if config.interval_days <= 0:
        if not run_once(config):
            sys.exit(1)
        return

    print("Running permanently, repeating every " + str(config.interval_days) + " day(s)")
    while True:
        run_once(config)
        print("Sleeping for " + str(config.interval_days) + " day(s) before the next run")
        time.sleep(config.interval_days * 24 * 60 * 60)


if __name__ == "__main__":
    main()
