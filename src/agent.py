"""
VibeFinder Agent — multi-step agentic orchestrator.

Steps (each printed and logged so intermediate work is observable):
  1. Profile Analysis   — parse and validate user preferences
  2. RAG Retrieval      — multi-source candidate + context fetch
  3. Scoring            — rank candidates using existing recommender logic
  4. Self-Critique      — inspect results for quality issues
  5. Final Response     — attach confidence scores and format output
"""

from __future__ import annotations

import time
from typing import Any

from src.evaluator import (
    compute_overall_confidence,
    critique_recommendations,
    score_recommendations,
    validate_profile,
)
from src.logger import log_agent_step, log_error, log_retrieval
from src.recommender import recommend_songs
from src.retriever import _load_genre_docs, _load_songs, retrieve_candidates

# ---------------------------------------------------------------------------
# Few-shot persona templates (specialization / fine-tuning proxy)
# ---------------------------------------------------------------------------
PERSONAS = {
    "default": {
        "intro": "Here are your top picks based on your preferences:",
        "high_conf": "Strong match",
        "med_conf": "Good match",
        "low_conf": "Partial match",
    },
    "workout_coach": {
        "intro": "Let's get those gains! Your high-energy playlist:",
        "high_conf": "Perfect for your workout",
        "med_conf": "Solid choice for training",
        "low_conf": "May work as a warmup",
    },
    "music_critic": {
        "intro": "A curated selection reflecting your sonic preferences:",
        "high_conf": "Exceptionally aligned",
        "med_conf": "Notable alignment",
        "low_conf": "Marginal resonance",
    },
    "study_buddy": {
        "intro": "Here's your focus playlist to help you stay in the zone:",
        "high_conf": "Ideal for deep focus",
        "med_conf": "Good background track",
        "low_conf": "May cause mild distraction",
    },
}


def _pick_persona(user_prefs: dict) -> str:
    """Choose a persona based on mood and energy cues."""
    mood = user_prefs.get("mood", "").lower()
    energy = float(user_prefs.get("energy", 0.5))
    if mood in ("intense", "energetic", "angry") and energy >= 0.75:
        return "workout_coach"
    if mood in ("chill", "focused", "peaceful") and energy <= 0.5:
        return "study_buddy"
    return "default"


def _print_step(step_num: int, title: str, detail: str = ""):
    line = f"\n  {'─'*60}"
    print(line)
    print(f"  [AGENT STEP {step_num}] {title}")
    if detail:
        print(f"  {detail}")
    print(f"  {'─'*60}")


