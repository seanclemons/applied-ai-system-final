# Model Card: Music Recommender Simulation

---

## 1. Model Name

**SoundMatch 1.0**

---

## 2. Goal / Task

SoundMatch tries to predict which songs a person will enjoy right now, based on the vibe they describe. Given a user's preferred genre, mood, energy level, emotional tone, and acoustic texture, it scans a catalog of 18 songs and returns the top 5 best matches — ranked from most to least compatible. It is not trying to learn over time or guess hidden preferences; it simply asks "how close is each song to what this person said they want?" and sorts accordingly.

---

## 3. Data Used

The catalog is stored in `data/songs.csv` and contains **18 songs**, each with 10 attributes:

| Attribute | Type | Description |
|---|---|---|
| genre | text | Musical style (pop, lofi, rock, jazz, etc.) |
| mood | text | Emotional context (happy, chill, intense, etc.) |
| energy | 0.0 – 1.0 | How loud and driven the track feels |
| valence | 0.0 – 1.0 | Emotional positivity (high = upbeat, low = dark) |
| acousticness | 0.0 – 1.0 | Organic vs. electronic sound texture |
| tempo_bpm | integer | Beats per minute |
| danceability | 0.0 – 1.0 | How suitable for dancing |

**Genres covered:** pop, lofi, rock, jazz, synthwave, ambient, indie pop, hip-hop, r&b, classical, country, EDM, metal, folk, funk

**Moods covered:** happy, chill, intense, relaxed, moody, focused, nostalgic, romantic, peaceful, energetic, angry

**Dataset limits:** Most non-pop genres have only one song each. The catalog reflects Western popular music almost entirely — no reggae, Latin, African, or world music is present. The data was hand-crafted for classroom use, not collected from real listening behavior.

---

## 4. Algorithm Summary

SoundMatch uses a **weighted scoring rule** to judge every song in the catalog against the user's preferences. Think of it like a judge at a cooking competition who grades each dish on five criteria, with some criteria worth more points than others.

For each song, the system awards points in five categories:

1. **Genre match** — worth up to 2.0 points. If the song's genre exactly matches what the user asked for, it gets the full 2 points. If not, it gets zero. This is the biggest single factor.

2. **Mood match** — worth up to 1.0 point. Same all-or-nothing rule. If the mood label matches, the song earns 1 point.

3. **Energy closeness** — worth up to 1.5 points. Instead of rewarding songs that are simply "high energy," the system rewards songs that are *close* to the user's target energy. A user who wants energy 0.8 prefers a song at 0.82 over a song at 0.5, even if both are considered "high."

4. **Valence closeness** — worth up to 1.0 point. Same proximity logic applied to emotional positivity.

5. **Acousticness closeness** — worth up to 0.5 points. Rewards songs whose organic/electronic texture matches the user's preference.

The five scores are added together (maximum possible: 6.0 points). All 18 songs are scored, then sorted highest to lowest, and the top 5 are returned with a plain-language explanation of which features contributed.

---

## 5. Observed Behavior / Biases

**Genre dominates everything.** Because genre is worth 2.0 out of a maximum 6.0 points, a song that matches genre but fails on mood, energy, and valence can still beat a song that matches mood, energy, and valence but has a slightly different genre label. For example, *Gym Hero* (pop/intense, energy 0.93) consistently ranks #2 for a pop/happy user who wants energy 0.8 — it shares the genre but the mood is wrong and energy is off. Meanwhile, *Rooftop Lights* (indie pop/happy, energy 0.76) drops to #3 even though it's a closer mood and energy match, simply because "indie pop" ≠ "pop."

**Adversarial conflict: genre beats large energy gaps.** When tested with a profile asking for ambient genre but energy 0.9 (a contradictory combination since ambient music is inherently low-energy), the system recommended *Spacewalk Thoughts* — an ambient/chill song at energy 0.28 — as the top result. The genre string matched, so it won, even though the actual track would feel completely wrong to someone expecting high-energy music. The genre weight drowned out a 0.62-point energy mismatch.

**Thin catalog creates false confidence.** When a genre has only one song, the system ranks that song #1 with high confidence and fills slots #2-5 with essentially random low-energy songs from unrelated genres. For a classical/romantic user, recommendations #2 through #5 were folk, ambient, jazz, and r&b — connected only because they happened to have low energy, not because they share any musical relationship with classical music.

**No variety protection.** The same artist can appear multiple times in the top results. For the lofi profile, LoRoom appears at both #2 and #3. A real streaming platform would actively push different artists even if one artist scored highest.

---

## 6. Evaluation Process

Five distinct user profiles were tested, including three realistic profiles and two adversarial "edge case" profiles designed to stress-test the scoring logic:

