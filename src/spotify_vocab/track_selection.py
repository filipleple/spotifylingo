from typing import List

from .spotify_client import SpotifyClient
from .language_filter import filter_tracks_by_language
from .models import Track
from .config import TimeRange


def get_candidate_tracks_for_language(
    client: SpotifyClient,
    target_language: str,
    limit: int = 50,
    time_range: TimeRange = "long_term",
) -> List[Track]:
    """
    Fetch top tracks and return those whose detected language matches target_language.
    This is only a prefilter. Real filtering will use lyrics later.
    """
    tracks = client.get_current_user_top_tracks(limit=limit, time_range=time_range)
    return filter_tracks_by_language(tracks, target_language)
