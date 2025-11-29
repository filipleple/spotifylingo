# Spotifylingo

## 1. High level purpose

Pipeline for one user:

1. Authenticate to Spotify with a short lived token from `.env`.
2. Fetch that user’s top tracks.
3. Heuristically select tracks in a target language.
4. For those tracks, fetch lyrics from Genius and scrape text.
5. (Planned) Cache lyrics and metadata in a database and later derive vocab flashcards.

Right now you have a working end to end pipeline up to step 4, entirely in scripts and pure Python modules.

---

## 2. Project structure and responsibilities

Top level:

* `pyproject.toml`

  * Defines the project as an installable package with `src` layout.
  * Declares dependencies: `requests`, `python-dotenv`, `langdetect`, `beautifulsoup4` and others.
  * Critical for imports to work (`pip install -e .`).

* `.env` and `.env.example`

  * `.env.example` documents required environment variables.
  * `.env` (ignored from VCS) has real values.
  * Currently used vars:

    * `SPOTIFY_ACCESS_TOKEN`
    * `GENIUS_ACCESS_TOKEN`
    * (Planned) `DATABASE_URL`

* `scripts/`

  * Contains thin command line entrypoints for manual runs and experiments.
  * Must not contain real business logic.

* `src/spotify_vocab/`

  * All reusable code lives here.
  * This is what will later back your FastAPI app and any background jobs.

* `tests/`

  * Placeholder for unit tests.

---

## 3. Core modules

### 3.1 `config.py`

Responsibility:

* Central place for configuration and environment variable access.
* Defines typed config objects and returns them via functions.

Current elements:

* `SpotifyConfig` and `get_spotify_config()`

  * Reads `SPOTIFY_ACCESS_TOKEN`.
  * Holds defaults for `time_range` and `limit`.

* `GeniusConfig` and `get_genius_config()`

  * Reads `GENIUS_ACCESS_TOKEN`.
  * Holds base URL for Genius API.

* (Planned) `DatabaseConfig` and `get_database_config()`

  * Will read `DATABASE_URL`.
  * Used by SQLAlchemy setup.

Key point: all secrets and environment setup pass through this module, nowhere else.

---

### 3.2 `models.py`

Responsibility:

* Internal, API independent representations of your domain objects.

Current elements:

* `Artist` dataclass

  * `id`, `name`.

* `Track` dataclass

  * `id` (Spotify track id).
  * `name`.
  * `artists: list[Artist]`.
  * `uri`, `href`, `preview_url`.
  * `display_name` property that formats `"{track} by {artists}"`.

You never pass raw Spotify JSON around. You convert it once in `spotify_client` and then work with these models.

---

### 3.3 `spotify_client.py`

Responsibility:

* All interaction with the Spotify Web API.
* No project logic, only API calls and mapping to internal models.

Key parts:

* `SpotifyApiError` exception.

* `SpotifyClient` class

  * Initialized with a `SpotifyConfig`.
  * Internal `_get()` that:

    * Builds URL `https://api.spotify.com/v1/...`.
    * Adds authorization headers.
    * Handles errors and returns parsed JSON.
  * `get_current_user_top_tracks(limit, time_range)`:

    * Calls `/me/top/tracks` with params.
    * Parses items into `Track` instances via `_parse_track`.

The rest of the app never calls Spotify directly, only `SpotifyClient`.

---

### 3.4 `language_filter.py`

Responsibility:

* Heuristic language detection for tracks based on text metadata.

Functions:

* `detect_track_language(track: Track) -> str | None`

  * Concatenates track name and artist names.
  * Uses `langdetect.detect`.
  * Returns ISO 639 language code or `None`.

* `filter_tracks_by_language(tracks, target_language)`

  * Filters a sequence of `Track` objects by language code.

Important caveat:

* This is only a prefilter and unreliable for short or ambiguous text.
* Proper language detection must be done on lyrics once you have them.

---

### 3.5 `track_selection.py`

Responsibility:

* Encapsulate the logic for “get candidate tracks in a target language”.

Function:

* `get_candidate_tracks_for_language(client, target_language, limit, time_range)`

  * Calls `SpotifyClient.get_current_user_top_tracks`.
  * Applies `filter_tracks_by_language`.
  * Returns a list of candidate `Track` objects.

This is your current “pool of songs for language X” abstraction.

---

### 3.6 Lyrics provider abstraction

#### `lyrics_provider.py`

Responsibility:

* Common interface for any lyrics provider.

Elements:

* `LyricsProviderError`

  * Base exception for provider related failures.

* `LyricsProvider` abstract base class

  * `name` property

    * Short identifier of the provider, for example `"genius"`.
  * `get_lyrics_for_track(track: Track) -> Optional[str]`

    * Returns full lyrics text or `None`.

Strict rule: every external lyrics service must be wrapped in a class implementing this interface. No raw HTTP in the rest of the code.

---

### 3.7 Genius provider

#### `lyrics_provider_genius.py`

Responsibility:

* Concrete implementation of `LyricsProvider` using Genius API plus HTML scraping.

Workflow inside `GeniusProvider`:

1. Build search query from Spotify track:

   * `"{track.name} {primary_artist.name}"`.

2. Call Genius search API:

   * `GET https://api.genius.com/search?q=<query>`.
   * Authorization header from `GeniusConfig`.
   * Extract `hits` list from JSON.

3. Select the best hit:

   * First try exact match on title and primary artist name (case insensitive).
   * Then fallback to exact title only.
   * Then fallback to first hit.

4. Derive song page URL:

   * Use `result["url"]`, or fallback to `https://genius.com{path}` if only `path` is present.

5. Scrape lyrics from song page:

   * Fetch HTML.
   * Remove `<script>` tags.
   * Extract all `div` elements with `data-lyrics-container="true"` and join their text.
   * If not present, fallback to legacy `div class="lyrics"`.
   * Return combined text or `None`.

