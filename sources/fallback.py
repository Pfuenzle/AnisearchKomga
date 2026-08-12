from sources.base import MetadataResult, MetadataSource


class FallbackSource(MetadataSource):
    """Tries each source in order, returning the first valid result."""

    def __init__(self, sources):
        self.sources = sources

    def fetch(self, query):
        for source in self.sources:
            result = source.fetch(query)
            if result.isvalid:
                return result
            print("No result from this source, trying next one...")
        return MetadataResult()

    def close(self):
        for source in self.sources:
            source.close()
