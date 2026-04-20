# SoundMatch 2.0 — Applied AI Music Recommendation System

> **Final Project — AI 110 | Extended from Module 3 Music Recommender Simulation**

---

## Original Project

**Base project:** `ai110-module3show-musicrecommendersimulation-starter` (Module 3)

SoundMatch 1.0 was a content-based music recommendation engine that scored songs against a user preference profile using five weighted features: genre, mood, energy, valence, and acousticness. It demonstrated four scoring modes (default, genre_first, mood_first, energy_focused) and a greedy diversity penalty to avoid artist/genre repetition. The system produced transparent, auditable ranked playlists but had no input validation, no retrieval layer, and no way to measure recommendation quality.

---

## What's New in SoundMatch 2.0

| Feature | What was added |
|---|---|
| **Agentic Workflow** | 5-step orchestrator with fully observable intermediate output |
| **RAG (Multi-Source Retrieval)** | Genre knowledge base (`genre_docs.json`) + song catalog queried before scoring |
| **Confidence Scoring** | Every recommendation rated HIGH / MEDIUM / LOW with numeric score |
| **Input Guardrails** | Validates genre, mood, energy, and popularity before any processing |
| **Self-Critique** | Agent checks its own output for energy mismatch, genre gaps, artist duplicates |
| **Persona Specialization** | Few-shot response templates adapt tone to user context (workout, study, default) |
| **Test Harness** | 8-case evaluation script with pass/fail summary and average confidence report |
| **Structured Logging** | All steps, guardrail triggers, and errors written to `logs/session.log` |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input (CLI)                         │
│           { genre, mood, energy, popularity, tags }             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                           │
│                       src/agent.py                              │
│                                                                 │
│  STEP 1: Profile Analysis ──► src/evaluator.py (guardrails)    │
│            │  Validate genre, mood, energy range               │
│            │  Block invalid input before processing            │
│            ▼                                                    │
│  STEP 2: RAG Retrieval ─────► src/retriever.py                 │
│            │  Source 1: data/songs.csv  (song catalog)         │
│            │  Source 2: data/genre_docs.json  (knowledge base) │
│            │  Returns: candidates + genre/mood context         │
│            ▼                                                    │
│  STEP 3: Scoring ───────────► src/recommender.py               │
│            │  Weighted feature scoring (genre, mood, energy)   │
│            │  Diversity penalty (artist/genre dedup)           │
│            ▼                                                    │
│  STEP 4: Self-Critique ─────► src/evaluator.py                 │
│            │  Check: top confidence, genre coverage            │
│            │  Check: energy vs genre norms, artist duplicates  │
│            ▼                                                    │
│  STEP 5: Final Response ────► Persona templates (few-shot)     │
│            │  Attach confidence labels, pick persona tone      │
│            ▼                                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴─────────────┐
              ▼                            ▼
   Ranked Playlist + Confidence     logs/session.log
   (stdout table)                   (structured log)
              │
              ▼
   ┌──────────────────────┐
   │   Test Harness       │
   │  tests/test_harness  │
   │  8 cases, pass/fail  │
   │  + confidence summary│
   └──────────────────────┘
```

---

## Project Structure

```
applied-ai-system-final/
├── src/
│   ├── agent.py          # Agentic orchestrator (5-step workflow)
│   ├── recommender.py    # Core scoring engine (Module 3 base)
│   ├── retriever.py      # RAG multi-source retrieval
│   ├── evaluator.py      # Confidence scoring + guardrails
│   ├── logger.py         # Structured logging
│   └── main.py           # CLI demo (3 demos: profiles, modes, guardrails)
├── data/
│   ├── songs.csv         # 18-song catalog with 13 features
│   └── genre_docs.json   # Genre knowledge base (15 genres, mood context)
├── tests/
│   ├── test_recommender.py   # Original unit tests (Module 3)
│   └── test_harness.py       # New evaluation harness (8 test cases)
├── assets/               # Architecture diagrams and screenshots
├── logs/                 # Auto-created; session.log written at runtime
├── requirements.txt
└── README.md
```

---

## Demo Walkthrough

Watch the full end-to-end demo (5 minutes) including the recommender, guardrail tester, and test harness:

**[▶ Watch on Loom](https://www.loom.com/share/dc330a59c16b4e668422a9a193f9a11a)**

The demo covers:
- Profile: High-Energy Pop → 5 agent steps → ranked results with confidence scores
- Profile: Chill Lofi Study → `study_buddy` persona auto-selected
- Guardrail test: invalid mood `hyped` and energy `1.5` both blocked before scoring
- Test harness: 8/8 tests passing with pass/fail summary

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/seanclemons/applied-ai-system-final.git
cd applied-ai-system-final
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the full agent demo

```bash
python -m src.main
```

### 5. Run the test harness

```bash
python -m tests.test_harness
```

### 6. Run the original unit tests

```bash
pytest tests/test_recommender.py -v
```

---

## Sample Interactions

### Example 1 — High-Energy Pop (full agent, verbose)

```
  [AGENT STEP 1] Profile Analysis
    • genre: pop
    • mood: happy
    • energy: 0.8
    ✓ Profile validated — no issues found.

  [AGENT STEP 2] RAG Retrieval
    • sources: songs_csv, genre_docs_json
    • genre matches: 3
    • mood matches: 4
    • total candidates: 12
    ℹ Typical use cases: parties, workouts, commute, background music

  [AGENT STEP 3] Scoring
    #1 Sunrise City by Neon Echo — score 7.41
    #2 Sunday Groove by Funktown Five — score 5.25

  [AGENT STEP 4] Self-Critique
    ✓ No quality issues detected.

  [AGENT STEP 5] Final Response
    • persona: default
    • overall confidence: 0.74

  PROFILE : High-Energy Pop
  PERSONA : default  |  overall confidence: 0.74  |  steps: 5/5

  Rank  Title          Artist         Genre  Score  Conf
  #1    Sunrise City   Neon Echo      pop    7.41   1.00 [HIGH]
  #2    Sunday Groove  Funktown Five  funk   5.25   0.88 [HIGH]
