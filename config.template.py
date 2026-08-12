anisearchlang="German"
komgaurl="https://komga.com"
komgaapikey="your-komga-api-key"
mangas = []
keepProgress = True

# Optional: restrict to specific Komga libraries (by their library ID, as seen in the Komga UI/API).
# Leave empty to scan every library, e.g. if Anisearch/Mangacore don't have data for a comic-only library.
libraries = []

# One or more metadata sources, tried in order; the first one that finds a
# match for a given series wins, later ones are only used as fallback.
# Supported: "Anisearch", "Mangacore"
sources = ["Anisearch"]

# Required if "Mangacore" is in sources. Bearer token from your Mangacore account.
mangacoreapikey = "your-mangacore-api-token"

# 0 (default) = run once and exit, e.g. for a one-off container/cron job.
# Any positive number = keep the container running and repeat the whole run every N days.
intervalDays = 0

# False (default) = ignore the two settings below.
# True = keep the container running permanently, checking every hour for series that have never
# been touched (new additions to your library) and updating those right away. Requires
# keepProgress (enabled automatically if it isn't already), since that's how new series are told
# apart from ones already done. Combine with intervalDays for a full library rescan on top of the
# hourly check, to also catch changes to series that were already updated.
daemon = False