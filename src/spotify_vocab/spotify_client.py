from typing import List, Literal, Dict, Any

import requests

from .config import SpotifyConfig, TimeRange
from .models import Track, Artist


class SpotifyApiError(Exception):
    pass


class SpotifyClient:
    def __init__(self, config: SpotifyConfig) -> None:
        self._config = config
        self._base_url = "https://api.spotify.com/v1"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._config.access_token}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        response = requests.get(url, headers=self._headers(), params=params)
        if response.status_code == 401:
            raise SpotifyApiError("Unauthorized. Your access token is invalid or expired.")
        if not response.ok:
            raise SpotifyApiError(
                f"Spotify API error {response.status_code}: {response.text}"
            )
        return response.json()

    def get_current_user_top_tracks(
        self,
        limit: int | None = None,
        time_range: TimeRange | None = None,
    ) -> List[Track]:
        if limit is None:
            limit = self._config.default_limit
        if time_range is None:
            time_range = self._config.default_time_range

        params = {
            "limit": limit,
            "time_range": time_range,
        }

        data = self._get("/me/top/tracks", params=params)
        items = data.get("items", [])
        return [self._parse_track(item) for item in items]

    @staticmethod
    def _parse_track(item: Dict[str, Any]) -> Track:
        artists = [
            Artist(id=a["id"], name=a["name"])
            for a in item.get("artists", [])
        ]
        return Track(
            id=item["id"],
            name=item["name"],
            artists=artists,
            uri=item["uri"],
            href=item["href"],
            preview_url=item.get("preview_url"),
        )
