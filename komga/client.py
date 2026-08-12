import requests


class KomgaClient:
    def __init__(self, base_url, api_key=""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def using_api_key(self):
        return bool(self.api_key)

    def _auth(self):
        headers = {"Content-Type": "application/json", "accept": "*/*"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            return headers, None
        return headers, None

    def get_series(self, size=50000, library_ids=None):
        headers, auth = self._auth()
        params = {"size": size}
        if library_ids:
            params["library_id"] = library_ids
        response = requests.get(
            self.base_url + "/api/v1/series",
            params=params,
            headers=headers,
            auth=auth,
        )
        return response.json()

    def get_books_by_series(self, series_id, size=5000):
        headers, auth = self._auth()
        response = requests.get(
            self.base_url + "/api/v1/series/" + str(series_id) + "/books?size=" + str(size),
            headers=headers,
            auth=auth,
        )
        return response.json()

    def patch_book_metadata(self, book_id, volume):
        headers, auth = self._auth()
        payload = {
            "summary": volume.summary,
            "summaryLock": True,
            "isbn": volume.isbn,
            "isbnLock": True,
        }
        if volume.release_date:
            payload["releaseDate"] = volume.release_date
            payload["releaseDateLock"] = True
        return requests.patch(
            self.base_url + "/api/v1/books/" + str(book_id) + "/metadata",
            json=payload,
            headers=headers,
            auth=auth,
        )

    def patch_series_metadata(self, series_id, metadata):
        headers, auth = self._auth()
        payload = {
            "status": metadata.status,
            "statusLock": True,
            "summary": metadata.summary,
            "summaryLock": True,
            "publisher": metadata.publisher,
            "publisherLock": True,
            "genres": metadata.genres,
            "genresLock": True,
            "tags": metadata.tags,
            "tagsLock": True,
        }
        return requests.patch(
            self.base_url + "/api/v1/series/" + str(series_id) + "/metadata",
            json=payload,
            headers=headers,
            auth=auth,
        )
