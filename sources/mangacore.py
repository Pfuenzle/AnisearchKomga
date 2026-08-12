import requests

from sources.base import MetadataResult, MetadataSource, VolumeMetadata

BASE_URL = "https://api.mangacore.moe"

LANGUAGE_CODES = {
    "German": "de",
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Italian": "it",
    "Japanese": "ja",
}

# Status text isn't localized to the requested language (seen coming through in German, from
# Anisearch), and may also arrive in AniList's upstream vocabulary - cover both, upcoming counts
# as ongoing (see sources/anisearch.py for why), on-hold maps to Komga's HIATUS.
STATUS_UPCOMING = ["zukünftig", "upcoming", "futuro", "à l’avenir", "近日公開", "not_yet_released"]
STATUS_ONGOING = ["laufend", "ongoing", "corriente", "en cours", "in corso", "放送（連載）中", "releasing"]
STATUS_ON_HOLD = ["pausiert", "on hold", "pausado", "en pause", "in pausa", "休止中", "hiatus"]
STATUS_ABANDONED = ["abgebrochen", "canceled", "cancelled", "cancelado", "annulé", "cancellato", "中止"]
STATUS_ENDED = ["abgeschlossen", "completed", "completado", "terminé", "completato", "完結", "finished"]


class MangacoreSource(MetadataSource):
    def __init__(self, api_key, language=None):
        self.api_key = api_key
        self.language_code = LANGUAGE_CODES.get(language)

    def _headers(self):
        return {"Authorization": "Bearer " + self.api_key, "accept": "application/json"}

    def fetch(self, query):
        print("Getting metadata for " + str(query) + " (Mangacore)")
        result = MetadataResult()

        candidates = self._search(query)
        if not candidates:
            print("No result found or error occured")
            return result

        series = self._pick_best_candidate(candidates)
        if series is None:
            return result

        editions = series.get("editions") or []

        result.status = self._parse_status(series.get("status"))
        result.summary = series.get("summary") or ""
        result.genres = series.get("genres") or []
        result.tags = series.get("tags") or []
        result.publisher = self._pick_publisher(editions)
        result.volumes = self._collect_volumes(editions)
        result.isvalid = True
        return result

    def _search(self, query):
        try:
            response = requests.get(
                BASE_URL + "/api/v1/series",
                params={"q": query, "page_size": 5},
                headers=self._headers(),
            )
        except requests.RequestException as e:
            print(e)
            return []

        if response.status_code != 200:
            print("Status code was " + str(response.status_code) + ", so skipping...")
            return []

        return response.json().get("items") or []

    def _pick_best_candidate(self, candidates):
        # Mangacore can carry multiple unmerged series records for the same title
        # (fed by different upstream sources), with wildly different data richness -
        # e.g. one entry has real per-volume ISBN/summary data, another duplicate has none.
        # Fetch full detail for each candidate and keep the one that scores best.
        best_series = None
        best_score = -1
        for item in candidates:
            series = self._get_series_detail(item["series_id"])
            if series is None:
                continue
            score = self._score_candidate(series)
            if score > best_score:
                best_score = score
                best_series = series
        return best_series

    def _score_candidate(self, series):
        score = 0
        for edition in series.get("editions") or []:
            if self.language_code and edition.get("language") == self.language_code:
                score += 100
            for volume in edition.get("volumes") or []:
                if volume.get("isbn"):
                    score += 2
                if volume.get("summary"):
                    score += 1
        return score

    def _get_series_detail(self, series_id):
        try:
            response = requests.get(
                BASE_URL + "/api/v1/series/" + str(series_id),
                headers=self._headers(),
            )
        except requests.RequestException as e:
            print(e)
            return None

        if response.status_code != 200:
            print("Status code was " + str(response.status_code) + ", so skipping...")
            return None

        return response.json()

    def _preferred_editions(self, editions):
        if self.language_code:
            preferred = [e for e in editions if e.get("language") == self.language_code]
            if preferred:
                return preferred
        return editions

    def _pick_publisher(self, editions):
        for edition in self._preferred_editions(editions):
            if edition.get("publisher"):
                return edition["publisher"]
        return ""

    def _collect_volumes(self, editions):
        for edition in self._preferred_editions(editions):
            volumes = [v for v in (edition.get("volumes") or []) if v.get("summary")]
            if volumes:
                return [self._to_volume_metadata(v) for v in volumes]
        return []

    @staticmethod
    def _to_volume_metadata(volume):
        release_date = None
        year = volume.get("release_year")
        if year:
            month = volume.get("release_month") or 1
            day = volume.get("release_day") or 1
            release_date = "%04d-%02d-%02d" % (year, month, day)
        return VolumeMetadata(
            number=volume.get("number"),
            summary=volume.get("summary") or "",
            isbn=volume.get("isbn") or "",
            release_date=release_date,
        )

    @staticmethod
    def _parse_status(status):
        if not status:
            return None
        normalized = status.strip().lower()
        if normalized in STATUS_ONGOING or normalized in STATUS_UPCOMING:
            return "ONGOING"
        if normalized in STATUS_ON_HOLD:
            return "HIATUS"
        if normalized in STATUS_ABANDONED:
            return "ABANDONED"
        if normalized in STATUS_ENDED:
            return "ENDED"
        return None
