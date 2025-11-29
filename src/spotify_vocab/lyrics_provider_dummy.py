from typing import Optional

from .lyrics_provider import LyricsProvider
from .models import Track


class DummyLyricsProvider(LyricsProvider):
    """
    Placeholder provider so we can develop the pipeline.
    Replace this with a real provider implementation later.
    """

    def get_lyrics_for_track(self, track: Track) -> Optional[str]:
        # In tests and initial wiring you can return a static string
        # or None to simulate missing lyrics.
        return None
