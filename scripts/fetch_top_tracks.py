#!/usr/bin/env python

import argparse

from spotify_vocab.config import get_spotify_config
from spotify_vocab.spotify_client import SpotifyClient
from spotify_vocab.track_selection import get_candidate_tracks_for_language
from spotify_vocab.lyrics_fetcher import fetch_lyrics_for_tracks
from spotify_vocab.lyrics_provider_dummy import DummyLyricsProvider


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch top tracks and filter by language"
    )
    parser.add_argument(
        "--lang",
        required=True,
        help="Target language code for filtering tracks, for example en, es, ru",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of top tracks to fetch from Spotify",
    )
    parser.add_argument(
        "--time-range",
        choices=["short_term", "medium_term", "long_term"],
        default="long_term",
        help="Spotify time range for top tracks",
    )
    parser.add_argument(
        "--print-lyrics",
        action="store_true",
        help="Fetch and print the lyrics?",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = get_spotify_config()
    client = SpotifyClient(config)

    print(f"Fetching top tracks, limit={args.limit}, time_range={args.time_range}")
    candidates = get_candidate_tracks_for_language(
        client=client,
        target_language=args.lang,
        limit=args.limit,
        time_range=args.time_range,
    )

    print(f"Tracks matching {args.lang}: {len(candidates)}")
    print()
    for track in candidates:
        print(track.display_name)

    provider = DummyLyricsProvider()

    if (args.print_lyrics):
        print(fetch_lyrics_for_tracks(provider, candidates))


if __name__ == "__main__":
    main()
