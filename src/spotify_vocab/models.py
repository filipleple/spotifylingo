from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Artist:
    id: str
    name: str


@dataclass
class Track:
    id: str
    name: str
    artists: List[Artist]
    uri: str
    href: str
    preview_url: Optional[str] = None

    @property
    def display_name(self) -> str:
        artist_names = ", ".join(artist.name for artist in self.artists)
        return f"{self.name} by {artist_names}"
