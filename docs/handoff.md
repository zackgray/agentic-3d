# Handoff: h7 confirmed on the fourth held-out set

Written 2026-11-18 after the fourth held-out set ran on h7. Replace this file when the next piece of work ends.

## Read first

1. `README.md`, then `docs/eval-method.md` (measurement rules, noise floor, Phase 3 ground rules).
2. `docs/journal.md` (h7 entries and the fourth held-out result); earlier Phase 3 entries are in `docs/journal-phase-3-h1-h6.md`.
3. `docs/case-study.md` for the story as it stands.

## Where things stand

h7 is the current harness (the `h7` tag), and its claim is now made on unseen tasks. All four held-out sets are spent.

| Suite | No MCP pass | No MCP tokens per pass | Harness | Harness pass | Harness tokens per pass | Ratio | Geometric-mean ratio |
|---|---|---|---|---|---|---|---|
| Development (30 × 3) | 80/90 | 26,727 | h7 | 86/90 | 6,489 | 0.24 | 0.29 |
| Fourth held-out (h7) | 18/24 | 58,147 | h7 | 20/24 | 11,934 | 0.21 | 0.27 |
| Fourth held-out without w05 | 16/21 | 33,774 | h7 | 19/21 | 10,755 | 0.32 | 0.34 |
| Third held-out without z05 (h6) | 18/21 | 35,480 | h6 | 18/21 | 22,257 | 0.63 | 0.43 |

h7's held-out losses are genuine: two w05 runs lost the top-edge round while refilling the top face, one candlestick corner was 0.44 mm out, and one tape-dispenser body was built 1000× too large in plan.

**Phase 3 spend:** about $2.75 of the $20 standing budget.

## Next (owner's calls)

- **Any further harness work needs a fresh held-out set** to be claimed; none is left.
- Open-source prep, code containment, the Sonnet arm, and the fresh-context repairer are below; all wait on the owner.

## Also open

- **Code containment** (raised 2026-11-18): agent code runs in Blender as the logged-in user with no boundary. Recommended a low-privilege account for the harness Blender plus an audit hook refusing writes outside the run folder, process launches and network; applies to the Haiku runs too, and is a prerequisite for any local-model arm.
- **Local models on the 4090** (asked 2026-11-18): about a day of work (an OpenAI-style client shim, local token counting); compare within the model only, since tokenizers differ. Breaks the Anthropic-only rule, so it needs an explicit owner decision; recommended after the held-out result.
- **Stronger model:** Sonnet 5.5 at low effort with its own no-MCP baseline, about $7–10.

## Using the rig

- Free: `python tests/harness_selftest.py` (15 checks against a live Blender), `python -m rig.opening_read` (the read and its token count on every scripted starting scene), `python tests/read_stress.py` (the read over recorded final scenes), `python -m rig.replay <runs folder> --version "harness h7"`.
- h6's development runs are in `runs/_matrix-h6/`, h5's in `runs/_matrix-h5/`. h7's are in `runs/` with the baselines.
- `runs/_mining/compare_pilot.py` compares revision runs between versions (inspection calls, tokens, errors); git-ignored with the runs, like `extract.py`.

## Lessons from this session

- **Check a detector on agent-built geometry, not only on the scenes it was written for.** The 15 starting scenes all read correctly early; 400 recorded final scenes exposed seven real defects (a rounded box read as a circle, rib corners as lathe rings, a boolean splitting one ring 0.01 mm apart, a rectangle's corners fitting a "circle", gentle polylines absorbed as arcs, triangulated faces chaining features together, chord points defeating an arc fit).
- **Don't pay to tell the agent what it already assumes.** A prompt sentence explaining that names carry over cost 36 tokens per request; agents already assumed it, which is what caused the NameErrors. The code change alone captured the gain.
- **The mining's ceiling was close to what landed.** It predicted the read could remove most of 210 inspection calls; the pilot made 1 where h6 made 43. Measuring where tokens go before building paid off again.
