from typing import Any
from src.logger import log_guardrail, log_confidence, log_critique

VALID_MOODS = {
    "happy", "chill", "intense", "relaxed", "moody",
    "focused", "nostalgic", "romantic", "peaceful", "energetic", "angry",
}

VALID_GENRES = {
    "pop", "lofi", "rock", "jazz", "ambient", "metal", "edm",
    "synthwave", "indie pop", "classical", "hip-hop", "r&b",
    "country", "funk", "folk",
}

MAX_RAW_SCORE = 6.0


# ---------------------------------------------------------------------------
# Input guardrails
# ---------------------------------------------------------------------------

def validate_profile(user_prefs: dict) -> tuple[bool, list[str]]:
    """
    Validate user profile fields. Returns (is_valid, list_of_issues).
    Logs each issue via the guardrail logger.
    """
    issues = []

    genre = user_prefs.get("genre", "").lower().strip()
    mood = user_prefs.get("mood", "").lower().strip()
    energy = user_prefs.get("energy")
    popularity = user_prefs.get("popularity")

    if not genre:
        issues.append("genre is missing")
        log_guardrail("genre", "missing value")
    elif genre not in VALID_GENRES:
        issues.append(f"genre '{genre}' is not recognized (known: {sorted(VALID_GENRES)})")
        log_guardrail("genre", f"unrecognized value '{genre}'")

    if not mood:
        issues.append("mood is missing")
        log_guardrail("mood", "missing value")
    elif mood not in VALID_MOODS:
        issues.append(f"mood '{mood}' is not recognized (known: {sorted(VALID_MOODS)})")
        log_guardrail("mood", f"unrecognized value '{mood}'")

    if energy is None:
        issues.append("energy is missing")
        log_guardrail("energy", "missing value")
    else:
        try:
            e = float(energy)
            if not 0.0 <= e <= 1.0:
                issues.append(f"energy {e} out of range [0.0, 1.0]")
                log_guardrail("energy", f"value {e} out of range")
        except (ValueError, TypeError):
            issues.append(f"energy must be a number, got '{energy}'")
            log_guardrail("energy", f"non-numeric value '{energy}'")

    if popularity is not None:
        try:
            p = int(popularity)
            if not 0 <= p <= 100:
                issues.append(f"popularity {p} out of range [0, 100]")
                log_guardrail("popularity", f"value {p} out of range")
        except (ValueError, TypeError):
            issues.append(f"popularity must be an integer, got '{popularity}'")
            log_guardrail("popularity", f"non-integer value '{popularity}'")

    return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def compute_confidence(raw_score: float, max_score: float = MAX_RAW_SCORE) -> float:
    """
    Normalize raw score to a [0.0, 1.0] confidence value.
    Scores above 70% of max are considered high confidence.
    """
    if max_score <= 0:
        return 0.0
    return round(min(raw_score / max_score, 1.0), 3)


def confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "HIGH"
    elif confidence >= 0.45:
        return "MEDIUM"
    else:
        return "LOW"


def score_recommendations(
    recommendations: list[dict],
) -> list[dict]:
    """
    Attach confidence score and label to each recommendation dict.
    Expects each dict to have a 'score' key.
    """
    scored = []
    for rec in recommendations:
        raw = rec.get("score", 0.0)
        conf = compute_confidence(raw)
        label = confidence_label(conf)
        log_confidence(rec.get("title", "?"), raw, conf)
        scored.append({**rec, "confidence": conf, "confidence_label": label})
    return scored


# ---------------------------------------------------------------------------
# Output guardrails / self-critique
# ---------------------------------------------------------------------------

def critique_recommendations(
    recommendations: list[dict],
    user_prefs: dict,
    genre_context: dict,
) -> list[str]:
    """
    Self-critique pass: inspect recommendations for obvious quality issues.
    Returns a list of critique notes (empty = no issues found).
    """
    notes = []
    genre = user_prefs.get("genre", "").lower()
    target_energy = float(user_prefs.get("energy", 0.5))
    typical_range = genre_context.get("typical_energy_range", [0.0, 1.0])

    if not recommendations:
        notes.append("No recommendations produced — catalog may be too small or filters too strict.")
        log_critique("Empty recommendation list")
        return notes

    # Check: top result confidence (compute from score if not yet attached)
    top = recommendations[0]
    top_conf = top.get("confidence") or compute_confidence(top.get("score", 0.0))
    if top_conf < 0.45:
        msg = f"Top recommendation confidence is LOW ({top_conf:.2f}) — results may be poor matches."
        notes.append(msg)
        log_critique(msg)

    # Check: genre coverage
    genre_hits = sum(1 for r in recommendations if r.get("genre", "").lower() == genre)
    if genre_hits == 0:
        msg = f"No results match requested genre '{genre}' — consider broadening preferences."
        notes.append(msg)
        log_critique(msg)

    # Check: energy mismatch against genre norms
    if target_energy < typical_range[0]:
        msg = (
            f"Requested energy ({target_energy}) is below typical range for '{genre}' "
            f"({typical_range[0]}–{typical_range[1]}). Results may feel inconsistent."
        )
        notes.append(msg)
        log_critique(msg)
    elif target_energy > typical_range[1]:
        msg = (
            f"Requested energy ({target_energy}) exceeds typical range for '{genre}' "
            f"({typical_range[0]}–{typical_range[1]}). Results may feel inconsistent."
        )
        notes.append(msg)
        log_critique(msg)

    # Check: artist diversity
    artists = [r.get("artist", "") for r in recommendations]
    duplicates = {a for a in artists if artists.count(a) > 1}
    if duplicates:
        msg = f"Artist diversity issue: {duplicates} appear more than once in top results."
        notes.append(msg)
        log_critique(msg)

    return notes


def compute_overall_confidence(recommendations: list[dict]) -> float:
    """Average confidence across all recommendations."""
    if not recommendations:
        return 0.0
    return round(sum(r.get("confidence", 0.0) for r in recommendations) / len(recommendations), 3)
