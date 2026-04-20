# Model Card: SoundMatch 2.0 — Applied AI Music Recommendation System

> Extended from SoundMatch 1.0 (Module 3 Music Recommender Simulation)

---

## 1. Model Name and Version

**SoundMatch 2.0**
Base project: `ai110-module3show-musicrecommendersimulation-starter` (Module 3)

---

## 2. What Changed from 1.0 to 2.0

SoundMatch 1.0 was a content-based scoring engine with no input validation, no retrieval layer, and no way to measure recommendation quality. Version 2.0 wraps that engine inside a 5-step agentic workflow:

| Component | 1.0 | 2.0 |
|---|---|---|
| Input validation | None | Guardrails block invalid genre/mood/energy |
| Retrieval | Load all 18 songs | Multi-source RAG (songs.csv + genre_docs.json) |
| Scoring | Same | Same engine, now fed curated candidates |
| Output quality check | None | Self-critique step flags energy mismatches, artist duplicates |
| Confidence | None | Every result rated HIGH / MEDIUM / LOW |
| Testing | 2 unit tests | 8-case automated test harness with pass/fail summary |
| Logging | None | Structured session log written to logs/session.log |
| UI | CLI only | Streamlit demo app (src/app.py) |

---

## 3. Goal / Task

SoundMatch recommends music by matching a user's stated preferences (genre, mood, energy, popularity) against a catalog of songs. It does not learn from listening history — it reasons from explicit preferences using a transparent scoring algorithm enriched with a genre knowledge base.

---

## 4. Data Sources

| Source | Contents | Role |
|---|---|---|
| `data/songs.csv` | 18 songs, 13 features each | Primary song catalog |
| `data/genre_docs.json` | 15 genre descriptions, energy ranges, mood context | RAG knowledge base for retrieval context and self-critique |

**Catalog limits:** Most non-pop genres have only one song. The dataset is hand-crafted for classroom use and does not represent real listening behavior or diverse global music.

---

## 5. Algorithm Summary

**Step 1 — Profile Analysis:** Validate genre, mood, energy (0–1), and popularity (0–100). Block invalid inputs before any processing.

**Step 2 — RAG Retrieval:** Query songs.csv and genre_docs.json. Return up to 12 candidates prioritized by: (1) exact genre match, (2) mood match, (3) energy proximity. Enrich with genre context (typical energy range, use cases, mood description).

**Step 3 — Scoring:** Apply weighted feature scoring to all candidates:
- Genre match: up to 2.0 pts (exact match only)
- Mood match: up to 1.0 pts
- Energy proximity: up to 1.5 pts
- Valence proximity: up to 1.0 pts
- Acousticness proximity: up to 0.5 pts
- Popularity proximity: up to 1.0 pts (normalized)
- Mood tags: partial credit per matched tag

**Step 4 — Self-Critique:** Check top confidence, genre coverage, energy vs. genre norms (using genre_docs.json), and artist diversity. Log warnings for any issues.

**Step 5 — Final Response:** Normalize scores to [0, 1] confidence, attach HIGH/MEDIUM/LOW labels, select persona (workout_coach / study_buddy / default) based on mood and energy cues.

---

## 6. Observed Biases and Limitations

**Genre lock-in persists.** Genre contributes 2.0 of 6.0 maximum points (33%). A song that matches genre but misses on mood and energy can still outrank a closer match from a related genre. *Gym Hero* (pop/intense) consistently ranks #2 for a pop/happy profile despite the mood mismatch.

**Thin catalog creates low confidence for rare genres.** Single-song genres (rock, metal, folk, etc.) produce one HIGH-confidence result then fill remaining slots with energy-proximity matches from unrelated genres. The self-critique step now surfaces this automatically.

**Self-critique relies on genre_docs energy ranges.** If a user requests a genre not in genre_docs.json, the typical energy range defaults to [0.0, 1.0] and no energy mismatch warning fires. The system degrades gracefully but silently.

**Persona selection is heuristic.** The three personas (workout_coach, study_buddy, default) are assigned by mood + energy threshold rules, not learned from user behavior. They affect tone only — not ranking.

**No memory or feedback.** The system has no user history. Every run starts fresh. Two users with the same preferences get identical results.

---

## 7. Reliability and Testing Results

The automated test harness (`tests/test_harness.py`) runs 8 predefined cases:

| Category | Cases | Result | Notes |
|---|---|---|---|
| Core profiles (pop, lofi, rock) | 3 | PASS | Correct top result, confidence >= 0.45 |
| Adversarial (metal + low energy) | 1 | PASS | Self-critique flagged energy mismatch |
| Guardrail (invalid mood) | 1 | PASS | Blocked before scoring |
| Guardrail (energy out of range) | 1 | PASS | Blocked before scoring |
| Edge case (zero popularity, ambient) | 1 | PASS | Results produced, low confidence expected |
| Funk groove | 1 | PASS | Correct top result (Sunday Groove) |

**Overall: 8/8 tests passed. Average confidence across valid profiles: 0.68.**

Guardrail tests correctly produce 0.0 confidence (blocked). The adversarial metal/peaceful test produced a self-critique warning: *"Requested energy (0.1) is below typical range for 'metal' (0.8–1.0)."* — confirming the RAG knowledge base is actively informing quality checks.

---

## 8. AI Collaboration Reflection

### How AI was used
Claude Code was used throughout the final project for architecture planning, generating boilerplate code, debugging import errors, and drafting the test harness structure. Each component was designed through conversation, reviewed against the rubric, and refined before implementation.

### One helpful AI suggestion
When designing the RAG retrieval layer, the AI suggested splitting candidates into three priority tiers — genre matches first, then mood matches, then energy proximity — rather than scoring and sorting all 18 songs at once. This improved candidate quality passed to the scorer and made the retrieval logic transparent and debuggable. It was a design decision I would not have landed on as quickly independently.

### One flawed AI suggestion
An early draft normalized confidence scores dynamically per scoring mode — dividing raw scores by the maximum achievable score under that mode's weights. This made confidence values incomparable: a 0.80 confidence in `genre_first` mode represented a different quality of match than 0.80 in `mood_first` mode. The AI did not flag this until the problem was pointed out. The fix was simple — use a fixed normalization constant (6.0) — but it required recognizing the subtle design flaw first.

---

## 9. Intended and Non-Intended Use

**Intended use:**
- Portfolio demonstration of agentic AI system design
- Educational exploration of RAG, guardrails, confidence scoring, and evaluation harnesses
- Starting point for a larger music recommendation system

**Not intended for:**
- Real music recommendations — 18 songs is not a usable catalog
- Any context where demographic or cultural representation matters — the dataset is Western-only
- Production deployment of any kind

---

## 10. Limitations and Future Work

1. **Larger catalog** — The architecture is ready; `songs.csv` can be replaced with any CSV matching the 13-column schema. Connecting to a Spotify API export would make the system genuinely useful.

2. **Soft genre matching** — Replace binary genre match (0 or 2 pts) with a similarity table where related genres earn partial credit (e.g., indie pop → pop = 1.4 pts).

3. **User feedback loop** — Add thumbs up/down logging to a `feedback.csv`. Use that signal to re-weight scores over time — bridging the gap between content-based and collaborative filtering.

4. **Learned persona selection** — Replace the heuristic mood/energy threshold with a simple classifier trained on user feedback history.
