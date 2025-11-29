from typing import Iterable, List, Tuple

from .models import Track
from .lyrics_provider import LyricsProvider


def fetch_lyrics_for_tracks(
    provider: LyricsProvider,
    tracks: Iterable[Track],
) -> List[Tuple[Track, str]]:
    """
    For each track try to fetch lyrics and collect successes.
    """
    result: List[Tuple[Track, str]] = []
    for track in tracks:
        lyrics = provider.get_lyrics_for_track(track)
        if lyrics:
            result.append((track, lyrics))
    return result