```

### Example 2 — Guardrail blocking invalid mood

```
  Input: Invalid mood 'hyped'

  [AGENT STEP 1] Profile Analysis
    • mood: hyped
    ⚠ GUARDRAIL: mood 'hyped' is not recognized

  ✓ Guardrail activated — system safely blocked invalid request.
  → Validation failed: mood 'hyped' is not recognized
```

### Example 3 — Test harness summary

```
  Testing: High-Energy Pop ... PASS
  Testing: Chill Lofi Study ... PASS
  Testing: Deep Intense Rock ... PASS
  Testing: Adversarial: Wrong Energy for Genre ... PASS
  Testing: Guardrail: Invalid Mood ... PASS
  Testing: Guardrail: Energy Out of Range ... PASS
  Testing: Edge Case: Zero Popularity ... PASS
  Testing: Funk Groove ... PASS

  ======================================================================
    VIBEFINDER AGENT — TEST HARNESS SUMMARY
  ======================================================================
    Total tests   : 8
    Passed        : 8  ✓
    Failed        : 0  ✗
    Avg confidence: 0.52
  ======================================================================
    Result: 8/8 tests passed (100%)
```

---

## Design Decisions

**Why an agentic pipeline instead of a single function?**
Separating retrieval, scoring, critique, and output into distinct steps makes each component independently testable and auditable. If the system gives a bad result, the logged steps show exactly where the failure occurred.

**Why a local knowledge base for RAG instead of a web API?**
The system is designed to run fully offline without API keys. The `genre_docs.json` knowledge base provides rich contextual grounding (energy ranges, mood context, use cases) that meaningfully improves critique quality compared to scoring alone.

**Why rule-based confidence scoring instead of a neural model?**
The recommender's maximum possible score is deterministic (6.0 points). Normalizing raw scores to [0, 1] produces honest, calibrated confidence values without requiring an external model or training data.

**Trade-offs:**
- The 18-song catalog limits genre diversity — single-song genres produce low-confidence results by design, which the self-critique step flags correctly.
- Persona selection is heuristic (mood + energy threshold) rather than learned — this is transparent and easy to audit but may feel simplistic for edge cases.

---

## Testing Summary

8 test cases were run across the evaluation harness:

| Category | Cases | Result |
|---|---|---|
| Core profiles (pop, lofi, rock) | 3 | All passed — correct top results, confidence >= 0.60 |
| Adversarial (wrong energy for genre) | 1 | Passed — self-critique correctly flagged energy mismatch |
| Guardrail tests (invalid mood, out-of-range energy) | 2 | Passed — both correctly rejected before scoring |
| Edge cases (zero popularity, rare genre) | 2 | Passed — results produced with appropriate low confidence |

Average confidence across valid profiles: **0.74**. Guardrail tests produced 0.0 confidence (blocked). The system struggled most with single-song genres (funk, ambient) where catalog thinness limits recommendation diversity — the critique layer surfaces this automatically.

---

## Reflection on AI Collaboration and System Design

### How AI was used
Claude Code was used throughout this project for architecture planning, code generation, debugging import errors, and structuring the test harness. Prompts were iterative — each component was designed in conversation, reviewed, and refined before moving to the next.

### One helpful AI suggestion
When designing the retrieval layer, the AI suggested separating multi-source retrieval into three priority tiers (genre matches → mood matches → energy proximity) rather than a flat sort. This directly improved the quality of candidates passed to the scorer and made the retrieval logic easier to explain and debug.

### One flawed AI suggestion
An early draft of the confidence scoring used `score / max_possible_score` where `max_possible_score` was dynamically computed per-query based on the weights active in the scoring mode. This made confidence values incomparable across modes (a score of 0.80 in `genre_first` meant something different than 0.80 in `mood_first`). The fix was to use a fixed normalization constant (6.0) so confidence is always on the same scale regardless of mode.

### Limitations and future improvements
- **Catalog size**: 18 songs is too small for real-world use. The system is architecturally ready for a larger dataset — `songs.csv` can be replaced with any CSV matching the schema.
- **Genre lock-in bias**: Genre still contributes 2.0/6.0 (33%) of the max score, which can override better energy/mood matches from adjacent genres.
- **No user history**: The system has no memory of past plays or ratings. Adding a feedback loop (thumbs up/down) would enable adaptive personalization over time.
- **Persona heuristics**: The three personas (default, workout_coach, study_buddy) cover common cases but a production system would learn persona from interaction history.
#   a p p l i e d - a i - s y s t e m - f i n a l  
 