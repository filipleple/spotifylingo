#!/usr/bin/env python

from spotify_vocab.config import get_spotify_config
from spotify_vocab.spotify_client import SpotifyClient
from spotify_vocab.language_filter import filter_tracks_by_language


def main() -> None:
    config = get_spotify_config()
    client = SpotifyClient(config)

    print("Fetching top tracks")
    tracks = client.get_current_user_top_tracks(limit=50, time_range="long_term")

    # Change this to the language you are learning, for example "es" for Spanish.
    target_language = "es"

    print(f"Filtering tracks for language {target_language}")
    filtered = filter_tracks_by_language(tracks, target_language)

    print(f"Total tracks fetched: {len(tracks)}")
    print(f"Tracks matching {target_language}: {len(filtered)}")
    print()
    for track in filtered:
        print(track.display_name)


if __name__ == "__main__":
    main()
