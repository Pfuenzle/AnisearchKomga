from abc import ABC, abstractmethod


class VolumeMetadata:
    """Per-volume/book metadata, as some sources (e.g. Mangacore) provide a summary per volume."""

    def __init__(self, number, summary="", isbn="", release_date=None):
        self.number = number
        self.summary = summary
        self.isbn = isbn
        self.release_date = release_date


class MetadataResult:
    def __init__(self, status=None, summary="", publisher="", genres=None, tags=None, volumes=None, isvalid=False):
        self.status = status
        self.summary = summary
        self.publisher = publisher
        self.genres = genres or []
        self.tags = tags or []
        self.volumes = volumes or []
        self.isvalid = isvalid


class MetadataSource(ABC):
    """A source that can look up manga metadata by series name."""

    @abstractmethod
    def fetch(self, query):
        """Return a MetadataResult for the given series name."""
        raise NotImplementedError

    def close(self):
        """Release any resources held by the source (browser, sessions, ...)."""
        pass
