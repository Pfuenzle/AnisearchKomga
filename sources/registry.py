from sources.anisearch import AniSearchSource
from sources.mangacore import MangacoreSource


def build_source(name, config):
    key = name.strip().lower()
    if key == "anisearch":
        return AniSearchSource(config.anisearchlang)
    if key == "mangacore":
        return MangacoreSource(config.mangacoreapikey, config.anisearchlang)
    raise ValueError("Unknown metadata source: " + name)


def build_sources(config):
    return [build_source(name, config) for name in config.sources]
