# Journal

Dated record of the work: what was done, what was decided and why, and what was measured. Newest at the bottom. This is the raw material for the case study. Phases 0–2 (2026-11-16 to 2026-11-17) are in `docs/journal-phases-0-2.md`; Phase 3 from harness v1 through h6 and the third held-out set is in `docs/journal-phase-3-h1-h6.md`.

## 2026-11-18 · Phase 3: h7 built, all free checks passed

**Done.** The four opening-read additions the mining called for, each built and checked on its own before the next, plus the namespace fixes. All generic: each is computed the same way for any mesh, and none references a task.

- **Revolved profile.** For a part revolved about X, Y or Z (axis detected from rings of evenly spaced vertices; at least 70% of vertices on rings), the outline in order as (r, axial) points, the form the lathe helper takes, with flat caps closed, straight runs collapsed, true arcs written as "arc r R to (point)", and any vertices off the revolved shape located (the pen's clip). Replaces the two unpaired lists (Z levels, radii about the box centre).
- **Round holes and posts.** Every flat circular loop of sharp edges, paired into a wall when two share an axis and radius, grouped when they repeat, with (±a, ±b) when mirror-symmetric. Holes on tilted axes are summarised in one entry.
- **Repeated features.** Every cluster of sharp edges that isn't a round loop or the part's own outline is a feature; flat loops stacked on one footprint (a recess's opening and floor) are joined; features matching edge to edge after a shift, or a turn about an axis through the part's centre, form a pattern: count, pitch or angle step, start, one instance's extent, and grids as rows × columns. Ribs report their reach along their centre line (13.5 mm), not the corner distance (13.54 mm) that the mining found misleading.
- **Flat outlines.** Each flat sharp loop spanning at least half the part: its extent and corner radii, inner (cavity) loops marked, identical levels grouped.
- **Namespace.** Names now carry over between clean calls; a failed call drops its own names and every Blender reference (the reload invalidates them); bpy, math, bmesh and the helpers are restored every call; `Mesh.faces` reads `polygons`.

**Measured (free).** On the 15 starting scenes (development and all three held-out sets) the read goes from 1,990 to 2,969 tokens in total, about 65 tokens more per scene, against the 1–2k tokens each inspection call it should replace. On 400 agent-built final scenes from past runs: no errors, slowest read 2.1 s (once per task). Replaying all 114 recorded h6 development runs through h7: 99 of 99 passes held, no verdict changed, and three runs got shorter (two pen runs went from 3 calls to 2 because the agent's `me` variable now survives the previous call: the exact NameError the mining counted). Self-test: 15 of 15, including four new h7 checks.

**Decided.** A one-sentence system-prompt note telling the agent that names carry over was written and then dropped: it cost 36 tokens on every request of every task, and agents already assume persistence (that assumption is what produced the 29 NameErrors), so the code change alone captures the gain. Several detector defects were caught on real geometry before any paid run and fixed: a rounded box read as a circle, rib corners read as lathe rings, a boolean leaving one ring 0.01 mm off its radius and splitting it, a rectangle's corners fitting a "circle", gentle polylines absorbed as huge arcs, and a triangulated face chaining every port to the part's outline.

**Not done.** The paid revision-only pilot (8 development revisions × 3, about $0.05) waits for the owner's go. Tools added: `python -m rig.opening_read` prints the read on every scripted starting scene with token counts; `python tests/read_stress.py` runs it over recorded final scenes.

**Spend.** None this session.

## 2026-11-18 · Phase 3: h7 revision pilot

**Done.** Owner's go. The 8 development revisions × 3 on h7, against h6's recorded runs on the same tasks (h6's 90 development runs moved to `runs/_matrix-h6/` first). 0 voids, $0.024. Comparison: `python runs/_mining/compare_pilot.py`.

**Measured.**

| | h6 | h7 |
|---|---|---|
| Pass | 19/24 | 21/24 |
| Tokens per pass | 21,908 | 5,174 |
| Inspection calls before the first edit, per run | 1.79 | 0.04 |
| Calls per run | 3.21 | 1.17 |
| Calls that raised, per run | 0.71 | 0 |

Per task, tokens per run fell on 7 of 8 (r02, which the read barely changes, is flat at about 4.8k). The biggest drops are where the mining said inspection was heaviest: r04 holes 58.3k → 3.7k (6.3 inspection calls per run → 0), r03 outline 31.5k → 5.9k (2.0 → 0), r07 ribs 18.9k → 6.5k (2.7 → 0.3). One inspection call in 24 runs, where h6 made 43.

**Failures** are modelling mistakes, all on one-call runs: r02 plaque placed on the wrong face and the part extended below z 0; r03 fillet volume 1.2% short; r04 old holes filled 0.5 mm short of the top. h6 failed r02 and r04 too (1/3 on r04).

**Not a claim.** 24 runs on development tasks the read was checked against. The reduction is far outside the ~15% noise floor, but the claim waits for the full development matrix (builds included, since the namespace change touches them) and a fresh fourth held-out set.

## 2026-11-18 · Phase 3: h7 development matrix

**Done.** Owner's go. The development suite 30 × 3 on h7: 66 new runs plus the pilot's 24 revision runs (same prompt and version, so the batch runner counted them). 0 voids; the whole suite's runs cost $0.135. `python -m rig.compare --setups no-mcp harness --version harness=h7 --groups`.

**Measured.**

| | No MCP | h6 | h7 |
|---|---|---|---|
| Pass | 80/90 | 81/90 | 86/90 |
| Tokens per pass | 26,727 | 9,912 | 6,489 |
| Ratio to no MCP | 1.00 | 0.37 | 0.24 |
| Geometric-mean ratio | 1.00 | 0.35 | 0.29 |
| Wall seconds per run | 31.8 | | 12.3 |

By group, h6 → h7 (pass, tokens per pass): revisions 19/24 21,908 → 21/24 5,174; hard-surface 22/24 5,816 → 24/24 6,858; layouts 15/15 3,113 → 15/15 3,371; multi-part 11/12 11,088 → 11/12 7,697; product 14/15 6,426 → 15/15 9,969. Builds together (the read says nothing on an empty scene; only the namespace change reaches them): 62 → 65 passes, about 6.2k → 6.9k tokens per pass, +11%, inside the ~15% noise floor and driven by two long repair runs (a soap bar at 61k over 6 calls, a housing at 38k over 5) with no failed calls in either; the other build runs match h6 closely.

**What it means.** The whole gain is revisions, as the mining predicted: they went from the costliest group (2–4× any other on h6) to the same cost as a build. Inspection before the first edit fell from 1.79 calls per revision run to 0.04. h7 is the first version under a quarter of the baseline on development, at the best pass rate measured on this suite.

**Next.** Freeze h7 and write a fourth held-out set (same process as heldout3: four authors, then two independent builders from the prompt alone), run once with no MCP alongside, for the claim.

## 2026-11-18 · Phase 3: h7 frozen, and the fourth held-out set

**h7 frozen.** The harness code has not changed since h7 was built; the tree was clean when this work began. No harness edits until the fourth held-out set has run. The only rig change is adding `heldout4` to the suite lists of the batch runner, the comparer, the opening-read check and replay.

**A fourth held-out set (`heldout4/`, w01–w08), written after h7 was frozen,** at development difficulty, with the same group mix and the same process as heldout3. Four authoring agents worked in parallel from the authoring guide and the product brief. They were told not to open the harness code, the journal or the case study, so the tasks couldn't be shaped to flatter or defeat the opening read. The revision author was asked for natural client edits that need the existing model read, written from the product.

- Hard-surface: w01 a shower head (revolved puck with a filleted top edge, chamfered neck, blind bore, two polar rings of nozzles); w02 a screwdriver stand (rounded block, chamfered top edge, five holes tilted 20° with flat bottoms square to their axes); w03 a candlestick (rounded-square foot with a chamfer running round its corners, lofted to a round stem, socket and felt recess).
- Layout: w04 a coaster set (open holder with a thumb notch, two coasters stacked inside it at 0.5 mm clearances, two more beside it, one turned 45°).
- Revisions: w05 a brush holder going from four holes to six on the same circle, with the old holes filled flush; w06 a turned bud vase with its shoulder lowered 20 mm at the same diameter.
- Multi-step: w07 a tape dispenser (body with a cradle and blade slot, tape roll, flanged hub, serrated blade); w08 a moka pot (tapering octagonal boiler with a valve boss, hex valve, jug with a cavity and handle, chamfered lid with a filleted knob).

Every task is proven by `rig.verify_checks`, including a 24-segment variant that must pass: 85 variants, all OK, re-run independently after the authors finished. Then two independent builders made every task from its prompt alone, 16 builds in all. Builder A wrote bmesh by hand with 32-segment circles turned half a step off the axes and no modifiers. Builder B used primitives with Bevel, Boolean and Solidify modifiers at 48–64 segments. All 16 passed: 11 first time, 5 after the builder fixed a mistake of its own (a misread hole size, a hex turned the wrong way, coincident boolean faces). None was a task defect, unlike heldout3, where the builders caught one.

**Worth knowing before reading the results.**

- On w05, filling the old holes with plugs flush to the top face makes Blender's exact boolean leave doubled rim vertices; unless the agent merges after each plug, later cuts break the mesh. The author and builder B both hit this. It's a real trap on the most natural edit, not a defect, but expect it to cost runs.
- The tightest margins are w07's 36 mm tape and cradle (0.4 mm tolerance; a half-turned 24-segment circle sits about 0.31 mm in) and w01's side probes (0.27 mm of 0.3 for a half-turned 24-segment build).
- Opening read on the two new starting scenes: no crash, sensible output, 254 and 212 tokens. No harness change made in response.

**Next.** Run it once, with the owner's go: 8 tasks × 3 on no MCP and h7, about $0.30–0.50. That spends `heldout4/`.

## 2026-11-18 · Phase 3: fourth held-out set, run once on h7

**Done.** Owner's go. 8 tasks × 3 on no MCP and the frozen h7, 48 runs, 0 voids, $0.19 (no MCP $0.129, h7 $0.061). `python -m rig.compare --suite heldout4 --setups no-mcp harness --version harness=h7`. This spends `heldout4/`.

| | No MCP | h7 | Ratio |
|---|---|---|---|
| Pass | 18/24 (75%) | 20/24 (83%) | |
| Tokens per passed task (headline) | 58,147 | 11,934 | **0.21** |
| Geometric mean tokens per task | 27,772 | 7,552 | **0.27** |
| Without w05: tokens per pass | 33,774 | 10,755 | 0.32 |
| Without w05: geometric mean | 21,856 | 7,323 | 0.34 |
| Model turns per run | 4.0 | 1.5 | |
| Wall time per run | 40.3 s | 20.4 s | 0.51 |

By group (pass, tokens per pass), no MCP → h7: hard-surface 6/9 35,070 → 8/9 7,974; layout 3/3 12,728 → 3/3 5,409; revisions 5/6 122,762 → 4/6 11,784; multi-step 3/6 61,413 → 5/6 22,307.

**No task defeated both setups,** so nothing is excluded under the z05 rule. The column without w05 is a sensitivity check, not the claim: w05 (four holes to six) is no MCP's runaway task here, 90k–291k tokens a run over 5–14 calls, 36% of its total. h7 passed it once at 4k–21k. Even without it, h7 uses about a third of no MCP's tokens. On the earlier hard held-out sets, after the same kind of exclusion, h4 and h6 used 0.66 and 0.63 overall and 0.42 and 0.43 on the typical task.

**h7's four failures are genuine.**
- Two w05 runs lost the 4 mm round on the top edge while refilling the top face around the new holes. The probes read 0.4–0.7 mm off on the round; the holes themselves were right.
- One w03 foot corner was 0.44 mm out.
- One w07 body was built 1000× too large in plan, a millimetre-to-metre slip on two axes.

No MCP failed all three w07 runs (parts misplaced or the wrong size, one unit slip), plus one run each on w01, w03 and w05.

**What it means.** The development result holds on unseen tasks. h7 is about a fifth of no MCP's tokens per passed task (0.21) and about a quarter on the typical task (0.27). Its pass rate is at least as good (83% against 75%; with 24 runs that gap is inside the noise), and its runs take half the wall time. On the hard held-out sets the overall ratio has gone from 0.66 (h4) and 0.63 (h6, without z05) to 0.21, or 0.32 even with no MCP's costliest task removed. The revision gain carries over: on w06 (lower the vase's shoulder) h7 read the profile and moved it in one call at 3–7k tokens, where no MCP spent about 36k over four calls every time. The one place h7 lost accuracy is w05 (1/3 against 2/3), where the edit forces the top face to be rebuilt and the round goes with it.

**Spend.** This session $0.19; Phase 3 about $2.75 of the $20 standing budget.

**Housekeeping.** Phase 3's entries from harness v1 through h6 moved to `docs/journal-phase-3-h1-h6.md` to keep this file small.

## 2026-11-18 · Open-source preparation

**Decided (owner).** The repository is GPL-3.0-or-later throughout, following Blender's licence, since the Blender-side code uses its Python API. Nothing personal and nothing about why the project exists outside its own goals goes in the repository; the case study keeps its results and drops the personal section. An independent review (Fable) checked every tracked file and the full history: the files were then cleaned of the rest it found, and because the old history held personal context in nearly every commit, the public repository starts from one clean commit at h7. The full history is kept privately.

**Done.**
- **README rewritten results-first:** headline numbers, a tokens-per-pass chart across all six setups, a gallery of h7's passing models on the fourth held-out set, the method, setup and commands. Both figures are rebuilt by `python -m rig.figures chart|gallery`.
- **Packaging and tests:** `pyproject.toml` (`pip install -e .[dev]`), and 858 unit tests (3 expected failures for known gaps) that need no Blender and no network (about 4 s): every task file across all suites, the comparison arithmetic, cost accounting, the batch runner's task matching, the `.env` loader. CI runs them on Linux and Windows.
- **The tests found real defects.** Two heldout2 tasks carried short ids (`y07`, `y08`) instead of their folder names; fixed (runs are matched by folder name and prompt fingerprint, and the heldout2 comparison reproduces exactly). Three development or spent shape checks have no variant that fails them (`m01` probe_tail, `p04` probe_body, `z08` volume_motor); they're recorded as known gaps in the tests, not changed, since the tasks are spent or their results already published.
- **Run records for the release:** 1,629 runs (every matrix, every held-out set, the pilot, the prompt test and the thinking arms; one void excluded), with result, transcript and per-call records, 24.5 MB zipped. Local paths were replaced with placeholders, and a second scan found no keys or personal data. Every headline figure recomputes from it exactly. The final .blend scenes are left out: each embeds a local home path.

**Spend.** None.

**Published.** The repository went public on 2026-11-18 with the h7 release and its run records.

## 2026-11-19 · Sonnet 5.5 arm, round one

**Why.** To test whether h7's advantage is a property of the harness or only compensation for Haiku's mistakes: a stronger model should repair less on its own, so its no-MCP baseline should be leaner.

**Priced first.** Repricing all 180 scored Haiku development runs (no MCP and h7, 90 each) at Sonnet 5.5 rates gave about $9.60 for the full arm (30 × 3 per setup): $6.90 no MCP, $2.70 h7, with output (mostly thinking) about 75–80% of the cost. The owner approved one round (30 × 1 per setup) first, to measure Sonnet's own token profile before committing the rest.

**Fixed.** Cost accounting priced cache reads at 0.1× input for every model. Sonnet 5.5 and Opus 5.5 cache reads are 0.05× ($0.10 and $0.20 per million), so prices now carry a per-model cache-read rate. Haiku's costs are unchanged.

**Measured (round one, Sonnet 5.5 low, development, one run per task).** `python -m rig.compare --setups no-mcp harness --version harness=h7 --model claude-sonnet-5-5 --groups`. No voids.

| | No MCP | h7 | Ratio |
|---|---|---|---|
| Pass | 25/30 (83%) | 28/30 (93%) | |
| Tokens per passed task | 10,512 | 3,577 | 0.34 |
| Geometric mean tokens per task | 7,386 | 3,089 | 0.42 |
| Model turns per run | 2.9 | 1.2 | |
| Wall time per run | 21.1 s | 7.9 s | 0.37 |
| Cost | $0.864 | $0.389 | |

For comparison, Haiku 5.5 low on the same suite (90 runs each): no MCP 26,727 tokens per pass, h7 6,489 (0.24); geometric mean ratio 0.29.

**What it means so far.** Sonnet is leaner on its own: its no-MCP baseline uses about 40% of Haiku's tokens per pass, and it barely thinks at low effort. h7 still cuts tokens by about two thirds and wall time by about the same, with the pass rate at least as good, so the advantage holds on the stronger model, though it is smaller than on Haiku (0.34 against 0.24 per pass). On cost, Haiku plus h7 remains far cheaper: about $0.0016 per passed task against $0.014 for Sonnet plus h7. One round is 30 runs per setup, so these are directional.

**Spend.** $1.25 for the round, against $3.20 estimated. Phase 3 about $4.00 of $20. Rounds two and three re-quote at about $2.50.

## 2026-11-19 · Sonnet 5.5 arm complete

**Done.** Rounds two and three (owner's go, re-quoted at about $2.50), completing 30 × 3 per setup. No voids. `python -m rig.compare --setups no-mcp harness --version harness=h7 --model claude-sonnet-5-5 --groups`.

| Sonnet 5.5 low, development | No MCP | h7 | Ratio |
|---|---|---|---|
| Pass | 79/90 (88%) | 82/90 (91%) | |
| Tokens per passed task | 10,103 | 3,828 | 0.38 |
| Geometric mean tokens per task | 7,504 | 3,107 | 0.41 |
| Model turns per run | 2.8 | 1.2 | |
| Wall time per run | 20.8 s | 7.7 s | 0.37 |
| Cost per passed task | $0.034 | $0.015 | |

By group (pass, tokens per pass), no MCP → h7: hard-surface 20/24 10,822 → 20/24 3,858; layout 14/15 5,096 → 15/15 2,440; multi-step 11/12 11,470 → 12/12 4,729; product 14/15 8,347 → 12/15 5,034; revisions 20/24 13,367 → 23/24 3,609.

**What it means.** The harness advantage holds on the stronger model but narrows: 0.38 per pass and 0.41 typical, against Haiku's 0.24 and 0.29. Sonnet repairs less on its own, so there is less waste for the harness to remove. Revisions still gain the most (3.7× fewer tokens), as on Haiku. Sonnet with h7 is the fastest setup measured (7.7 s a run against Haiku with h7 at 12.3 s), but Haiku with h7 stays about nine times cheaper per passed task ($0.0016 against $0.015).

**h7's eight Sonnet failures are all one-call runs**: the agent built once, the call came back clean, and the run ended. p04 (gable carton) failed all three and h02 (lipstick) two. Haiku with h7 passed both every time, so a stronger model trusting a clean report and stopping early is worth reading before any Sonnet claim; no held-out set has been run for Sonnet.

**Spend.** Rounds two and three $2.59; the arm $3.85 against $9.60 first estimated. Phase 3 about $6.60 of $20.

**Proposed, not decided.** Cross-family models through OpenRouter to map where the harness stops paying. It would reverse the Anthropic-only rule, needs an adapter for the OpenAI-style tool interface (about a day), and I recommended code containment first. Waiting on the owner.

## 2026-11-19 · Reading h7's eight Sonnet failures

**Done.** Read the code, scene report and failed checks for all eight Sonnet 5.5 + h7 failures on development, and compared Haiku 5.5 + h7 on the same tasks. No runs, no spend.

**The earlier framing was wrong.** The entry above read the failures as a stronger model trusting a clean report and stopping early. Haiku with h7 also finishes p04, h02 and h07 in one call every time and passes. Both models stop after one clean call; Sonnet simply makes more geometry slips, and the scene report only checks that the mesh is valid, so neither model gets any feedback on shape.

**What each failure was.** Every scene report said "no problems found", and every mesh was valid; the shape was wrong.

- p04 gable carton, 3/3: the extruded side profile meets the 2 mm fin at y = ±1 mm with the roof at z = 230 (twice) or 231 (once, reasoned out as "230 + 1"). The roof falls 1 mm per mm, so it should be 229 there; Haiku wrote 229. An arithmetic slip of about 1 mm that only a probe catches.
- h02 lipstick, 2/3: the angled tip was cut with a rotated box, rotated the wrong way, so the slant runs backwards and the bullet tops out at 62 mm. Sonnet's own text said the top should be 72.91 mm. Haiku built the slanted top directly as vertices and avoided the rotation.
- h07 wide-mouth jar, 1/3: neither lathe profile reaches the axis, so the jar has no floor and the lid no top: both are watertight rings. Volumes 19% and 49% short.
- h08 soap bar, 1/3: the recess cutter was rounded with Blender's low-level bevel call without a profile setting. In Blender 5.2 that default makes a square inward notch, not a round, so the recess corners came out sharp. Confirmed in Blender: the bevelled corner points lie on a square, not an arc.
- r03 soften edge, 1/3: volume 0.50% short against a 0.5% tolerance, from a coarse fillet. Borderline faceting; Haiku fails r03 at the same rate.

**What the check catches that the report doesn't.** Dimensions and shape. The report is generic validation (watertight, normals, hygiene, unchanged booleans) and says nothing about size or form. Two generic additions would have caught three of the eight: reporting each object's bounding box (h02 twice: 62 mm against the 72.91 mm the model itself stated), and a warning when a lathe profile never touches the axis, which makes a ring rather than a solid (h07). p04 and r03 are not catchable generically; h08 needs either a note on the bevel default or a helper that rounds chosen edges.

**Proposed, not decided.** An h8 that adds the bounding box and the open-lathe warning to the report. It costs a few tokens per object on every run, so it has to be measured on Haiku as well as Sonnet: one development round each on the harness setup, about $0.45. Waiting on the owner.

## 2026-11-19 · h8: shape feedback before a clean finish, one round each

**Built** (local branch, not merged). The scene report already lists every object's bounding box, but a clean done=true call ends the run before the agent reads it, so a bounding-box report alone could not have caught anything. h8 added two things instead. First, a helper that takes the extents the agent expects and warns on a mismatch; a warning holds the run open once, as a missed boolean does. Second, a warning when a lathe profile never touches the axis. The batch runner now counts only runs at the setup's current version, so a new harness version doesn't skip cells the old one filled. Unit tests and the live self-test pass.

**Measured** (owner's go; development, harness only, one run per task, no voids). `python -m rig.compare --setups harness --version harness=h8 --model <model>`.

| | Haiku h7 (90) | Haiku h8 (30) | Sonnet h7 (90) | Sonnet h8 (30) |
|---|---|---|---|---|
| Pass | 86/90 (96%) | 30/30 | 82/90 (91%) | 27/30 (90%) |
| Tokens per passed task | 6,489 | 6,888 | 3,828 | 5,831 |
| Geometric mean tokens per task | 4,855 | 5,729 | 3,107 | 3,635 |
| Wall time per run | 12.3 s | 14.2 s | 7.7 s | 9.7 s |

**What happened.** The lathe warning fired only on parts that are meant to be rings: a bezel, a lid, a collar, a dip tube and a liner, on both models. Each one cost an extra call, and on Sonnet's spray bottle (p03) the run took 7 calls and 51k tokens, which alone moves Sonnet's tokens per pass by about half. It never fired on a real mistake. The extents helper fired once, on a Haiku soap bar built 1,000 times too large, which the run then fixed. Sonnet called it in only 15 of 30 runs. The four tasks Sonnet failed under h7 (p04, h02, h07, h08) all passed this round, but Sonnet's new failures (m03, r04, r07) came in runs that never called the helper. One round of 30 cannot show a change of two or three passes in 90.

**Decided (recommended to the owner).** Don't adopt h8: it costs 18% more tokens typical on both models, and the gain it was built for is too small to see. The lathe warning is wrong as a rule, because legitimate ring parts are common. An expects-only variant would be cheaper, but at best it catches two of Sonnet's eight h7 failures, so it is not worth another round. h7 stays the harness.

**Spend.** $0.56 (Haiku $0.05, Sonnet $0.50) against $0.45 estimated. Phase 3 about $7.15 of $20.
