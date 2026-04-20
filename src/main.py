"""
SoundMatch — Applied AI Music Recommendation System
Extended from the Module 3 Music Recommender Simulation.

Run with:  python -m src.main
"""

import sys
import io

# Ensure Unicode output works on Windows terminals
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    from tabulate import tabulate
    _HAS_TABULATE = True
except ImportError:
    _HAS_TABULATE = False

from src.agent import run_agent


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def print_agent_results(profile_name: str, result: dict) -> None:
    recs = result.get("recommendations", [])
    if not recs:
        print(f"\n  No recommendations produced for '{profile_name}'.")
        return

    print(f"\n{'=' * 72}")
    print(f"  PROFILE : {profile_name}")
    print(f"  PERSONA : {result.get('persona', 'default')}  |  "
          f"overall confidence: {result.get('overall_confidence', 0.0):.2f}  |  "
          f"steps: {len(result.get('steps_taken', []))}/5")
    print(f"  {result.get('persona_intro', '')}")
    print(f"{'=' * 72}")

    rows = []
    for i, r in enumerate(recs, 1):
        reason_str = _truncate(" | ".join(r.get("reasons", [])[:2]), 40)
        rows.append([
            f"#{i}",
            _truncate(r["title"], 20),
            _truncate(r["artist"], 16),
            r["genre"],
            r["mood"],
            f"{r['energy']:.2f}",
            f"{r['popularity']}",
            f"{r['score']:.2f}",
            f"{r['confidence']:.2f} [{r['confidence_label']}]",
            reason_str,
        ])

    headers = ["Rank", "Title", "Artist", "Genre", "Mood", "Nrg", "Pop", "Score", "Conf", "Why"]

    if _HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="simple"))
    else:
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

    critique = result.get("critique_notes", [])
    if critique:
        print()
        for note in critique:
            print(f"  ⚠ {note}")

    print()


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

PROFILES = {
    "High-Energy Pop": {
        "genre": "pop", "mood": "happy",
        "energy": 0.8, "popularity": 85,
        "tags": ["uplifting", "danceable"],
        "valence": 0.8, "acousticness": 0.2,
        "mood_tags": ["uplifting", "danceable"],
    },
    "Chill Lofi Study": {
        "genre": "lofi", "mood": "chill",
        "energy": 0.4, "popularity": 70,
        "tags": ["focused", "calm"],
        "valence": 0.6, "acousticness": 0.8,
        "mood_tags": ["focused", "calm"],
    },
    "Deep Intense Rock": {
        "genre": "rock", "mood": "intense",
        "energy": 0.92, "popularity": 65,
        "tags": ["aggressive", "powerful"],
        "valence": 0.4, "acousticness": 0.1,
        "mood_tags": ["aggressive", "powerful"],
    },
}


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def main() -> None:
    sep = "\n" + "#" * 72

    print(sep)
    print("  SOUNDMATCH — AGENTIC MUSIC RECOMMENDATION SYSTEM")
    print("  Each run executes 5 observable agent steps:")
    print("  1. Profile Analysis  2. RAG Retrieval  3. Scoring")
    print("  4. Self-Critique     5. Final Response")
    print("#" * 72)

    # ------------------------------------------------------------------
    # Demo 1: All three profiles — full agent, verbose step output
    # ------------------------------------------------------------------
    print(sep)
    print("  DEMO 1 — Three User Profiles (Full Agent, Verbose Steps)")
    print("#" * 72)

    for name, prefs in PROFILES.items():
        print(f"\n{'─'*72}")
        print(f"  Running agent for profile: {name}")
        result = run_agent(prefs, k=5, mode="default", use_diversity=True, verbose=True)
        print_agent_results(name, result)

    # ------------------------------------------------------------------
    # Demo 2: Scoring mode comparison (non-verbose, table output only)
    # ------------------------------------------------------------------
    print(sep)
    print("  DEMO 2 — Scoring Mode Comparison  [High-Energy Pop, verbose OFF]")
    print("#" * 72)

    for mode in ("default", "genre_first", "mood_first", "energy_focused"):
        result = run_agent(
            PROFILES["High-Energy Pop"],
            k=5, mode=mode, use_diversity=False, verbose=False,
        )
        print_agent_results(f"High-Energy Pop [{mode.upper()}]", result)

    # ------------------------------------------------------------------
    # Demo 3: Guardrail demo — invalid inputs
    # ------------------------------------------------------------------
    print(sep)
    print("  DEMO 3 — Guardrail Behavior  [Invalid Inputs]")
    print("#" * 72)

    bad_profiles = [
        ("Invalid mood 'hyped'", {"genre": "pop", "mood": "hyped", "energy": 0.8, "popularity": 80}),
        ("Energy out of range 1.5", {"genre": "jazz", "mood": "relaxed", "energy": 1.5, "popularity": 60}),
        ("Missing genre", {"mood": "chill", "energy": 0.4, "popularity": 70}),
    ]

    for label, prefs in bad_profiles:
        print(f"\n  Input: {label}")
        result = run_agent(prefs, verbose=True)
        if result.get("error"):
            print(f"  ✓ Guardrail activated — system safely blocked invalid request.")
            for note in result.get("critique_notes", []):
                print(f"    → {note}")
        print()


if __name__ == "__main__":
    main()
