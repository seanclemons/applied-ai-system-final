# SoundMatch 2.0 — Applied AI Music Recommendation System

**AI 110 Final Project** | Extended from `ai110-module3show-musicrecommendersimulation-starter` (Module 3)

SoundMatch 1.0 was a content-based scoring engine that ranked songs by genre, mood, and energy. Version 2.0 wraps that engine in a 5-step agentic pipeline with RAG retrieval, input guardrails, self-critique, confidence scoring, and an automated test harness.

---

## New Features

| Feature | Description |
|---|---|
| Agentic Workflow | 5-step orchestrator with observable intermediate output |
| RAG Retrieval | Songs catalog + genre knowledge base queried before scoring |
| Input Guardrails | Validates genre, mood, and energy before any processing |
| Self-Critique | Agent checks its own output for quality issues |
| Confidence Scoring | Every result rated HIGH / MEDIUM / LOW |
| Persona Specialization | Response tone adapts to user context |
| Test Harness | 8-case eval script with pass/fail summary |
| Streamlit UI | Interactive demo app (`src/app.py`) |

---

## System Architecture

See [`assets/architecture.md`](assets/architecture.md) for the full Mermaid diagram.

```
User Input
    │
    ▼
Step 1: Profile Analysis  →  validate genre, mood, energy (guardrails)
    │
    ▼
Step 2: RAG Retrieval  →  songs.csv + genre_docs.json
    │
    ▼
Step 3: Scoring  →  weighted feature scoring + diversity penalty
    │
    ▼
Step 4: Self-Critique  →  flag energy mismatches, artist duplicates
    │
    ▼
Step 5: Final Response  →  confidence labels + persona tone
    │
    ├── Ranked Playlist (stdout / UI)
    └── logs/session.log
```

---

## Project Structure

```
applied-ai-system-final/
├── src/
│   ├── agent.py          # Agentic orchestrator
│   ├── app.py            # Streamlit UI
│   ├── recommender.py    # Core scoring engine (Module 3 base)
│   ├── retriever.py      # RAG retrieval
│   ├── evaluator.py      # Guardrails + confidence scoring
│   ├── logger.py         # Structured logging
│   └── main.py           # CLI demo
├── data/
│   ├── songs.csv         # 18-song catalog
│   └── genre_docs.json   # Genre knowledge base
├── tests/
│   ├── test_recommender.py
│   └── test_harness.py   # 8-case evaluation harness
├── assets/
│   └── architecture.md   # System diagram (Mermaid)
├── logs/                 # Auto-created at runtime
└── requirements.txt
```

---

## Setup

```bash
git clone https://github.com/seanclemons/applied-ai-system-final.git
cd applied-ai-system-final
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**Run the UI:**
```bash
python -m streamlit run src/app.py
```

**Run the CLI demo:**
```bash
python -m src.main
```

**Run the test harness:**
```bash
python -m tests.test_harness
```

---

## Sample Outputs

**Example 1 — High-Energy Pop**
```
[STEP 1] Profile validated — no issues found.
[STEP 2] sources: songs_csv, genre_docs_json | candidates: 12
[STEP 3] #1 Sunrise City — score 7.41  #2 Sunday Groove — score 5.25
[STEP 4] No quality issues detected.
[STEP 5] persona: default | confidence: 0.86
```

**Example 2 — Guardrail blocked**
```
[STEP 1] ⚠ GUARDRAIL: mood 'hyped' is not recognized
→ Request blocked before scoring.
```

**Example 3 — Test harness**
```
8/8 tests passed (100%) | Avg confidence: 0.52
```

---

## Demo Video

**[▶ Watch on Loom](https://www.loom.com/share/dc330a59c16b4e668422a9a193f9a11a)**

---

## Design Decisions

- **Agentic pipeline over single function** — each step is independently testable; logs show exactly where failures occur.
- **Local RAG over web API** — runs fully offline; genre_docs.json enriches self-critique without any API keys.
- **Fixed confidence normalization** — dividing by a constant (6.0) keeps scores comparable across all scoring modes.

---

## Testing Summary

| Category | Cases | Result |
|---|---|---|
| Core profiles (pop, lofi, rock) | 3 | PASS — correct top results |
| Adversarial (wrong energy for genre) | 1 | PASS — self-critique flagged mismatch |
| Guardrail (invalid mood, out-of-range energy) | 2 | PASS — both blocked before scoring |
| Edge cases (zero popularity, rare genre) | 2 | PASS — low confidence as expected |

**8/8 passed. Avg confidence across valid profiles: 0.68.**

---

## Reflection

**AI collaboration:** Claude Code was used for architecture planning, code generation, and debugging. Prompts were iterative — each component was designed, reviewed, and refined before moving forward.

**Helpful suggestion:** Splitting RAG retrieval into three priority tiers (genre → mood → energy proximity) rather than a flat sort improved candidate quality and made the logic easier to explain.

**Flawed suggestion:** An early confidence scoring draft normalized dynamically per scoring mode, making scores incomparable across modes. Fixed by using a constant (6.0) instead.

**Limitations:** 18-song catalog is too small for real use; genre contributes 33% of max score which can override better energy/mood matches; no user history or feedback loop.
