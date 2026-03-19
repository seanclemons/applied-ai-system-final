import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


# ── Challenge 2: Scoring Modes (Strategy Pattern) ─────────────────────────────
# Each mode is a plain dict of feature weights. Swap modes to change behavior
# without touching scoring logic. Max score per mode varies; see each docstring.

SCORING_MODES: Dict[str, Dict[str, float]] = {
    # Default: balanced — genre is the strongest single signal
    "default": {
        "genre": 2.0, "mood": 1.0, "energy": 1.5,
        "valence": 1.0, "acousticness": 0.5,
        "popularity": 0.5, "decade": 0.5, "mood_tags": 1.0,
    },
    # Genre-First: doubles down on style boundary, useful for strict genre fans
    "genre_first": {
        "genre": 4.0, "mood": 1.0, "energy": 1.0,
        "valence": 0.5, "acousticness": 0.25,
        "popularity": 0.5, "decade": 0.25, "mood_tags": 0.5,
    },
    # Mood-First: context (what you're doing) matters more than style
    "mood_first": {
        "genre": 1.0, "mood": 3.0, "energy": 1.5,
        "valence": 1.0, "acousticness": 0.5,
        "popularity": 0.5, "decade": 0.5, "mood_tags": 2.0,
    },
    # Energy-Focused: intensity match above all else; great for workouts/focus
    "energy_focused": {
        "genre": 0.5, "mood": 0.5, "energy": 4.0,
        "valence": 0.5, "acousticness": 0.5,
        "popularity": 0.25, "decade": 0.25, "mood_tags": 0.5,
    },
}


@dataclass
class Song:
    """Represents a song and its audio attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # Challenge 1: advanced features (default values keep existing tests working)
    popularity: int = 50
    release_decade: str = "2020s"
    mood_tags: str = ""


@dataclass
class UserProfile:
    """Represents a user's taste preferences for content-based filtering."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return a list of dicts with typed numeric fields."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":             int(row["id"]),
                "title":          row["title"],
                "artist":         row["artist"],
                "genre":          row["genre"],
                "mood":           row["mood"],
                "energy":         float(row["energy"]),
                "tempo_bpm":      int(row["tempo_bpm"]),
                "valence":        float(row["valence"]),
                "danceability":   float(row["danceability"]),
                "acousticness":   float(row["acousticness"]),
                # Challenge 1: new fields
                "popularity":     int(row.get("popularity", 50)),
                "release_decade": row.get("release_decade", "2020s"),
                "mood_tags":      row.get("mood_tags", ""),
            })
    print(f"Loaded songs: {len(songs)}")
    return songs


