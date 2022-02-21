# Anisearch metadata scraper for Komga

## Introduction
This Script gets a list of every manga available on your Komga instance,
looks it up one after another on [Anisearch](https://www.anisearch.com/) and gets the metadata for the specific series.
This metadata then gets converted to be compatible to Komga and then gets sent to the server instance and added to the manga entry.

See below for a list of supported attributes and languages

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


## Getting started (Native)

1. Install the requirements using `pip install -r requirements.txt`
2. Init Playwright using `playwright install`
3. Rename `config.template.py` to `config.py` and edit the url, email and password to match the ones of your komga instance (User needs to have permission to edit the metadata)
4. Run the script using `python mangaMetadata.py`


## Getting started (Docker)
1. Run the docker image (replace the url, email and password with the one of your Komga instance (user needs to have permission to edit the metadata)) using
```
docker run \
  -e KOMGAURL=https://komga.com \
  -e KOMGAEMAIL=adminemail@komga.com \
  -e KOMGAPASSWORD=12345 \
  -e LANGUAGE=German \
  --name anisearchkomga \
  pfuenzle/anisearchkomga:latest
```
Hint: Replace "\" with "`"  when using Powershell