Genius API and HTML details are completely isolated in this module.

---

### 3.8 `lyrics_fetcher.py`

Responsibility:

* High level function to “get lyrics for a batch of tracks” using any provider.

Current simple version:

* `fetch_lyrics_for_tracks(provider, tracks)`

  * For each track:

    * Calls `provider.get_lyrics_for_track(track)`.
    * If non empty, adds `(track, lyrics)` to results list.
  * Returns `list[(Track, str)]`.

This function knows nothing about Genius or Spotify specifics.

After we add caching and a database, this module will gain session handling and cache lookups, but structure stays the same.

---

### 3.9 `scripts/fetch_top_tracks.py`

Responsibility:

* Thin CLI layer to exercise the pipeline.

What it does:

1. Parse arguments:

   * `--lang` (required): language code like `ru`, `en`.
   * `--limit`: number of top tracks (default 50).
   * `--time-range`: `short_term`, `medium_term`, `long_term`.
   * `--print-lyrics`: flag to also fetch and print lyrics.

2. Load config and construct clients:

   * `SpotifyConfig` and `SpotifyClient`.
   * For lyrics phase, `GeniusConfig` and `GeniusProvider`.

3. Fetch and display tracks:

   * Calls `get_candidate_tracks_for_language`.
   * Prints count and each track’s `display_name`.

4. Optionally fetch lyrics:

   * Calls `fetch_lyrics_for_tracks(provider, candidates)`.
   * Prints count and for each `(track, lyrics)` a short multi line preview.

The script itself contains no scraping logic, no direct API calls. It just wires modules together.

---

## 4. Current data flow

End to end flow for one run with `--print-lyrics`:

1. `scripts/fetch_top_tracks.py`
   → `get_spotify_config()`
   → `SpotifyClient`
   → `get_candidate_tracks_for_language()`
   → `SpotifyClient.get_current_user_top_tracks()`
   → `language_filter.filter_tracks_by_language()`
   → list of `Track` candidates.

2. If `--print-lyrics` is provided
   → `get_genius_config()`
   → `GeniusProvider`
   → `fetch_lyrics_for_tracks(provider, candidates)`
   → for each track:
   → `GeniusProvider.get_lyrics_for_track(track)`
   → Genius search API
   → Genius page scrape
   → return lyrics string.

3. Script prints debug counts and simple textual representation.

Nothing is persisted yet. Each run hits both Spotify and Genius fresh.

---

## 5. Planned near term additions

This is the next coherent block of work, in order.

### 5.1 Persistence and caching

Goal: avoid re scraping the same track lyrics every time and prepare for real backend use.

Planned pieces:

* `db.py`

  * SQLAlchemy engine creation based on `DatabaseConfig`.
  * `Base` declarative base.
  * `init_db()` to create tables.
  * `get_session()` context manager for transactions.

* `db_models.py`

  * `LyricsCache` ORM model:

    * `id`: primary key.
    * `spotify_track_id`.
    * `provider`.
    * `lyrics_text`.
    * `language` (optional).
    * `created_at`.
    * Unique constraint on `(spotify_track_id, provider)`.

* `lyrics_repository.py`

  * `get_cached_lyrics(session, spotify_track_id, provider) -> Optional[str]`.
  * `store_lyrics(session, spotify_track_id, provider, lyrics_text, language=None)`.

* `lyrics_fetcher.py` will change to:

  * Take a `Session` and `LyricsProvider`.
  * For each track:

    * Check cache.
    * If cached, use it.
    * If not, call provider and then store in cache.

CLI script will call `init_db()` once and use `get_session()` around the `fetch_lyrics_for_tracks` call.

### 5.2 Language detection on lyrics

After cache exists:

* Introduce a module, for example `lyrics_language.py`, to detect language from full lyrics text.
* On first insert into cache, detect and store `language` in `LyricsCache`.
* Introduce a more accurate selection function:

  * Use cached lyrics and their language to find tracks that actually match the user’s target language.
  * Move away from relying solely on track titles.

### 5.3 Word and sentence extraction

Once lyrics are available and language for each is known:

* New module, for example `text_processing.py`:

  * Tokenization and POS tagging (likely via spaCy).
  * Stopword removal.
  * Scoring of candidate words (frequency in song vs base frequency in language).
  * Extraction of example sentences or lines containing the word.

Outputs will be internal models such as `CardCandidate` that later get written to a dedicated table.

### 5.4 Translation layer

Another provider abstraction:

* `translation_provider.py` with `TranslationProvider` interface.
* Implementations using Google Translate API or similar.
* Use this to fill in `word_translation` and `sentence_translation` when generating cards.

### 5.5 Backend API

After data model and processing logic are stable:

* Add a FastAPI application module, for example `api.py`.
* Expose endpoints:

  * `/tracks`
  * `/lyrics`
  * `/cards`
* Reuse the same domain modules and repository layer.

---

## 6. How you should think about it

Mental map of layers:

* Edge layer

  * CLI scripts today.
  * Later HTTP endpoints.

* Application layer (orchestration)

  * `track_selection` for selecting tracks.
  * `lyrics_fetcher` for getting lyrics in bulk.
  * Future card generation services.

* Domain layer (pure logic, no IO)

  * `models`, language detection, text processing, scoring, selection rules.

* Infrastructure layer

  * `spotify_client`, `lyrics_provider_genius`, future translation providers.
  * Database modules: `db`, `db_models`, `lyrics_repository`.
  * Configuration: `config`.

![Diagram](http://www.plantuml.com/plantuml/proxy?cache=no&src=https://raw.githubusercontent.com/filipleple/spotifylingo/refs/heads/master/diagram.puml)