def score_song(
    user_prefs: Dict,
    song: Dict,
    weights: Dict[str, float] = None,
) -> Tuple[float, List[str]]:
    """Score one song against user preferences using the given weight config.

    Returns (total_score, list_of_reason_strings).
    If weights is None, the 'default' SCORING_MODES config is used.
    """
    w = weights if weights is not None else SCORING_MODES["default"]
    score = 0.0
    reasons = []

    # ── Categorical features (binary: full weight or zero) ────────────────────
    if song["genre"] == user_prefs.get("genre", ""):
        pts = w.get("genre", 0)
        score += pts
        reasons.append(f"genre match (+{pts:.1f})")

    if song["mood"] == user_prefs.get("mood", ""):
        pts = w.get("mood", 0)
        score += pts
        reasons.append(f"mood match (+{pts:.1f})")

    # Release decade match
    if "decade" in user_prefs and song["release_decade"] == user_prefs["decade"]:
        pts = w.get("decade", 0)
        score += pts
        reasons.append(f"decade match {song['release_decade']} (+{pts:.1f})")

    # ── Numeric proximity features (1 - |diff|, then scaled by weight) ────────
    if "energy" in user_prefs:
        pts = (1 - abs(song["energy"] - user_prefs["energy"])) * w.get("energy", 0)
        score += pts
        reasons.append(f"energy proximity (+{pts:.2f})")

    if "valence" in user_prefs:
        pts = (1 - abs(song["valence"] - user_prefs["valence"])) * w.get("valence", 0)
        score += pts
        reasons.append(f"valence proximity (+{pts:.2f})")

    if "acousticness" in user_prefs:
        pts = (1 - abs(song["acousticness"] - user_prefs["acousticness"])) * w.get("acousticness", 0)
        score += pts
        reasons.append(f"acousticness proximity (+{pts:.2f})")

    # Challenge 1: Popularity proximity — rewards songs near the user's target
    # popularity (0-100 → normalize to 0-1 for the math, then scale by weight)
    if "popularity" in user_prefs:
        song_pop_norm = song["popularity"] / 100.0
        user_pop_norm = user_prefs["popularity"] / 100.0
        pts = (1 - abs(song_pop_norm - user_pop_norm)) * w.get("popularity", 0)
        score += pts
        reasons.append(f"popularity proximity (+{pts:.2f})")

    # Challenge 1: Mood tags — partial credit for each matching tag
    if "mood_tags" in user_prefs and song.get("mood_tags"):
        song_tags = set(song["mood_tags"].split("|"))
        user_tags = set(user_prefs["mood_tags"])
        matched = song_tags & user_tags
        if matched:
            # Award proportional to fraction of user's desired tags that matched
            tag_ratio = len(matched) / max(len(user_tags), 1)
            pts = tag_ratio * w.get("mood_tags", 0)
            score += pts
            reasons.append(f"mood tags {matched} (+{pts:.2f})")

    return score, reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "default",
    use_diversity: bool = True,
    artist_penalty: float = 0.7,
    max_per_genre: int = 2,
) -> List[Tuple[Dict, float, str]]:
    """Score every song, apply optional diversity penalties, and return the top k.

    Challenge 2: pass mode='genre_first'|'mood_first'|'energy_focused' to switch strategy.
    Challenge 3: use_diversity=True applies greedy diversity penalties so no artist
    appears twice and no genre fills more than max_per_genre slots.

    Uses sorted() (returns a new list) so the original songs list is never modified.
    Diversity selection is greedy: scores are re-evaluated at each step so a penalized
    song is always compared fairly against other remaining candidates.
    """
    weights = SCORING_MODES.get(mode, SCORING_MODES["default"])

    # Score every song
    scored: List[Tuple[Dict, float, List[str]]] = [
        (song, *score_song(user_prefs, song, weights))
        for song in songs
    ]

    if not use_diversity:
        ranked = sorted(scored, key=lambda e: e[1], reverse=True)
        return [
            (s, sc, " | ".join(r) if r else "No matching features")
            for s, sc, r in ranked[:k]
        ]

    # ── Challenge 3: Greedy diversity selection ────────────────────────────────
    # At each step, re-apply penalties to all remaining candidates, pick the best,
    # then update the seen-artist and seen-genre counts for the next step.
    remaining = [(s, sc, r) for s, sc, r in scored]
    seen_artists: Dict[str, int] = {}
    seen_genres: Dict[str, int] = {}
    results: List[Tuple[Dict, float, str]] = []

    while remaining and len(results) < k:
        # Apply current diversity penalties to all remaining candidates
        adjusted = []
        for song, base_score, reasons in remaining:
            eff = base_score
            notes = list(reasons)
            if seen_artists.get(song["artist"], 0) >= 1:
                eff *= artist_penalty
                notes.append(f"artist repeat penalty (x{artist_penalty})")
            if seen_genres.get(song["genre"], 0) >= max_per_genre:
                eff *= artist_penalty
                notes.append(f"genre saturated penalty (x{artist_penalty})")
            adjusted.append((song, eff, notes, base_score))

        # Pick the best after adjustments
        adjusted.sort(key=lambda e: e[1], reverse=True)
        best_song, best_eff, best_notes, _ = adjusted[0]

        seen_artists[best_song["artist"]] = seen_artists.get(best_song["artist"], 0) + 1
        seen_genres[best_song["genre"]] = seen_genres.get(best_song["genre"], 0) + 1
        results.append((best_song, best_eff, " | ".join(best_notes) if best_notes else "No matching features"))

        # Remove selected song from candidates
        remaining = [(s, sc, r) for s, sc, r in remaining if s["id"] != best_song["id"]]

    return results


class Recommender:
    """OOP wrapper around the scoring logic; operates on Song dataclass instances."""

    def __init__(self, songs: List[Song]):
        """Store the song catalog."""
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Compute a compatibility score between a UserProfile and a Song."""
        score = 0.0
        reasons = []

        if song.genre == user.favorite_genre:
            score += 2.0
            reasons.append("genre match (+2.0)")

        if song.mood == user.favorite_mood:
            score += 1.0
            reasons.append("mood match (+1.0)")

        energy_pts = (1 - abs(song.energy - user.target_energy)) * 1.5
        score += energy_pts
        reasons.append(f"energy proximity (+{energy_pts:.2f})")

        acousticness_target = 0.8 if user.likes_acoustic else 0.2
        acousticness_pts = (1 - abs(song.acousticness - acousticness_target)) * 0.5
        score += acousticness_pts
        reasons.append(f"acousticness proximity (+{acousticness_pts:.2f})")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top k Song objects ranked by compatibility with the user profile."""
        return sorted(self.songs, key=lambda s: self._score(user, s)[0], reverse=True)[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language explanation of why this song was recommended."""
        _, reasons = self._score(user, song)
        return " | ".join(reasons) if reasons else "No matching features"
