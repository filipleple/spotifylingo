from abc import ABC, abstractmethod
from typing import Optional

from .models import Track


class LyricsProviderError(Exception):
    pass


class LyricsProvider(ABC):
    @abstractmethod
    def get_lyrics_for_track(self, track: Track) -> Optional[str]:
        """
        Return full lyrics as a single string for the given track.
        Return None if lyrics are not found.
        Raise LyricsProviderError for network or API related problems.
        """
        raise NotImplementedError