| Profile | Top Result | Score | Verdict |
|---|---|---|---|
| High-Energy Pop | Sunrise City | 5.92 / 6.00 | Correct — all features aligned |
| Chill Lofi Study | Library Rain | 5.89 / 6.00 | Correct — exactly the right vibe |
| Deep Intense Rock | Storm Runner | 5.90 / 6.00 | Correct — clear winner |
| Conflicting (ambient genre + energy 0.9) | Spacewalk Thoughts | 3.81 / 6.00 | Wrong — genre overrode energy |
| Underrepresented (classical + romantic) | Moonlight Remix | 4.78 / 6.00 | Partial — correct #1, arbitrary #2-5 |

A weight experiment was also run: energy weight doubled (1.5 → 3.0) and genre weight halved (2.0 → 1.0). Key finding: *Rooftop Lights* rose from #3 to #2 for the pop/happy profile, which felt more accurate since it better matches the mood. This confirmed that hand-tuned weights directly control what the user sees — there is no "right" answer, only tradeoffs.

Both of the automated tests in `tests/test_recommender.py` pass, verifying that the OOP interface correctly sorts songs by score and returns non-empty explanations.

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
- Classroom demonstration of how content-based filtering works
- Learning how weighted scoring turns structured data into a ranked list
- Exploring the tradeoffs between different feature weights in a recommender
- A starting point for understanding why real AI systems need much larger datasets and learned weights

**Not intended for:**
- Making real music recommendations for real users — the 18-song catalog is far too small and is not drawn from actual listening data
- Any context where fairness or representation matters — the dataset strongly underrepresents non-Western genres and is not suitable for diverse audiences
- Deployment in any product or public-facing application
- Drawing conclusions about what music people "should" like — the system reflects the preferences baked into its hand-crafted weights, not any objective truth about musical quality

---

## 8. Ideas for Improvement

1. **Soft genre matching** — Replace the binary genre match (0 or 2 points) with a similarity table where related genres earn partial credit. For example, "indie pop" → "pop" = 1.4 points instead of 0. This would prevent the cliff-edge penalty for closely related styles and reduce genre lock-in.

2. **Diversity penalty** — After scoring all songs, apply a rule that reduces a song's effective ranking if the same artist already appears in the top results. This ensures the user gets variety instead of seeing the same artist twice.

3. **Energy range preference** — Let the user specify a range like `energy: [0.6, 0.85]` rather than a single target. Any song within range scores maximum energy points; outside the range is penalized by distance. This makes the system more forgiving and more realistic — most people don't have an exact energy number in mind.

---

## 9. Personal Reflection

**Biggest learning moment:** The adversarial profile test was the clearest "aha" moment of the project. I set the genre to "ambient" and energy to 0.9 expecting the system to struggle — and it did, but not in the way I expected. It didn't return an error or a random result. It confidently returned a quiet ambient song as the perfect match, completely ignoring the massive energy contradiction, because the genre string matched. That taught me that a confident-looking output from an AI system can still be completely wrong. The system had no way to recognize that "ambient" and "energy 0.9" contradict each other — it just ran the math.

**How AI tools helped, and when I had to check them:** AI helped accelerate the design phase significantly — generating the algorithm recipe, suggesting weight rationale, and explaining the difference between `.sort()` and `sorted()` in clear terms. But the weight values (2.0 for genre, 1.5 for energy, etc.) required human judgment. The AI could explain *how* weighting works, but it couldn't tell me what the "right" weights are for a musical vibe — that required actually running the system, reading the results, and asking whether they felt correct. The adversarial profiles were suggested by the AI, which was genuinely useful: I wouldn't have thought to test "ambient genre + high energy" on my own.

**What surprised me about simple algorithms "feeling" like recommendations:** Even with just five features and five weights, the output reads like something a real recommender could produce. For the chill lofi profile, the top two results — *Library Rain* and *Midnight Coding* — are genuinely the right answer. The system doesn't understand music at all; it's doing arithmetic on five numbers. But because those five numbers were chosen to represent meaningful human concepts (vibe, intensity, texture), the math produces outputs that feel meaningful too. That gap between "it's just arithmetic" and "it feels intelligent" is probably the most important thing to understand about AI systems in general.

**What I'd try next:** The most interesting extension would be adding a simple collaborative layer — even just a CSV of "liked songs" per user profile — and using that to break ties between closely scored songs. If two songs score 3.85 and 3.78, the current system always picks the higher number. But if users similar to me consistently preferred the 3.78 song, that signal should matter. Bridging the gap between content-based and collaborative filtering, even at a tiny scale, would make the system meaningfully more realistic.
