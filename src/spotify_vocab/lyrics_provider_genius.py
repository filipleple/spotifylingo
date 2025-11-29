from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .config import GeniusConfig
from .lyrics_provider import LyricsProvider, LyricsProviderError
from .models import Track


@dataclass
class GeniusProvider(LyricsProvider):
    """
    Lyrics provider using the Genius API.

    1. Search for the song using track name + primary artist.
    2. Pick the best matching hit.
    3. Fetch the song page HTML and scrape lyrics blocks.
    """

    config: GeniusConfig

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
        }

    def get_lyrics_for_track(self, track: Track) -> Optional[str]:
        query = self._build_search_query(track)
        hits = self._search(query)
        if not hits:
            return None

        best = self._select_best_hit(hits, track)
        if not best:
            return None

        # Genius API song object: we can either use 'url' or 'path'
        song_url = best.get("url")
        if not song_url:
            path = best.get("path")
            if path:
                song_url = f"https://genius.com{path}"
            else:
                return None

        return self._scrape_lyrics_from_page(song_url)

    @staticmethod
    def _build_search_query(track: Track) -> str:
        primary_artist = track.artists[0].name if track.artists else ""
        return f"{track.name} {primary_artist}".strip()

    def _search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.config.base_url}/search"
        params = {"q": query}

        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=5.0)
        except requests.RequestException as exc:
            raise LyricsProviderError(f"Genius search request failed: {exc}") from exc

        if not response.ok:
            raise LyricsProviderError(f"Genius search error {response.status_code}: {response.text}")

        data = response.json()
        hits = data.get("response", {}).get("hits", [])
        results: List[Dict[str, Any]] = []
        for hit in hits:
            result = hit.get("result")
            if isinstance(result, dict):
                results.append(result)
        return results

    @staticmethod
    def _normalize(s: str) -> str:
        return s.strip().lower()

    def _select_best_hit(
        self,
        hits: List[Dict[str, Any]],
        track: Track,
    ) -> Optional[Dict[str, Any]]:
        """
        Basic matching heuristic against the Spotify track metadata.
        """

        track_title = self._normalize(track.name)
        track_artist = self._normalize(track.artists[0].name) if track.artists else ""

        # First pass: exact title + exact primary artist
        for hit in hits:
            title = self._normalize(str(hit.get("title", "")))
            primary_artist = hit.get("primary_artist") or {}
            artist_name = self._normalize(str(primary_artist.get("name", "")))
            if title == track_title and artist_name == track_artist:
                return hit

        # Second pass: exact title only
        for hit in hits:
            title = self._normalize(str(hit.get("title", "")))
            if title == track_title:
                return hit

        # Fallback: first hit
        return hits[0] if hits else None

    def _scrape_lyrics_from_page(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, timeout=5.0)
        except requests.RequestException as exc:
            raise LyricsProviderError(f"Genius page fetch failed for {url}: {exc}") from exc

        if not response.ok:
            raise LyricsProviderError(
                f"Genius page error {response.status_code} for {url}"
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts to reduce noise
        for script in soup("script"):
            script.decompose()

        # Newer Genius layout: multiple <div data-lyrics-container="true">
        containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        if containers:
            parts = [c.get_text(separator="\n", strip=True) for c in containers]
            text = "\n".join(p for p in parts if p)
            return text or None

        # Fallback for older layout: single <div class="lyrics">
        legacy = soup.find("div", class_="lyrics")
        if legacy:
            text = legacy.get_text(separator="\n", strip=True)
            return text or None

        # If both fail, no lyrics found
        return None
