from typing import Iterable, List

from langdetect import detect, LangDetectException

from .models import Track


def detect_track_language(track: Track) -> str | None:
    """
    Heuristic, uses track and artist names.
    This is not reliable for short or non textual names.
    """
    text_parts = [track.name] + [artist.name for artist in track.artists]
    text = " ".join(part for part in text_parts if part)
    if not text.strip():
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None


def filter_tracks_by_language(
    tracks: Iterable[Track],
    target_language: str,
) -> List[Track]:
    """
    Return tracks whose detected language matches the target.
    For example target_language="en" or "es".
    """
    result: List[Track] = []
    for track in tracks:
        lang = detect_track_language(track)
        if lang == target_language:
            result.append(track)
    return result
