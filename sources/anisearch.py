import time

from lxml import etree
from lxml.etree import ParserError
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from sources.base import MetadataResult, MetadataSource

BASE_URLS = {
    "German": "https://www.anisearch.de/",
    "English": "https://www.anisearch.com/",
    "Spanish": "https://www.anisearch.es/",
    "French": "https://www.anisearch.fr/",
    "Italian": "https://www.anisearch.it/",
    "Japanese": "https://www.anisearch.jp/",
}

FLAG_LANGUAGES = {
    "German": "Deutsch",
    "English": "English",
    "Spanish": "Español",
    "French": "Français",
    "Italian": "Italiana",
    "Japanese": "日本語",
}

SUMMARY_SOURCE_MARKERS = [" Quelle: ", " Quelle:", "Quelle:", " Source: ", " Source:", "Source:"]
# Verbatim labels from Anisearch's own status filter (manga/index), one per SUPPORTED_LANGUAGES entry.
# Upcoming series count as ongoing here - Anisearch's data for not-yet-released volumes is often stale,
# and it's less wrong to call an upcoming series "ongoing" than to fall through to "ended".
UPCOMING_STATUS = ["Zukünftig", "Upcoming", "Futuro", "À l’avenir", "Futuro", "近日公開"]
RUNNING_STATUS = ["Laufend", "Ongoing", "Corriente", "En cours", "In corso", "放送（連載）中"]
ON_HOLD_STATUS = ["Pausiert", "On Hold", "Pausado", "En pause", "In pausa", "休止中"]
ABANDONED_STATUS = ["Abgebrochen", "Canceled", "Cancelado", "Annulé", "Cancellato", "中止"]
ENDED_STATUS = ["Abgeschlossen", "Completed", "Completado", "Terminé", "Completato", "完結"]
TAG_SECTION_MARKERS = ["Hauptgenres", "Main genres", "Género principal", "Principaux genres", "Generi principali", "メインジャンル"]
NO_SUMMARY_MARKERS = [
    "Damit hilfst Du der gesamten deutschsprachigen Anime und Manga-Community",
    "We’re looking forward to your contributions",
    "Con esto ayudas a toda la comunidad de Anime y Manga",
    "Nous attendons avec impatience tes contributions",
    "Non vediamo l’ora di ricevere i tuoi contributi",
    "皆様からのご投稿をお待ちしております",
]
BLURB_MARKERS = ["Klappentext", "Blurb", "Texto de presentación", "Texte du rabat", "Testo della bandella"]


