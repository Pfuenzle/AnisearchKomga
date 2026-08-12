"""Standalone script: query the live Mangacore API for a known series and check the parsed
fields against a snapshot of known-correct values (see EXPECTED below). Re-run after Mangacore
changes its API, to see exactly what broke.

Needs a real config.py with a working `mangacoreapikey`. Not part of the automated pipeline.
Usage: python mangacore_test.py
"""

import config
from sources.mangacore import MangacoreSource

QUERY = "5 Seconds to Death"

# Snapshot of known-correct values, captured from the live API. Genres/tags are checked as
# "contains at least these", not exact equality, since Mangacore's data keeps growing.
EXPECTED = {
    "status": "ONGOING",
    "publisher": "Egmont Manga",
    "genres_contains": ["Mystery", "Drama", "Supernatural", "Action"],
    "tags_contains": ["Shounen"],
    "min_volumes": 20,
    "volume_1": {
        "isbn": "9783-7704-9761-4",
        "release_date": "2018-05-03",
        "summary_prefix": "Der neue Mystery-Hit vom Zeichner von Testament of Sister New Devil",
    },
}


def check(expected, result):
    checks = [
        ("status", expected["status"], result.status, expected["status"] == result.status),
        ("publisher", expected["publisher"], result.publisher, expected["publisher"] == result.publisher),
    ]

    missing_genres = [g for g in expected["genres_contains"] if g not in result.genres]
    checks.append(("genres contain", expected["genres_contains"], result.genres, not missing_genres))

    missing_tags = [t for t in expected["tags_contains"] if t not in result.tags]
    checks.append(("tags contain", expected["tags_contains"], result.tags, not missing_tags))

    volume_count_ok = len(result.volumes) >= expected["min_volumes"]
    checks.append(("volume count >=", expected["min_volumes"], len(result.volumes), volume_count_ok))

    volume_1 = next((v for v in result.volumes if v.number == 1), None)
    if volume_1 is None:
        checks.append(("volume 1 exists", True, False, False))
        return checks

    exp = expected["volume_1"]
    checks.append(("volume 1 isbn", exp["isbn"], volume_1.isbn, exp["isbn"] == volume_1.isbn))
    checks.append(("volume 1 release_date", exp["release_date"], volume_1.release_date, exp["release_date"] == volume_1.release_date))

    summary_head = volume_1.summary[:len(exp["summary_prefix"])]
    checks.append(("volume 1 summary starts with", exp["summary_prefix"], summary_head, summary_head == exp["summary_prefix"]))

    return checks


def print_overview(checks):
    print()
    print("=" * 70)
    print("OVERVIEW")
    print("=" * 70)
    overall_ok = True
    for name, expected, actual, ok in checks:
        mark = "OK  " if ok else "FAIL"
        print(" [" + mark + "] " + name)
        if not ok:
            overall_ok = False
            print("        expected:", expected)
            print("        actual:  ", actual)

    print()
    print("RESULT:", "ALL CHECKS PASSED" if overall_ok else "SOME CHECKS FAILED - source needs fixing")


if __name__ == "__main__":
    source = MangacoreSource(config.mangacoreapikey, "German")
    result = source.fetch(QUERY)

    print("isvalid:", result.isvalid)
    print("status:", result.status)
    print("publisher:", result.publisher)
    print("genres:", result.genres)
    print("tags:", result.tags)
    print("volumes:", len(result.volumes))

    if not result.isvalid:
        print("FAILED to fetch metadata")
    else:
        print_overview(check(EXPECTED, result))
