# Metadata scraper for Komga

## Introduction
This Script gets a list of every manga available on your Komga instance,
looks it up one after another on one or more metadata sources and gets the metadata for the specific series.
This metadata then gets converted to be compatible to Komga and then gets sent to the server instance and added to the manga entry.

See below for a list of supported attributes, sources and languages

## Supported Sources
Configured via `sources` (config.py) or `SOURCES` (env/docker), as a list/comma-separated list, e.g. `["Anisearch", "Mangacore"]` or `SOURCES=Anisearch,Mangacore`.

Sources are tried in the given order per manga; the first source that finds a match is used, the others act purely as fallback (their results are not merged with an earlier match).

- **Anisearch** ([anisearch.com](https://www.anisearch.com/)) - scraped, supports all languages listed below. Default if `sources` is not set.
- **Mangacore** ([api.mangacore.moe](https://api.mangacore.moe/api/docs)) - uses a personal API token (`mangacoreapikey` / `MANGACOREAPIKEY`), set as a `Bearer` token. In addition to the series-level attributes, Mangacore sometimes has a summary, ISBN and release date per volume/edition - if present, these get pushed to the matching book in Komga (matched via the book's volume number).

## Running Mode
By default, the script runs once, updates every manga it can, and exits - suitable for a one-off container run, a cron job, or a scheduled task.

Set `intervalDays` (config.py) or `INTERVALDAYS` (env/docker) to a number greater than 0 to instead keep the container running permanently, repeating the whole run every N days. When using this mode with Docker, also set a restart policy (e.g. `restart: unless-stopped`) so the container comes back up after a crash or host reboot.

## Daemon Mode
For large libraries where running a full scan on a schedule is wasteful, set `daemon` (config.py) or `DAEMON` (env/docker) to `True`/`1` to keep the container running permanently and check every hour for series that haven't been touched yet (i.e. newly added to your Komga library) - if there are any, they get updated right away; if not, it just waits for the next hourly check. This requires `keepProgress` to tell new series apart from already-updated ones, and gets enabled automatically if it wasn't already.

Combine daemon mode with `intervalDays`/`INTERVALDAYS` to additionally do a full library rescan on that interval (ignoring progress tracking for that one run), to catch metadata changes on series that were already updated. Leave `intervalDays` at `0` to only ever do the hourly new-series check.

## Search query fallback
Each series is first looked up by its Komga series `name` (the folder name). If none of the configured sources find a match for that, it's retried once using the series' Komga `title` metadata instead (Metadata tab of the series in the Komga UI). This lets you fix an unmatched series without touching the filesystem or the Komga database directly - just edit the title in Komga to whatever the source(s) would recognize, and it'll be picked up on the next run.

## Restricting to specific libraries
If your Komga instance has multiple libraries and only some of them contain manga (e.g. a separate library for western comics), set `libraries` (config.py) or `LIBRARIES` (env/docker) to a list/comma-separated list of Komga library IDs to only scan those. Leave empty (default) to scan every library. Library IDs are visible in the Komga UI's URL when browsing a library, or via Komga's own API.

## Requirements
- A Komga instance with access to the admin account
- Either Windows/Linux/MAc or alternatively Docker
- Python installed if using Windows, Linux or Mac natively

## Supported Languages
These languages have to be set in the config under `anisearchlang`.

If the chosen language has no summary available, the english summary will be used.
For status and publisher the japanese metadata will be used as a fallback.

I tried to test the languages as best as I could, but if I missed something please make an Issue and tell me whats wrong :)

- German
- English
- Spanish
- French
- Italian
- Japanese


## Parsed Attributes
- [x] Status
- [x] Summary
- [x] Publisher
- [ ] Age rating (not supported for now, does Anisearch even have this?)
- [x] Genres
- [x] Tags
- [x] Per-volume summary/ISBN/release date (Mangacore only, when available)


## Getting started (Native)

1. Install the requirements using `pip install -r requirements.txt`
2. Init Playwright using `playwright install`
3. Rename `config.template.py` to `config.py` and set `komgaurl` plus your Komga `komgaapikey` (the value from your Komga API key). The script authenticates with the `X-API-Key` header, which is the recommended Komga method for API access.
The "mangas" array can be filled with the names of mangas which are supposed to be updated, if it is left empty every manga will be updated.
"keepProgress" can be set to either "True" or "False". If it is set to true, successfully updated Mangas will be stored in a list and not be updated on the next run.
"sources" selects which metadata source(s) to use, and in which order (see [Supported Sources](#supported-sources)). If "Mangacore" is used, "mangacoreapikey" also has to be set.
"intervalDays" controls the [Running Mode](#running-mode) - 0 (default) runs once and exits, a number of days keeps it running and repeating.
"daemon" enables [Daemon Mode](#daemon-mode) - checks hourly for newly added series instead of running on a fixed schedule.
"libraries" restricts the scan to specific Komga libraries (see [Restricting to specific libraries](#restricting-to-specific-libraries)), if left empty every library is scanned.
4. Run the script using `python mangaMetadata.py`


## Getting started (Docker)
1. Run the docker image (replace the URL and API key with the values of your Komga instance; the user needs permission to edit metadata) using
```
docker run \
  -e KOMGAURL=https://komga.com \
  -e KOMGAAPIKEY=your-komga-api-key \
  -e LANGUAGE=German \
  --name anisearchkomga \
  pfuenzle/anisearchkomga:latest
```
Hint: Replace \ with `  when using Powershell

Alternatively, you could run the docker-compose to get a running container with progress tracking

### Additional Environment Variables
- `KOMGAAPIKEY=...` - Komga API key used in the `X-API-Key` request header for authentication.
- `MANGAS="Manga1,Manga2"` - This can be used to give a comma seperated list of mangas which are supposed to be updated. If it is left blank, every manga will be updated.
- `KEEPPROGRESS=True` - This can be set to either true or false. If it is set to true, a list of all successfully updated mangas will be saved and mangas in this list will not be updated on the next run. If you want to persist the list on the disk, you have to also add a volume as following: `-v /path/to/mangas.progress:/app/mangas.progress`, where `/path/to/mangas.progress` has to be replaced with the path to an empty existing file.
- `SOURCES="Anisearch,Mangacore"` - Comma separated list of metadata sources to use, tried in this order per manga (see [Supported Sources](#supported-sources)). Defaults to `Anisearch` if not set.
- `MANGACOREAPIKEY=...` - Required if `Mangacore` is part of `SOURCES`. Personal API token for [Mangacore](https://api.mangacore.moe/api/docs), sent as a `Bearer` token.
- `INTERVALDAYS=7` - See [Running Mode](#running-mode). Defaults to `0` (run once and exit) if not set.
- `DAEMON=1` - See [Daemon Mode](#daemon-mode). Defaults to off if not set.
- `LIBRARIES="libraryId1,libraryId2"` - See [Restricting to specific libraries](#restricting-to-specific-libraries). Every library is scanned if not set.