def _print_substep(label: str, value: str):
    print(f"    • {label}: {value}")


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def run_agent(
    user_prefs: dict,
    k: int = 5,
    mode: str = "default",
    use_diversity: bool = True,
    verbose: bool = True,
    songs: list[dict] | None = None,
    genre_docs: dict | None = None,
) -> dict[str, Any]:
    """
    Run the full 5-step agentic workflow.

    Parameters
    ----------
    user_prefs : dict with keys genre, mood, energy, popularity, tags (optional)
    k          : number of recommendations to return
    mode       : scoring mode ('default', 'genre_first', 'mood_first', 'energy_focused')
    use_diversity : apply artist/genre diversity penalty
    verbose    : print observable step output to stdout
    songs      : override song catalog (used in tests)
    genre_docs : override genre knowledge base (used in tests)

    Returns
    -------
    dict with keys: recommendations, critique_notes, overall_confidence,
                    persona, retrieval_info, steps_taken, elapsed_seconds
    """
    start = time.time()
    steps_taken = []

    # ------------------------------------------------------------------
    # STEP 1 — Profile Analysis
    # ------------------------------------------------------------------
    if verbose:
        _print_step(1, "Profile Analysis", "Validating user preferences and enriching context.")

    log_agent_step(1, "Profile Analysis")
    # Normalize tags → mood_tags so the scorer picks them up
    if "tags" in user_prefs and "mood_tags" not in user_prefs:
        user_prefs = {**user_prefs, "mood_tags": user_prefs["tags"]}
    is_valid, issues = validate_profile(user_prefs)

    if verbose:
        _print_substep("genre", user_prefs.get("genre", "—"))
        _print_substep("mood", user_prefs.get("mood", "—"))
        _print_substep("energy", user_prefs.get("energy", "—"))
        _print_substep("popularity", user_prefs.get("popularity", "—"))
        if issues:
            for issue in issues:
                print(f"    ⚠ GUARDRAIL: {issue}")
        else:
            print("    ✓ Profile validated — no issues found.")

    steps_taken.append("profile_analysis")

    if not is_valid:
        return {
            "recommendations": [],
            "critique_notes": [f"Validation failed: {'; '.join(issues)}"],
            "overall_confidence": 0.0,
            "persona": "default",
            "retrieval_info": {},
            "steps_taken": steps_taken,
            "elapsed_seconds": round(time.time() - start, 3),
            "error": "invalid_profile",
        }

    # ------------------------------------------------------------------
    # STEP 2 — RAG Retrieval
    # ------------------------------------------------------------------
    if verbose:
        _print_step(2, "RAG Retrieval", "Fetching candidates from songs catalog + genre knowledge base.")

    log_agent_step(2, "RAG Retrieval")

    try:
        retrieval = retrieve_candidates(
            user_prefs,
            songs=songs,
            genre_docs=genre_docs,
        )
    except Exception as exc:
        log_error("RAG Retrieval", exc)
        retrieval = {
            "candidates": songs or _load_songs(),
            "genre_context": {},
            "mood_context": "",
            "related_genres": [],
            "typical_energy_range": [0.0, 1.0],
            "sources_used": ["songs_csv"],
            "source_counts": {},
        }

    candidates = retrieval["candidates"]
    genre_context = retrieval["genre_context"]

    log_retrieval(
        user_prefs.get("genre", ""),
        len(candidates),
        retrieval["sources_used"],
    )

    if verbose:
        sc = retrieval["source_counts"]
        _print_substep("sources", ", ".join(retrieval["sources_used"]))
        _print_substep("genre matches", str(sc.get("genre_matches", "?")))
        _print_substep("mood matches", str(sc.get("mood_matches", "?")))
        _print_substep("total candidates", str(len(candidates)))
        if retrieval["mood_context"]:
            print(f"    ℹ Mood context: {retrieval['mood_context'][:80]}...")
        if genre_context.get("use_cases"):
            print(f"    ℹ Typical use cases: {', '.join(genre_context['use_cases'])}")

    steps_taken.append("rag_retrieval")

    # ------------------------------------------------------------------
    # STEP 3 — Scoring
    # ------------------------------------------------------------------
    if verbose:
        _print_step(3, "Scoring", f"Ranking candidates using mode='{mode}', diversity={use_diversity}.")

    log_agent_step(3, "Scoring", f"mode={mode} diversity={use_diversity} k={k}")

    raw_recs = recommend_songs(
        user_prefs,
        candidates,
        k=k,
        mode=mode,
        use_diversity=use_diversity,
    )

    if verbose:
        for i, (song, score, reasons) in enumerate(raw_recs, 1):
            reason_preview = reasons[:60] if isinstance(reasons, str) else " | ".join(reasons[:2])
            print(f"    #{i} {song['title']} by {song['artist']} — score {score:.2f} ({reason_preview})")

    steps_taken.append("scoring")

    # ------------------------------------------------------------------
    # STEP 4 — Self-Critique
    # ------------------------------------------------------------------
    if verbose:
        _print_step(4, "Self-Critique", "Checking results for quality, diversity, and energy fit.")

    log_agent_step(4, "Self-Critique")

    recs_for_critique = [
        {"title": s["title"], "artist": s["artist"], "genre": s["genre"], "score": sc}
        for s, sc, _ in raw_recs
    ]
    critique_notes = critique_recommendations(recs_for_critique, user_prefs, genre_context)

    if verbose:
        if critique_notes:
            for note in critique_notes:
                print(f"    ⚠ {note}")
        else:
            print("    ✓ No quality issues detected.")

    steps_taken.append("self_critique")

    # ------------------------------------------------------------------
    # STEP 5 — Final Response
    # ------------------------------------------------------------------
    if verbose:
        _print_step(5, "Final Response", "Attaching confidence scores and selecting persona.")

    log_agent_step(5, "Final Response")

    persona_key = _pick_persona(user_prefs)
    persona = PERSONAS[persona_key]

    final_recs = []
    _conf_key = {"HIGH": "high_conf", "MEDIUM": "med_conf", "LOW": "low_conf"}

    for song, raw_score, reasons in raw_recs:
        from src.evaluator import compute_confidence, confidence_label
        conf = compute_confidence(raw_score)
        lbl = confidence_label(conf)
        reasons_list = reasons.split(" | ") if isinstance(reasons, str) else reasons
        final_recs.append({
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "energy": song["energy"],
            "popularity": song["popularity"],
            "score": round(raw_score, 3),
            "confidence": conf,
            "confidence_label": lbl,
            "persona_label": persona[_conf_key[lbl]],
            "reasons": reasons_list,
        })

    overall_conf = compute_overall_confidence(final_recs)
    elapsed = round(time.time() - start, 3)

    if verbose:
        _print_substep("persona", persona_key)
        _print_substep("overall confidence", f"{overall_conf:.2f}")
        _print_substep("elapsed", f"{elapsed}s")
        print()

    steps_taken.append("final_response")

    return {
        "recommendations": final_recs,
        "critique_notes": critique_notes,
        "overall_confidence": overall_conf,
        "persona": persona_key,
        "persona_intro": persona["intro"],
        "retrieval_info": retrieval,
        "steps_taken": steps_taken,
        "elapsed_seconds": elapsed,
    }
