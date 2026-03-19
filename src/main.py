"""
Command line runner for the Music Recommender Simulation.

Run with:  python -m src.main
"""

try:
    from tabulate import tabulate
    _HAS_TABULATE = True
except ImportError:
    _HAS_TABULATE = False

try:
    from src.recommender import load_songs, recommend_songs, SCORING_MODES
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs, SCORING_MODES


# ── Challenge 4: Visual Table ─────────────────────────────────────────────────

def _truncate(text: str, width: int) -> str:
    """Truncate a string to width, adding '…' if cut."""
    return text if len(text) <= width else text[: width - 1] + "…"


def print_table(label: str, profile_summary: str, results: list) -> None:
    """Print recommendations as a formatted table (tabulate if available, else ASCII)."""
    print(f"\n{'=' * 70}")
    print(f"  PROFILE : {label}")
    print(f"  PREFS   : {profile_summary}")
    print(f"{'=' * 70}")

    rows = []
    for rank, (song, score, explanation) in enumerate(results, start=1):
        rows.append([
            f"#{rank}",
            _truncate(song["title"], 22),
            _truncate(song["artist"], 16),
            song["genre"],
            song["mood"],
            f"{song['energy']:.2f}",
            f"{song.get('popularity', '?')}",
            f"{score:.2f}",
            _truncate(explanation, 48),
        ])

    headers = ["Rank", "Title", "Artist", "Genre", "Mood", "Nrg", "Pop", "Score", "Why"]

    if _HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
        # Fallback: simple padded ASCII table
        col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
        divider = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        def fmt_row(row):
            return "|" + "|".join(f" {str(c).ljust(w)} " for c, w in zip(row, col_widths)) + "|"
        print(divider)
        print(fmt_row(headers))
        print(divider)
        for row in rows:
            print(fmt_row(row))
        print(divider)
    print()


# ── Profiles ──────────────────────────────────────────────────────────────────

PROFILES = {
    "High-Energy Pop": {
        "genre": "pop", "mood": "happy",
        "energy": 0.8, "valence": 0.8, "acousticness": 0.2,
        "popularity": 85, "mood_tags": ["uplifting", "danceable"],
    },
    "Chill Lofi Study": {
        "genre": "lofi", "mood": "chill",
        "energy": 0.4, "valence": 0.6, "acousticness": 0.8,
        "popularity": 70, "mood_tags": ["focused", "calm"],
    },
    "Deep Intense Rock": {
        "genre": "rock", "mood": "intense",
        "energy": 0.92, "valence": 0.4, "acousticness": 0.1,
        "popularity": 65, "mood_tags": ["aggressive", "powerful"],
    },
}


def profile_summary(prefs: dict) -> str:
    return (
        f"genre={prefs['genre']} | mood={prefs['mood']} | "
        f"energy={prefs['energy']} | pop={prefs.get('popularity','?')} | "
        f"tags={prefs.get('mood_tags', [])}"
    )


def main() -> None:
    songs = load_songs("data/songs.csv")

    # ── Challenge 2: Compare scoring modes for High-Energy Pop ────────────────
    print("\n\n### CHALLENGE 2: SCORING MODES — High-Energy Pop ###")
    prefs = PROFILES["High-Energy Pop"]
    for mode in SCORING_MODES:
        results = recommend_songs(prefs, songs, k=5, mode=mode, use_diversity=False)
        print_table(
            label=f"High-Energy Pop  [{mode.upper()} mode]",
            profile_summary=profile_summary(prefs),
            results=results,
        )

    # ── Challenge 3: Diversity penalty ON vs OFF — Chill Lofi ─────────────────
    print("\n\n### CHALLENGE 3: DIVERSITY PENALTY — Chill Lofi Study ###")
    prefs = PROFILES["Chill Lofi Study"]

    results_no_div = recommend_songs(prefs, songs, k=5, mode="default", use_diversity=False)
    print_table(
        label="Chill Lofi Study  [diversity OFF]",
        profile_summary=profile_summary(prefs),
        results=results_no_div,
    )

    results_div = recommend_songs(prefs, songs, k=5, mode="default", use_diversity=True)
    print_table(
        label="Chill Lofi Study  [diversity ON]",
        profile_summary=profile_summary(prefs),
        results=results_div,
    )

    # ── Challenge 1: New features in action — show popularity + mood tags ──────
    print("\n\n### CHALLENGE 1: ADVANCED FEATURES — all profiles, default mode ###")
    for label, prefs in PROFILES.items():
        results = recommend_songs(prefs, songs, k=5, mode="default", use_diversity=True)
        print_table(
            label=label,
            profile_summary=profile_summary(prefs),
            results=results,
        )


if __name__ == "__main__":
    main()
