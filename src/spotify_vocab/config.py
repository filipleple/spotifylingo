from dataclasses import dataclass
import os
from typing import Literal, Optional

from dotenv import load_dotenv

# Load .env in development. In production, you configure real environment variables.
load_dotenv()


TimeRange = Literal["short_term", "medium_term", "long_term"]


@dataclass
class SpotifyConfig:
    access_token: str
    default_time_range: TimeRange = "long_term"
    default_limit: int = 50


def get_spotify_config() -> SpotifyConfig:
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("SPOTIFY_ACCESS_TOKEN is not set. Check your .env or environment.")
    return SpotifyConfig(access_token=token)


@dataclass
class GeniusConfig:
    access_token: str
    base_url: str = "https://api.genius.com"


def get_genius_config() -> GeniusConfig:
    token = os.getenv("GENIUS_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("GENIUS_ACCESS_TOKEN is not set. Check your .env or environment.")
    return GeniusConfig(access_token=token)
