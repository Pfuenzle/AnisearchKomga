import os
import sys

SUPPORTED_LANGUAGES = ["German", "English", "Spanish", "French", "Italian", "Japanese"]
SUPPORTED_SOURCES = ["anisearch", "mangacore"]
DEFAULT_SOURCES = ["anisearch"]


class Config:
    def __init__(self, komgaurl, komgaapikey, anisearchlang,
                 keep_progress, mangas, sources, mangacoreapikey, interval_days, libraries, daemon):
        self.komgaurl = komgaurl
        self.komgaapikey = komgaapikey
        self.anisearchlang = anisearchlang
        self.keep_progress = keep_progress
        self.mangas = mangas
        self.sources = sources
        self.mangacoreapikey = mangacoreapikey
        self.interval_days = interval_days
        self.libraries = libraries
        self.daemon = daemon


def _parse_list(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_interval_days(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        print("intervalDays / INTERVALDAYS must be a whole number of days")
        sys.exit(1)


def _from_env():
    env_url = os.environ.get("KOMGAURL", "")
    env_api_key = os.environ.get("KOMGAAPIKEY", "")

    if env_url == env_api_key == "":
        return None

    if env_url == "" or (env_api_key == ""):
        print("Looks like either you are trying to set the configuration using environment variables or you are using docker.")
        if env_url == "":
            print("Missing Komga URL")
        if env_api_key == "":
            print("Missing Komga API key")
        sys.exit(1)

    env_lang = os.environ.get("LANGUAGE", "")
    env_mangas = os.environ.get("MANGAS", "NONE")
    env_progress = os.environ.get("KEEPPROGRESS", "").lower() == "true"
    env_sources = os.environ.get("SOURCES", "")
    env_mangacore_key = os.environ.get("MANGACOREAPIKEY", "")
    env_interval_days = _parse_interval_days(os.environ.get("INTERVALDAYS", "0"))
    env_libraries = os.environ.get("LIBRARIES", "NONE")
    env_daemon = os.environ.get("DAEMON", "").lower() in ("1", "true")

    mangas = _parse_list(env_mangas) if env_mangas != "NONE" else []
    sources = [s.lower() for s in _parse_list(env_sources)] or DEFAULT_SOURCES
    libraries = _parse_list(env_libraries) if env_libraries != "NONE" else []

    return Config(env_url, env_api_key, env_lang, env_progress, mangas, sources, env_mangacore_key, env_interval_days, libraries, env_daemon)


def _from_file():
    try:
        import config as user_config
    except ImportError:
        print("Failed to find config.py, does it exist?")
        sys.exit(1)

    sources = [s.lower() for s in getattr(user_config, "sources", DEFAULT_SOURCES)]

    return Config(
        komgaurl=user_config.komgaurl,
        komgaapikey=getattr(user_config, "komgaapikey", ""),
        anisearchlang=getattr(user_config, "anisearchlang", ""),
        keep_progress=getattr(user_config, "keepProgress", False),
        mangas=getattr(user_config, "mangas", []),
        sources=sources,
        mangacoreapikey=getattr(user_config, "mangacoreapikey", ""),
        interval_days=_parse_interval_days(getattr(user_config, "intervalDays", 0)),
        libraries=getattr(user_config, "libraries", []),
        daemon=bool(getattr(user_config, "daemon", False)),
    )


def load_config():
    config = _from_env() or _from_file()

    for source in config.sources:
        if source not in SUPPORTED_SOURCES:
            print("Invalid source \"" + source + "\", select one or more of: " + ", ".join(SUPPORTED_SOURCES))
            sys.exit(1)

    if not config.sources:
        print("No metadata source configured, select one or more of: " + ", ".join(SUPPORTED_SOURCES))
        sys.exit(1)

    if "anisearch" in config.sources and config.anisearchlang not in SUPPORTED_LANGUAGES:
        print("Invalid language, select one listed the README")
        sys.exit(1)

    if "mangacore" in config.sources and not config.mangacoreapikey:
        print("Missing Mangacore API token")
        sys.exit(1)

    if config.interval_days < 0:
        print("intervalDays / INTERVALDAYS can't be negative")
        sys.exit(1)

    if config.daemon and not config.keep_progress:
        print("Daemon mode needs keepProgress/KEEPPROGRESS to tell new series apart from already-updated ones - enabling it")
        config.keep_progress = True

    return config