class AniSearchSource(MetadataSource):
    def __init__(self, language):
        self.base_url = BASE_URLS[language]
        self.flag_language = FLAG_LANGUAGES[language]
        self.language = language
        self._playwright = sync_playwright().__enter__()
        self.browser = self._playwright.chromium.launch()
        self.page = self.browser.new_page()
        self.page.goto(self.base_url)

    def close(self):
        self.browser.close()
        self._playwright.stop()

    def fetch(self, query):
        print("Getting metadata for " + str(query))
        result = MetadataResult()

        url = self._search(query)
        if url == "":
            print("No result found or error occured")
            return result

        time.sleep(1)

        html_dom = self._load_page(url)
        if html_dom is None:
            return result

        right_index, status_index, publisher_index = self._find_language_index(html_dom)

        result.status = self._parse_status(html_dom, right_index, status_index)
        result.summary = self._parse_summary(html_dom)
        result.publisher = self._parse_publisher(html_dom, right_index, publisher_index)
        result.genres, result.tags = self._parse_genres_and_tags(html_dom)
        result.isvalid = True
        return result

    def _search(self, query):
        # The plain "manga/index?text=...&q=true" GET search got rejected by the site at some
        # point ("ungültige Suchanfrage"/invalid search query). The quick-search box now works
        # through a POST to /ajax/search/manga with a session-bound token, so drive the actual
        # search box instead of trying to reconstruct that request by hand.
        self.page.goto(self.base_url + "manga/index")
        try:
            with self.page.expect_response(
                lambda response: "/ajax/search/manga" in response.url, timeout=10000
            ) as response_info:
                self.page.fill("#qsearch", query)
            response = response_info.value
        except PlaywrightTimeoutError:
            print("Search request timed out")
            return ""

        if response.status != 200:
            print("Status code was " + str(response.status) + ", so skipping...")
            return ""

        try:
            data = response.json()
        except Exception as e:
            print(e)
            return ""

        for item in data.get("r", []):
            slug = item.get("u")
            if item.get("i") and slug:
                return self.base_url + "manga/" + slug

        return ""

    def _load_page(self, url):
        resp = self.page.goto(url)
        content = self.page.content()
        status_code = resp.status

        if status_code != 200:
            print("return code was " + str(status_code) + ", skipping...")
            return None
        return self._parse_html(content)

    @staticmethod
    def _parse_html(content):
        try:
            parser = etree.HTMLParser()
            return etree.HTML(content, parser)
        except ParserError as e:
            print(e)
            return None

    def _find_language_index(self, html_dom):
        default_index = (3, 6) if self.language == "Japanese" else (2, 5)
        index = 1
        while True:
            try:
                flag = html_dom.xpath(
                    "//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + str(index) + "]/div[1]/img/@title"
                )[0]
            except Exception:
                print("Failed to find set language, using first language as fallback")
                return "1", default_index[0], default_index[1]

            if flag == self.flag_language:
                return str(index), default_index[0], default_index[1]
            index += 1

    def _parse_status(self, html_dom, right_index, status_index):
        try:
            status_text = html_dom.xpath(
                "//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + right_index + "]/div[" + str(status_index) + "]"
            )[0].itertext()
            status_text = ''.join(status_text).split(": ")[1]
        except Exception:
            try:
                status_text = html_dom.xpath(
                    "//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[3]"
                )[0].itertext()
                status_text = ''.join(status_text).split(": ")[1]
            except Exception as e:
                print(e)
                print("Failed to get status")
                return None

        if status_text in RUNNING_STATUS or status_text in UPCOMING_STATUS:
            return "ONGOING"
        if status_text in ON_HOLD_STATUS:
            return "HIATUS"
        if status_text in ABANDONED_STATUS:
            return "ABANDONED"
        if status_text in ENDED_STATUS:
            return "ENDED"

        print("Unrecognized status \"" + status_text + "\", leaving status unset")
        return None

    def _parse_summary(self, html_dom):
        try:
            summary = html_dom.xpath("//*[@id=\"description\"]/div/div/div[1]")[0].itertext()
            summary = ''.join(summary)
            for marker in TAG_SECTION_MARKERS:
                if marker in summary:
                    raise ValueError
            for marker in NO_SUMMARY_MARKERS:
                if marker in summary:
                    raise ValueError
        except Exception:
            summary = self._parse_multi_language_summary(html_dom)

        if summary == "":
            return ""

        for blurb in BLURB_MARKERS:
            if blurb in summary.split(":")[0]:
                summary = summary[len(blurb):]

        summary_parts = summary.split(":")[:-1]
        summary = "".join(part + ":" for part in summary_parts)

        if summary[0:1] == ":":
            summary = summary[1:]

        for marker in SUMMARY_SOURCE_MARKERS:
            marker_len = len(marker)
            if summary[len(summary) - marker_len:] == marker:
                summary = summary[:len(summary) - marker_len]
                break

        return summary

    def _parse_multi_language_summary(self, html_dom):
        english_summary = ""
        language_summary = ""
        index = 1
        no_summary_available = False
        while True:
            try:
                summary = html_dom.xpath(
                    "//*[@id=\"description\"]/div/div/section/div[" + str(index) + "]"
                )[0].itertext()
                summary = ''.join(summary)
                summary_lang = html_dom.xpath(
                    "//*[@id=\"description\"]/div/div/section/button[" + str(index) + "]"
                )[0].itertext()
                summary_lang = ''.join(summary_lang)

                for marker in NO_SUMMARY_MARKERS:
                    if marker in summary:
                        print("No summary available for this language")
                        no_summary_available = True
                        continue

                if summary_lang == self.flag_language and not no_summary_available:
                    language_summary = summary
                    break
                elif summary_lang == "English":
                    english_summary = summary
                    if no_summary_available:
                        break
                index += 1
            except Exception:
                break

        return language_summary if language_summary != "" else english_summary

    def _parse_publisher(self, html_dom, right_index, publisher_index):
        try:
            publisher = html_dom.xpath(
                "//*[@id=\"information\"]/div/ul/li[2]/ul/li[" + right_index + "]/div[" + str(publisher_index) + "]"
            )[0].itertext()
            publisher = ''.join(publisher)
        except Exception:
            try:
                publisher = html_dom.xpath(
                    "//*[@id=\"information\"]/div/ul/li[2]/ul/li[1]/div[6]"
                )[0].itertext()
                publisher = ''.join(publisher)
            except Exception as e:
                print(e)
                print("Failed to get publisher")
                return ""

        if publisher == "":
            return ""
        return publisher.split(": ")[1]

    @staticmethod
    def _parse_genres_and_tags(html_dom):
        # Main genres use href "genre/main/...", subsidiary genres "genre/subsidiary/...",
        # and tags "genre/tag/..." - all three used to live under #description, now under #genres-tags.
        genres = []
        tags = []
        links = html_dom.xpath("//*[@id=\"genres-tags\"]//ul[contains(@class, \"cloud\")]/li/a")
        for link in links:
            text = ''.join(link.itertext())
            href = link.get("href") or ""
            target = tags if "/genre/tag/" in href else genres
            if text not in target:
                target.append(text)

        return genres, tags
