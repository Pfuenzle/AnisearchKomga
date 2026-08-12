"""Standalone script: scrape a known Anisearch page and check the parsed fields against a
snapshot of known-correct values (see EXPECTED below). Re-run after Anisearch changes its
page layout, to see exactly what broke.

Not part of the automated pipeline - run manually: python anisearch_test.py
"""

from sources.anisearch import AniSearchSource

QUERY = "One Piece"
SLUG = "manga/724,one-piece"

# Snapshot of known-correct values, captured from the live page. Genres/tags are checked as
# "contains at least these", not exact equality, since Anisearch adds new ones over time.
EXPECTED = {
    "German": {
        "status": "ONGOING",
        "publisher": "Carlsen Manga, Shuueisha Inc.",
        "summary_prefix": "Reichtum, Macht und Ruhm",
        "genres_contains": ["Fighting-Shounen", "Abenteuer", "Action"],
        "tags_contains": ["Pirat", "Tsundere", "Monster"],
    },
    "English": {
        "status": "ONGOING",
        "publisher": "VIZ Media, LLC, Shuueisha Inc.",
        "summary_prefix": "Wealth, power and fame",
        "genres_contains": ["Fighting-Shounen", "Adventure", "Action"],
        "tags_contains": ["Pirate", "Tsundere", "Monster"],
    },
    "Spanish": {
        "status": "ONGOING",
        "publisher": "Editorial Planeta DeAgostini S.A., Panini México SA, Editorial Ivrea S.A., Shuueisha Inc., LARP Editores S.A.",
        "summary_prefix": "Cuando tenía 7 años",
        "genres_contains": ["Fighting-Shounen", "Aventura", "Acción"],
        "tags_contains": ["Pirata", "Tsundere", "Monstruos"],
    },
}


def check(expected, actual):
    search_ok = SLUG in actual["search_url"]
    checks = [
        ("search finds " + QUERY, SLUG, actual["search_url"], search_ok),
        ("status", expected["status"], actual["status"], expected["status"] == actual["status"]),
        ("publisher", expected["publisher"], actual["publisher"], expected["publisher"] == actual["publisher"]),
    ]

    summary_head = actual["summary"][:len(expected["summary_prefix"])]
    checks.append(("summary starts with", expected["summary_prefix"], summary_head, summary_head == expected["summary_prefix"]))

    missing_genres = [g for g in expected["genres_contains"] if g not in actual["genres"]]
    checks.append(("genres contain", expected["genres_contains"], actual["genres"], not missing_genres))

    missing_tags = [t for t in expected["tags_contains"] if t not in actual["tags"]]
    checks.append(("tags contain", expected["tags_contains"], actual["tags"], not missing_tags))

    return checks


def run(language):
    print("=" * 70)
    print("Language:", language)
    source = AniSearchSource(language)
    try:
        search_url = source._search(QUERY)
        print("search url:", search_url)

        html_dom = source._load_page(source.base_url + SLUG)
        if html_dom is None:
            print("FAILED to load page")
            return language, [("page load", "success", "failed", False)]

        right_index, status_index, publisher_index = source._find_language_index(html_dom)
        status = source._parse_status(html_dom, right_index, status_index)
        summary = source._parse_summary(html_dom)
        publisher = source._parse_publisher(html_dom, right_index, publisher_index)
        genres, tags = source._parse_genres_and_tags(html_dom)

        print("status:", status)
        print("publisher:", publisher)
        print("summary length:", len(summary))
        print("genres:", genres)
        print("tags:", tags)

        actual = {
            "search_url": search_url,
            "status": status,
            "publisher": publisher,
            "summary": summary,
            "genres": genres,
            "tags": tags,
        }
        return language, check(EXPECTED[language], actual)
    finally:
        source.close()


def print_overview(all_checks):
    print()
    print("=" * 70)
    print("OVERVIEW")
    print("=" * 70)
    overall_ok = True
    for language, checks in all_checks:
        print()
        print(language + ":")
        for name, expected, actual, ok in checks:
            mark = "OK  " if ok else "FAIL"
            print(" [" + mark + "] " + name)
            if not ok:
                overall_ok = False
                print("        expected:", expected)
                print("        actual:  ", actual)

    print()
    print("RESULT:", "ALL CHECKS PASSED" if overall_ok else "SOME CHECKS FAILED - scraper needs fixing")


if __name__ == "__main__":
    all_checks = [run(lang) for lang in ["German", "English", "Spanish"]]
    print_overview(all_checks)
