"""
SoundMatch Test Harness
Runs the agent on predefined profiles and prints a pass/fail summary.

Usage:
    python -m tests.test_harness
"""

from __future__ import annotations

import sys
import io
import os

# Ensure Unicode output works on Windows terminals
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agent import run_agent

# ---------------------------------------------------------------------------
# Test cases
# Each case has:
#   profile       : user preferences passed to the agent
#   expect_top    : expected title of #1 recommendation
#   expect_genre  : at least one result must match this genre
#   min_confidence: overall confidence must meet or exceed this threshold
#   expect_valid  : True = expect successful run, False = expect guardrail block
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "name": "High-Energy Pop",
        "profile": {
            "genre": "pop", "mood": "happy",
            "energy": 0.8, "popularity": 85,
            "tags": ["uplifting", "danceable"],
        },
        "expect_top": "Sunrise City",
        "expect_genre": "pop",
        "min_confidence": 0.60,
        "expect_valid": True,
    },
    {
        "name": "Chill Lofi Study",
        "profile": {
            "genre": "lofi", "mood": "chill",
            "energy": 0.4, "popularity": 70,
            "tags": ["focused", "calm"],
        },
        "expect_top": "Midnight Coding",
        "expect_genre": "lofi",
        "min_confidence": 0.60,
        "expect_valid": True,
    },
    {
        "name": "Deep Intense Rock",
        "profile": {
            "genre": "rock", "mood": "intense",
            "energy": 0.92, "popularity": 65,
            "tags": ["aggressive", "powerful"],
        },
        "expect_top": "Storm Runner",
        "expect_genre": "rock",
        "min_confidence": 0.45,
        "expect_valid": True,
    },
    {
        "name": "Adversarial: Wrong Energy for Genre",
        "profile": {
            "genre": "metal", "mood": "peaceful",
            "energy": 0.1, "popularity": 50,
        },
        "expect_top": None,
        "expect_genre": None,
        "min_confidence": 0.0,
        "expect_valid": True,
        "note": "Low energy for metal — critique should flag energy mismatch.",
    },
    {
        "name": "Guardrail: Invalid Mood",
        "profile": {
            "genre": "pop", "mood": "hyped",
            "energy": 0.8, "popularity": 80,
        },
        "expect_top": None,
        "expect_genre": None,
        "min_confidence": 0.0,
        "expect_valid": False,
        "note": "'hyped' is not a recognized mood — should be blocked.",
    },
    {
        "name": "Guardrail: Energy Out of Range",
        "profile": {
            "genre": "jazz", "mood": "relaxed",
            "energy": 1.5, "popularity": 60,
        },
        "expect_top": None,
        "expect_genre": None,
        "min_confidence": 0.0,
        "expect_valid": False,
        "note": "energy=1.5 exceeds [0.0, 1.0] range.",
    },
    {
        "name": "Edge Case: Zero Popularity",
        "profile": {
            "genre": "ambient", "mood": "peaceful",
            "energy": 0.2, "popularity": 0,
        },
        "expect_top": None,
        "expect_genre": "ambient",
        "min_confidence": 0.30,
        "expect_valid": True,
        "note": "Rare genre with very low popularity preference.",
    },
    {
        "name": "Funk Groove",
        "profile": {
            "genre": "funk", "mood": "happy",
            "energy": 0.75, "popularity": 70,
        },
        "expect_top": "Sunday Groove",
        "expect_genre": "funk",
        "min_confidence": 0.40,
        "expect_valid": True,
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_test(case: dict, verbose_agent: bool = False) -> dict:
    profile = case["profile"]
    result = run_agent(profile, k=5, verbose=verbose_agent)

    passed_checks = []
    failed_checks = []

    # Check 1: valid/invalid profile handled correctly
    ran_ok = "error" not in result or result.get("error") == "invalid_profile"
    if case["expect_valid"]:
        if result.get("error") == "invalid_profile":
            failed_checks.append("expected valid run but got invalid_profile error")
        else:
            passed_checks.append("profile accepted (expected valid)")
    else:
        if result.get("error") == "invalid_profile":
            passed_checks.append("profile correctly rejected by guardrail")
        else:
            failed_checks.append("expected guardrail rejection but profile was accepted")

    recs = result.get("recommendations", [])

    # Check 2: top result matches expectation (only for valid cases with a target)
    if case["expect_valid"] and case.get("expect_top") and recs:
        top_title = recs[0]["title"]
        if top_title == case["expect_top"]:
            passed_checks.append(f"top result = '{top_title}' ✓")
        else:
            failed_checks.append(f"top result = '{top_title}', expected '{case['expect_top']}'")

    # Check 3: genre appears in results
    if case["expect_valid"] and case.get("expect_genre") and recs:
        genres_found = [r["genre"] for r in recs]
        if case["expect_genre"] in genres_found:
            passed_checks.append(f"genre '{case['expect_genre']}' present in results ✓")
        else:
            failed_checks.append(f"genre '{case['expect_genre']}' not found in results: {genres_found}")

    # Check 4: overall confidence threshold
    if case["expect_valid"] and recs:
        conf = result.get("overall_confidence", 0.0)
        if conf >= case["min_confidence"]:
            passed_checks.append(f"confidence {conf:.2f} >= {case['min_confidence']} ✓")
        else:
            failed_checks.append(f"confidence {conf:.2f} < min {case['min_confidence']}")

    # Check 5: steps completed
    if case["expect_valid"] and result.get("error") != "invalid_profile":
        expected_steps = {"profile_analysis", "rag_retrieval", "scoring", "self_critique", "final_response"}
        actual_steps = set(result.get("steps_taken", []))
        if expected_steps == actual_steps:
            passed_checks.append("all 5 agent steps completed ✓")
        else:
            missing = expected_steps - actual_steps
            failed_checks.append(f"missing steps: {missing}")

    status = "PASS" if not failed_checks else "FAIL"
    return {
        "name": case["name"],
        "status": status,
        "passed": passed_checks,
        "failed": failed_checks,
        "overall_confidence": result.get("overall_confidence", 0.0),
        "critique_notes": result.get("critique_notes", []),
        "note": case.get("note", ""),
        "elapsed": result.get("elapsed_seconds", 0.0),
    }


def print_summary(results: list[dict]):
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    avg_conf = sum(r["overall_confidence"] for r in results) / total if total else 0.0

    sep = "=" * 70
    print(f"\n{sep}")
    print("  SOUNDMATCH AGENT -- TEST HARNESS SUMMARY")
    print(sep)
    print(f"  Total tests   : {total}")
    print(f"  Passed        : {passed}  [OK]")
    print(f"  Failed        : {failed}  [!!]")
    print(f"  Avg confidence: {avg_conf:.2f}")
    print(sep)

    for r in results:
        icon = "PASS" if r["status"] == "PASS" else "FAIL"
        conf_str = f"conf={r['overall_confidence']:.2f}" if r["overall_confidence"] else ""
        print(f"  [{icon}] {r['name']:<35} {conf_str}")
        if r["note"]:
            print(f"         note: {r['note']}")
        for chk in r["failed"]:
            print(f"         FAIL: {chk}")
        if r["critique_notes"]:
            for note in r["critique_notes"]:
                print(f"         critique: {note}")

    print(sep)
    pct = int(passed / total * 100) if total else 0
    print(f"  Result: {passed}/{total} tests passed ({pct}%)")
    print(sep + "\n")


def main():
    print("\nRunning SoundMatch Test Harness...\n")
    results = []
    for case in TEST_CASES:
        print(f"  Testing: {case['name']} ...", end=" ", flush=True)
        result = run_test(case, verbose_agent=False)
        print(result["status"])
        results.append(result)

    print_summary(results)


if __name__ == "__main__":
    main()
