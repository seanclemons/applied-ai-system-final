import csv
import json
import os
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SONGS_CSV = os.path.join(DATA_DIR, "songs.csv")
GENRE_DOCS = os.path.join(DATA_DIR, "genre_docs.json")


def _load_songs() -> list[dict]:
    songs = []
    with open(SONGS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["energy"] = float(row["energy"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            row["popularity"] = int(row["popularity"])
            row["tempo_bpm"] = int(row["tempo_bpm"])
            # Keep mood_tags as pipe-separated string; recommender.py handles the split
            songs.append(row)
    return songs


def _load_genre_docs() -> dict:
    with open(GENRE_DOCS, encoding="utf-8") as f:
        return json.load(f)


def retrieve_songs_by_genre(genre: str, songs: list[dict]) -> list[dict]:
    """Return songs whose genre matches or is related to the requested genre."""
    exact = [s for s in songs if s["genre"].lower() == genre.lower()]
    if exact:
        return exact
    # Soft match: genre name contains query or vice versa
    soft = [s for s in songs if genre.lower() in s["genre"].lower()
            or s["genre"].lower() in genre.lower()]
    return soft


def retrieve_genre_context(genre: str, genre_docs: dict) -> dict[str, Any]:
    """Return genre knowledge doc for the requested genre, or closest match."""
    genres = genre_docs.get("genres", {})
    if genre in genres:
        return genres[genre]
    # Soft match
    for key in genres:
        if genre in key or key in genre:
            return genres[key]
    return {}


def retrieve_mood_context(mood: str, genre_docs: dict) -> str:
    """Return mood description from genre docs."""
    return genre_docs.get("mood_context", {}).get(mood, "")


def retrieve_candidates(
    user_prefs: dict,
    songs: list[dict] | None = None,
    genre_docs: dict | None = None,
    top_n: int = 12,
) -> dict[str, Any]:
    """
    Multi-source retrieval step.
    Returns candidate songs plus enriched context from genre knowledge base.
    """
    if songs is None:
        songs = _load_songs()
    if genre_docs is None:
        genre_docs = _load_genre_docs()

    genre = user_prefs.get("genre", "").lower()
    mood = user_prefs.get("mood", "").lower()

    # Source 1: genre-matched songs
    genre_matches = retrieve_songs_by_genre(genre, songs)

    # Source 2: mood-matched songs not already in genre matches
    genre_match_ids = {s["id"] for s in genre_matches}
    mood_matches = [
        s for s in songs
        if s["mood"].lower() == mood and s["id"] not in genre_match_ids
    ]

    # Source 3: remaining songs sorted by energy proximity
    target_energy = float(user_prefs.get("energy", 0.5))
    covered_ids = genre_match_ids | {s["id"] for s in mood_matches}
    remaining = sorted(
        [s for s in songs if s["id"] not in covered_ids],
        key=lambda s: abs(s["energy"] - target_energy),
    )

    # Merge sources, genre first, then mood, then energy-proximity
    candidates = (genre_matches + mood_matches + remaining)[:top_n]

    # Enrich with genre knowledge
    genre_context = retrieve_genre_context(genre, genre_docs)
    mood_context = retrieve_mood_context(mood, genre_docs)

    related_genres = genre_context.get("related_genres", [])
    typical_energy = genre_context.get("typical_energy_range", [0.0, 1.0])

    return {
        "candidates": candidates,
        "genre_context": genre_context,
        "mood_context": mood_context,
        "related_genres": related_genres,
        "typical_energy_range": typical_energy,
        "sources_used": ["songs_csv", "genre_docs_json"],
        "source_counts": {
            "genre_matches": len(genre_matches),
            "mood_matches": len(mood_matches),
            "energy_proximity": len(remaining[:top_n]),
        },
    }
