"""
SoundMatch — Streamlit Demo UI
Run with: streamlit run src/app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import time

from src.agent import run_agent
from src.evaluator import VALID_GENRES, VALID_MOODS

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SoundMatch AI",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 800; color: #1DB954; margin-bottom: 0; }
    .sub-title  { font-size: 1rem; color: #888; margin-top: 0; }
    .step-box   { background: #1a1a2e; border-left: 4px solid #1DB954;
                  padding: 10px 16px; border-radius: 6px; margin: 6px 0; }
    .step-label { font-weight: 700; color: #1DB954; font-size: 0.85rem; }
    .guardrail  { background: #2d1a1a; border-left: 4px solid #e05c5c;
                  padding: 10px 16px; border-radius: 6px; margin: 6px 0; }
    .critique   { background: #2d2a1a; border-left: 4px solid #f0a500;
                  padding: 10px 16px; border-radius: 6px; margin: 6px 0; }
    .conf-high   { color: #1DB954; font-weight: 700; }
    .conf-medium { color: #f0a500; font-weight: 700; }
    .conf-low    { color: #e05c5c; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<p class="main-title">🎵 SoundMatch</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Agentic AI Music Recommendation System — AI 110 Final Project</p>', unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🎧 Recommender", "🛡️ Guardrail Tester", "🧪 Test Harness"])

# ===========================================================================
# TAB 1 — Recommender
# ===========================================================================
with tab1:
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Your Profile")

        genre = st.selectbox("Genre", sorted(VALID_GENRES), index=sorted(VALID_GENRES).index("pop"))
        mood  = st.selectbox("Mood",  sorted(VALID_MOODS),  index=sorted(VALID_MOODS).index("happy"))
        energy = st.slider("Energy", 0.0, 1.0, 0.8, 0.01,
                           help="0 = very calm, 1 = maximum intensity")
        popularity = st.slider("Popularity target", 0, 100, 80,
                               help="0 = underground, 100 = chart-topping")
        mode = st.selectbox("Scoring mode",
                            ["default", "genre_first", "mood_first", "energy_focused"],
                            help="Changes how the agent weights each feature")
        diversity = st.toggle("Diversity penalty", value=True,
                              help="Prevents the same artist appearing twice")
        k = st.slider("Results", 3, 10, 5)

        run_btn = st.button("▶ Run SoundMatch", use_container_width=True, type="primary")

    with col_right:
        if run_btn:
            user_prefs = {
                "genre": genre, "mood": mood,
                "energy": energy, "popularity": popularity,
                "mood_tags": [], "valence": energy, "acousticness": 1 - energy,
            }

            # ── Agent step display ──────────────────────────────────────
            st.subheader("Agent Steps")
            step_placeholders = []
            for i in range(1, 6):
                step_placeholders.append(st.empty())

            STEP_NAMES = [
                "Profile Analysis",
                "RAG Retrieval",
                "Scoring",
                "Self-Critique",
                "Final Response",
            ]

            # Animate steps
            for i, name in enumerate(STEP_NAMES):
                step_placeholders[i].markdown(
                    f'<div class="step-box"><span class="step-label">⏳ STEP {i+1}</span> — {name}</div>',
                    unsafe_allow_html=True,
                )
                time.sleep(0.25)

            # Run agent (silent)
            result = run_agent(user_prefs, k=k, mode=mode,
                               use_diversity=diversity, verbose=False)

            # Mark steps done
            for i, name in enumerate(STEP_NAMES):
                step_placeholders[i].markdown(
                    f'<div class="step-box"><span class="step-label">✓ STEP {i+1}</span> — {name}</div>',
                    unsafe_allow_html=True,
                )

            st.divider()

            # ── Guardrail block ─────────────────────────────────────────
            if result.get("error") == "invalid_profile":
                for note in result.get("critique_notes", []):
                    st.markdown(
                        f'<div class="guardrail">🚫 <strong>Guardrail triggered</strong><br>{note}</div>',
                        unsafe_allow_html=True,
                    )
                st.stop()

            # ── Metadata row ────────────────────────────────────────────
            recs = result["recommendations"]
            conf = result["overall_confidence"]
            persona = result["persona"]
            elapsed = result["elapsed_seconds"]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall Confidence", f"{conf:.0%}")
            m2.metric("Persona", persona.replace("_", " ").title())
            m3.metric("Mode", mode.replace("_", " ").title())
            m4.metric("Elapsed", f"{elapsed:.3f}s")

            # ── Persona intro ───────────────────────────────────────────
            st.info(f"💬 {result.get('persona_intro', '')}")

            # ── Results table ───────────────────────────────────────────
            st.subheader("Recommendations")

            def conf_badge(lbl):
                colors = {"HIGH": "🟢", "MEDIUM": "🟡", "LOW": "🔴"}
                return f"{colors.get(lbl, '⚪')} {lbl}"

            rows = []
            for i, r in enumerate(recs, 1):
                rows.append({
                    "Rank": f"#{i}",
                    "Title": r["title"],
                    "Artist": r["artist"],
                    "Genre": r["genre"],
                    "Mood": r["mood"],
                    "Energy": f"{r['energy']:.2f}",
                    "Score": f"{r['score']:.2f}",
                    "Confidence": conf_badge(r["confidence_label"]),
                    "Why": " | ".join(r.get("reasons", [])[:2])
                            if isinstance(r.get("reasons"), list)
                            else str(r.get("reasons", ""))[:60],
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # ── Critique notes ──────────────────────────────────────────
            critique = result.get("critique_notes", [])
            if critique:
                st.subheader("Self-Critique Notes")
                for note in critique:
                    st.markdown(
                        f'<div class="critique">⚠️ {note}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("✓ Self-critique passed — no quality issues detected.")

            # ── RAG context ─────────────────────────────────────────────
            with st.expander("📚 RAG Retrieval Details"):
                info = result.get("retrieval_info", {})
                sc = info.get("source_counts", {})
                st.write(f"**Sources:** {', '.join(info.get('sources_used', []))}")
                st.write(f"**Genre matches:** {sc.get('genre_matches', '?')}")
                st.write(f"**Mood matches:** {sc.get('mood_matches', '?')}")
                st.write(f"**Total candidates scored:** {len(info.get('candidates', []))}")
                gc = info.get("genre_context", {})
                if gc.get("description"):
                    st.write(f"**Genre context:** {gc['description']}")
                if gc.get("use_cases"):
                    st.write(f"**Typical use cases:** {', '.join(gc['use_cases'])}")
                if info.get("mood_context"):
                    st.write(f"**Mood context:** {info['mood_context']}")

        else:
            st.info("👈 Set your preferences and click **Run SoundMatch** to get recommendations.")

# ===========================================================================
# TAB 2 — Guardrail Tester
# ===========================================================================
with tab2:
    st.subheader("Test Guardrail Behavior")
    st.write("Enter any values — the system will validate them before processing.")

    c1, c2 = st.columns(2)
    with c1:
        gt_genre = st.text_input("Genre (free text)", value="pop")
        gt_mood  = st.text_input("Mood (free text)",  value="hyped")
    with c2:
        gt_energy = st.text_input("Energy (free text)", value="1.5")
        gt_pop    = st.text_input("Popularity (free text)", value="80")

    if st.button("▶ Test Guardrails", type="primary"):
        try:
            energy_val = float(gt_energy)
        except ValueError:
            energy_val = gt_energy

        try:
            pop_val = int(gt_pop)
        except ValueError:
            pop_val = gt_pop

        test_prefs = {
            "genre": gt_genre, "mood": gt_mood,
            "energy": energy_val, "popularity": pop_val,
        }

        result = run_agent(test_prefs, verbose=False)

        if result.get("error") == "invalid_profile":
            st.error("🚫 Guardrail triggered — request blocked before scoring.")
            for note in result.get("critique_notes", []):
                st.markdown(
                    f'<div class="guardrail">❌ {note}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("✅ Profile accepted — all fields valid.")
            recs = result.get("recommendations", [])
            if recs:
                st.write(f"Top result: **{recs[0]['title']}** by {recs[0]['artist']} "
                         f"(score {recs[0]['score']:.2f}, confidence {recs[0]['confidence_label']})")

    st.divider()
    st.markdown("**Quick examples to try:**")
    st.code("Genre: pop   | Mood: hyped     | Energy: 0.8  → blocked (invalid mood)")
    st.code("Genre: jazz  | Mood: relaxed   | Energy: 1.5  → blocked (energy out of range)")
    st.code("Genre:       | Mood: chill     | Energy: 0.4  → blocked (missing genre)")
    st.code("Genre: lofi  | Mood: chill     | Energy: 0.4  → accepted")

# ===========================================================================
# TAB 3 — Test Harness
# ===========================================================================
with tab3:
    st.subheader("Automated Test Harness")
    st.write("Runs 8 predefined test cases and reports pass/fail with confidence scores.")

    if st.button("▶ Run All Tests", type="primary"):
        from tests.test_harness import TEST_CASES, run_test

        results = []
        progress = st.progress(0, text="Running tests...")
        status_area = st.empty()

        for i, case in enumerate(TEST_CASES):
            status_area.write(f"Testing: **{case['name']}**...")
            r = run_test(case, verbose_agent=False)
            results.append(r)
            progress.progress((i + 1) / len(TEST_CASES), text=f"{i+1}/{len(TEST_CASES)} tests complete")

        status_area.empty()
        progress.empty()

        passed = sum(1 for r in results if r["status"] == "PASS")
        total  = len(results)
        avg_conf = sum(r["overall_confidence"] for r in results) / total

        m1, m2, m3 = st.columns(3)
        m1.metric("Tests Passed", f"{passed}/{total}")
        m2.metric("Pass Rate", f"{int(passed/total*100)}%")
        m3.metric("Avg Confidence", f"{avg_conf:.2f}")

        st.divider()

        for r in results:
            icon = "✅" if r["status"] == "PASS" else "❌"
            conf_str = f"conf={r['overall_confidence']:.2f}" if r["overall_confidence"] else "blocked"
            with st.expander(f"{icon} {r['name']} — {conf_str}"):
                if r["note"]:
                    st.caption(r["note"])
                if r["failed"]:
                    for f in r["failed"]:
                        st.error(f)
                for p in r["passed"]:
                    st.success(p)
                if r["critique_notes"]:
                    for note in r["critique_notes"]:
                        st.warning(note)
    else:
        st.info("Click **Run All Tests** to execute the full evaluation harness.")
