# Journal: Phase 3, h1 to h6

Phase 3 entries from 2026-11-17 to 2026-11-18, harness v1 through h6 and the first three held-out sets. Moved out of `docs/journal.md` to keep it small; newer entries continue there.

## 2026-11-17 · Phase 3: harness v1 meets the target on the development suite

**What was built.** A new setup, `harness`, beside no-MCP and run through the same rig, ledger and checks. It has one tool on a Blender session that stays open for the whole run. Each piece answers a line of the Phase 2 breakdown:

- **A scene report after every call:** face count and bounding box per mesh object, plus generic problems (non-manifold edges, separate pieces, self-intersections, bad normals, coincident vertices, zero-length edges, unapplied transforms, parts touching, intersecting or inside each other). It replaces the inspection code agents wrote and printed. It reuses the generic check functions and never sees a task's checks or expected values.
- **The scene read once up front,** with Z and radial levels, so a revision doesn't spend a turn reading the model. All 24 no-MCP revision runs had spent their first call reading.
- **Auto-finish (owner's go, this session):** a call marked done=true ends the run if it raises nothing and the report shows no problems. Per-turn analysis of the baseline showed most runs take two model calls, and the second, which only says "done", resends everything: 36% of all no-MCP tokens.
- **Generic helpers** (cylinder, box, lathe, exact boolean, bevel, finish/cleanup, a mm constant), to cut the code written per task.
- **A persistent Blender:** up in 1.2 s, about 0.1 s per call against 1.7 s to launch per call in the baseline. A failed call reloads the last saved scene, so each call is still one atomic step.

**Iterations, all on the full 30 tasks × 3:**

| Version | Pass | Tokens per pass | What changed |
|---|---|---|---|
| h1 pilot (5 runs) | 5/5 | 2.6k–7.3k | One call hung for 180 s: `finish()` read a stale transform, so 24 rotated ribs landed on top of each other and the booleans multiplied faces. A harness bug; fixed. |
| h2 | 72/90 (80%) | 10,543 | Below the 82% floor. 10 of 18 failures were built 1,000× too large: the report gave millimetres and agents read them as metres. A design fault in the report. |
| h3 | 75/90 (83%) | 9,759 | Report in metres. Revisions recovered (22/24). 12 of 15 failures were still 1,000× builds, now on models built from scratch: agents wrote mm figures as metres and finished in one call, never seeing the bounding box. The baseline makes this mistake in 2 of 90 runs. |
| h4 | **82/90 (91%)** | **9,773** | A `mm = 0.001` constant and one prompt line ("write 30 mm as 30 * mm"). |

**h4 against the no-MCP baseline:**

| | No MCP | Harness h4 | Ratio |
|---|---|---|---|
| Pass rate | 80/90 (88.9%) | 82/90 (91.1%) | tie |
| Tokens per passed task | 26,727 | 9,773 | 0.37 |
| Geometric mean tokens per task | 16,900 | 5,721 | 0.34 |
| Turns per run | 3.2 | 1.7 | |
| Wall time per run | 31.8 s | 15.0 s | 0.47 |
| Cost, 90 runs | $0.349 | $0.165 | 0.47 |

The target was at most half the tokens (about 13,400) at 82% or better. h4 is at 37% of the tokens and 91%, well outside the ±16% noise band in `docs/eval-method.md`. By group: hard-surface 21/24 at 6.6k, layout 15/15 at 2.8k, multi-step 12/12 at 9.8k, p-tasks 12/15 at 7.9k, revisions 22/24 at 18.6k (no-MCP: 37.0k). 83 of 90 runs ended by auto-finish.

**What's left in the failures.** Three are the soap bar built 1,000× too large, on every repeat: the agent writes the rounded profile in raw mm numbers despite the prompt line. The other five are shape misses (pump actuator, carton roof, the liner's wall, a fillet's volume), the same kind the baseline makes.

**Not counted toward the result.** The h1 to h3 runs are kept under `runs/_pilot-h1`, `runs/_matrix-h2` and `runs/_matrix-h3`, outside what the batch runner and comparison read. Changing versions mid-matrix would otherwise mix them in, because the batch runner matches runs by prompt, not by setup version.

**Tooling.** `python -m rig.compare --setups no-mcp harness --version harness=h4 --groups` computes the eval-method comparison. It reproduces the Phase 2 baseline numbers exactly.

**Spend.** Phase 3 so far: $0.48 over 275 runs, against the $20 standing budget.

**Not done yet:** the held-out confirmation (8 tasks, run once for the final claim; needs the owner's go and a small change so the batch runner can read `heldout/`), and the separate thinking arm (dropping replayed thinking is allowed by the API, but anyone could switch it on, so per the ground rules it is measured on the baseline too, not folded into the harness headline).

## 2026-11-17 · Phase 3: held-out confirmation, run once

The 8 held-out tasks, 3 repeats each, on no MCP and on the harness frozen at h4: 48 runs, 0 voids, $0.23. This spends the held-out set. Nothing in the harness changes because of it.

| | No MCP | Harness h4 | Ratio |
|---|---|---|---|
| Pass rate | 19/24 (79%) | 20/24 (83%) | tie |
| Tokens per passed task (headline) | 57,864 | 37,958 | **0.66** |
| Geometric mean tokens per task | 29,640 | 12,483 | **0.42** |
| Turns per run | 4.6 | 3.2 | |
| Wall time per run | 46.9 s | 28.8 s | 0.61 |
| Cost, 24 runs | $0.144 | $0.090 | 0.63 |

**The two measures disagree, and the reason is the tail.** On the typical task the harness holds at well under half (geometric-mean ratio 0.42; 15 of its 24 runs finished in one call at 4–9k tokens). The headline, total tokens over passes, is dominated by a few long runs. Two harness runs alone hold 380k of its 759k tokens: the wider-neck revision (178k, 13 turns, passed) and a desk lamp (202k, 14 turns, failed). The baseline has its own tail (286k on the remote button, 198k on the ice tray), but the harness's tail is what kept the headline at 0.66 instead of under 0.5.

**Why the harness runs long.** Both long runs are repair loops on a problem the scene report keeps flagging. On the bottle the agent chased non-manifold edges and zero-area faces through 13 calls; on the lamp, an arm intersecting the post through 14. Auto-finish refuses a call while the report shows a problem, so an agent that can't fix it keeps going, and each turn resends the growing context. The baseline agent in that spot usually stops and says done (and often fails). The report's gate makes runs more correct and, occasionally, much longer.

**Against the ground rules.** The pass-rate floor holds (83%). On the headline metric, half of no MCP's tokens per pass was the target and the held-out result is 66%: not met. On the eval method's comparison measure (the geometric-mean ratio) it is met at 0.42. With 24 runs a side and this tail, either number would move a lot with one run either way; the development suite (90 a side) is the steadier estimate.

**Diagnosis only, not tuning.** The obvious fix is a turn or token cap on repair loops, or reporting persistent problems without blocking the finish. Any such change is measured on the development suite, and a fresh held-out set would be needed to confirm it.

## 2026-11-18 · Phase 3: h5, fixing why repair loops get stuck

**Sizing the tail first (free, from the recorded h4 runs).** On the development suite, the 9 runs of 4+ calls hold 47% of h4's tokens; on held-out, 6 runs hold 83%. Resent history is 32% of development tokens and 60% of held-out ones; replayed thinking alone is 13% and 34%. A rule that lets a run finish once the same problems repeat for 3 calls would have saved 8% on development but 60% on held-out: the development suite has few stuck loops, so a loop fix can't be proven there beyond the 15–19% noise floor. The development matrix can only show it does no harm; a fresh held-out set has to carry the claim.

**Why agents got stuck: two causes, both partly the harness's own.**

- **Cleanup and report disagreed.** The report flags faces under 1e-10 m²; `finish()` only dissolved geometry under 1e-7 m in length, so boolean slivers survived it. The report gave a count with no location or threshold, and agents went looking with a tolerance about 100× tighter than the report's, found nothing, and repeated. The bottle (13 calls), ribbed cap (7) and remote (6) each escaped only when the agent loosened its own tolerance or rebuilt.
- **Mirrored cutters cut nothing.** To lay a cylinder on its side the agent swapped two coordinates, which mirrors the mesh and turns it inside out; the exact boolean with an inside-out cutter silently didn't cut the lamp's cross hole (the post's volume matched a solid cylinder exactly). The report said, truthfully, that arm and post intersect; the agent checked the hole's vertices, found them where they should be, and decided the check was a false positive. It wasn't: 331 genuine face crossings. The lamp run that passed escaped at call 7 by flipping one sign, which made the mirror a rotation.

**h5, all generic (no task knowledge):** cleanup widens its tolerance (0.1 µm → 1 µm → 10 µm) only while faces under the report's threshold remain; non-manifold edges, coincident vertices, zero-length edges, zero-area faces and part-pair intersections carry the box where they are (separate pieces, self-intersections, normals, inside and touch do not); `boolean()` makes both operands' normals outward first and warns when a boolean leaves the volume unchanged; a done=true call may finish once the same problems have been reported for 3 calls in a row (the agent is told when that happens); every run ends at 8 calls and is checked as it stands.

**Replay before spend (free; `python -m rig.replay`, output in `runs/_replay-h5/`).** All 114 recorded h4 runs replayed through h5 with their recorded code, then re-checked: no pass lost to the fixes, two pump-dispenser fails became passes, the five stuck runs all pass at call 1–3 instead of 6–14. One pass is lost to the 8-call cap (a 9-call rib revision), as predicted.

**Development matrix, 30 × 3:**

| | No MCP | h4 | h5 |
|---|---|---|---|
| Pass | 80/90 (89%) | 82/90 (91%) | 79/90 (88%) |
| Tokens per pass | 26,727 | 9,773 (0.37) | 8,202 (0.31) |
| Geometric-mean ratio | 1.00 | 0.34 | 0.32 |
| Model turns per run | 3.2 | 1.7 | 1.5 |
| Cost, 90 runs | $0.349 | $0.165 | $0.152 |

The early finish and the call cap never fired; the "unchanged over the last 3 calls" notice was shown three times, in two runs (one soap bar, one move-holes revision that went on to pass). All 11 failures ended on a clean finish with a wrong model: the soap bar built 1,000× too large (as on every h4 run), a part given the wrong name twice ("Shaft" for "Crank", "Head" for "Actuator"; generic validation can't know expected names), and shape misses of the kind the baseline makes. Three passes fewer than h4 is within one standard error; the 16% token drop sits at the noise floor, as the tail sizing predicted.

**A fresh held-out set,** `heldout2/` (y01–y08): the same group mix as the spent set (3 hard-surface, 1 layout, 2 revisions, 2 multi-step), written by four parallel agents, every task proven by `rig.verify_checks` and re-verified independently. Written after h5's design was settled; not used for any tuning.

**Decisions (owner):** a second agent (a fresh-context repairer, or a reviewer for shape misses) is deferred until this checkpoint: the repairer's case was long loops, which h5 attacks at the source, and a reviewer adds tokens to every run for an accuracy gain, when accuracy is the guardrail, not the target. Claim h5 now as the first checkpoint; later versions get their own fresh held-out set.

**Fresh held-out (`heldout2/`), run once:** 8 tasks × 3 on no MCP and h5, 48 runs, 0 voids, about $0.08. This spends `heldout2/`.

| | No MCP | Harness h5 | Ratio |
|---|---|---|---|
| Pass rate | 22/24 (92%) | 24/24 (100%) | tie or better |
| Tokens per passed task (headline) | 15,392 | 3,451 | **0.22** |
| Geometric mean tokens per task | 11,986 | 3,246 | **0.27** |
| Model turns per run | 2.8 | 1.0 | |
| Wall time per run | 22.4 s | 7.5 s | 0.33 |
| Cost, 24 runs | $0.062 | $0.020 | 0.32 |

The target (half of no MCP's tokens per pass at 82% or better) is met on both measures, by a wide margin. Every h5 run finished in one tool call (one also spent a second, text-only turn); neither the persistence rule nor the call cap fired.

**What this result does and doesn't show.** This set came out easier than the spent one: no MCP needed 15.4k tokens per pass here against 57.9k on the first held-out set and 26.7k on development, and the authoring agents themselves judged several tasks at the easy end of their brief. No run looped, so the persistence rule and cleanup were not exercised. One fix was: on a table clock the agent laid cylinders on their side by swapping coordinates, the mirrored-cutter case; replaying that call against h4's library leaves the face recess uncut (body 372,886 mm³, fails the 1% volume check), against h5's it passes (357,831 mm³). So one of the 24 passes is owed to the normals fix. It confirms the harness's efficiency on unseen tasks of this kind (one call, about a fifth of the tokens); it is not evidence that the loop fixes work on unseen tasks. That evidence is the replay of the spent set's stuck runs, which is diagnostic, not a held-out measurement.

**Independent review (Fable, 2026-11-18).** Reproduced every figure above, found no wrong verdict or void, confirmed h5's code was frozen before `heldout2/` was written and that nothing in h5 references a task. Its corrections are applied above. Its main point stands as a caveat on the claim: `heldout2/` is materially easier than both other suites (baseline geometric-mean tokens per task 9.3k against 16.4k development and 33.5k first held-out on hard-surface; 9.8k against 23.6k and 47.6k on revisions), every shape in it is buildable from the harness's own helpers, and several tasks are close cousins of development tasks. Per-group ratios on it (0.21–0.34) are in line with development (0.28–0.38), so ease doesn't inflate the geometric-mean ratio much; the 0.22 headline is helped by the baseline's two failures. **The public statement pairs both held-out results:** first set (harder, h4) 0.66 headline and 0.42 geometric mean, target missed on the headline because of two repair loops; second set (easier, h5) 0.22 and 0.27, target met.

The review also found h5 code issues that touch no reported number, to be fixed in h6 before the loop handling is relied on for harder tasks: the persistence streak counts calls that raised and inspection-only calls, and strips counts so steady progress (270 → 40 → 6 edges) reads as "unchanged"; `boolean()`'s outward-normals step fills a cavity built as an inner shell (a regression against h4); the volume warning misfires on small holes in big parts and can't be read when a done=true call ends the run; problem keys merge digit-suffixed object names; the 8-call cap and the persistence rule aren't in the system prompt; crashes and timeouts aren't counted toward the cap. Two `heldout2/` probes are stricter than the authoring rules allow for coarse builds (y03's slot end off its widest point; y04's 1% jar volume against a 24-segment cylinder); every actual build passed them.


**Checkpoint accepted (owner, 2026-11-18).** Next session explores from here; the handoff ranks the options.

## 2026-11-18 · Phase 3: thinking arm, part 1 — thinking off

**What and why.** First option from the checkpoint (owner's pick): measure thinking as a separate arm, applied to no MCP and the harness alike (Phase 3 ground rules). The owner chose to see whether accuracy holds with thinking fully off before spending on the second arm (thinking on, earlier turns' reasoning not resent), because nobody had seen this small a model work with no thinking. Haiku 5.5 accepts thinking off at low effort, so it's the setting anyone could flip. The rig gained an arm that changes the request instead of the prompt; same prompt hashes, matched by arm name. Development suite, 30 tasks × 3, both setups: 180 runs, none void, $0.35.

| Setup | Thinking | Pass | Tokens per pass | Geometric mean | Turns | Wall s | Cost $ |
|---|---|---|---|---|---|---|---|
| No MCP | on | 80/90 (89%) | 26,727 | 16,900 | 3.2 | 31.8 | 0.349 |
| No MCP | off | 53/90 (59%) | 36,923 | 14,941 | 4.2 | 23.8 | 0.239 |
| Harness h5 | on | 79/90 (88%) | 8,202 | 5,397 | 1.5 | 13.7 | 0.152 |
| Harness h5 | off | 75/90 (83%) | 10,212 | 5,411 | 2.2 | 9.5 | 0.113 |

**Thinking off loses on the headline for both setups.** It halves output per call, but agents need more calls to get right what they used to reason through, and they pass less often. No MCP collapses: hard-surface 12/24 (was 23/24), parametric 4/15 (was 12/15). The harness holds the accuracy guardrail by one run (83% against 82%) but costs 25% more per pass; the typical task is unchanged (geometric mean 5,411 against 5,397). It is cheaper in dollars and wall time, because output is the expensive token, but the headline is tokens per pass.

**Where it helps and where it hurts.** On the harness, simple work gets cheaper without thinking: layouts 15/15 at 2.6k tokens a run (was 14/15 at 3.7k), and revisions hold at 21/24 with slightly fewer tokens. Multi-part builds double (9.3k → 20k a run): the toothbrush dock failed all three runs, and the coffee grinder took 5–6 calls each time. Thinking pays for itself on the long builds and is waste on the short ones. Picking per task would use task knowledge, so it is not a generic setting; per-call effort chosen by the model isn't available with thinking off.

**Decision.** Thinking stays on at low effort for the headline, on both setups. The harness makes thinking survivable (83% vs no MCP's 59%), which is a point in its favour, but not a token saving. The second arm (thinking on, earlier reasoning cleared server-side) is still worth measuring. It keeps the reasoning that the long builds need and targets replay, 13% of development tokens and 34% of the first held-out's. On the development suite it is likely under the ~15% noise floor, so its result may only be readable on a harder set. Phase 3 spend: about $1.30 of $20.

## 2026-11-18 · Phase 3: thinking arm, part 2 — resend only the latest thinking

**What and why.** Thinking stays on; only the most recent response's reasoning is resent, so replay (13% of development tokens, 34% of the first held-out's) shouldn't pile up across calls. Applied to both setups (ground rules). Development suite, 30 × 3, 180 runs, none void, about $0.57.

**The planned mechanism didn't work.** The API's server-side thinking clearing counts a whole tool loop as one turn and always keeps the turn in progress, so in an agent run it clears nothing (the smoke run cleared 0 tokens on every call; those runs are set aside in `runs/_smoke-clear-thinking-serverside/`). The arm drops earlier responses' thinking client-side instead. Haiku 5.5's history check allows removing a leading run of thinking blocks, oldest first, and no request failed. The ledger counts what was actually resent; unattributed input stayed under 1%. Cost: the prompt cache can't reuse history past the first message once older thinking is dropped.

| Setup | Thinking replay | Pass | Tokens per pass | Tokens per run | Replay share | Turns | Cost $ |
|---|---|---|---|---|---|---|---|
| No MCP | all resent | 80/90 | 26,727 | 23,756 | 27% | 3.2 | 0.349 |
| No MCP | latest only | 80/90 | 23,840 | 21,190 | 14% | 3.4 | 0.403 |
| Harness h5 | all resent | 79/90 | 8,202 | 7,199 | 12% | 1.5 | 0.152 |
| Harness h5 | latest only | 83/90 | 7,903 | 7,288 | 7% | 1.7 | 0.155 |

**Result: inside the noise on both setups.** Replay's share roughly halved, but runs got slightly longer (agents without their earlier reasoning take a few more calls), which gives most of it back. No MCP saves 11% per pass at the same pass rate; the harness saves 4% per pass, all from four more passes; its tokens per run didn't move. Both are under the ~15% floor. Typical-task tokens are unchanged on both. Cost rose 15% on no MCP from lost cache reuse. A partial read at 170 runs showed −18% and −12%; the last runs, mostly revisions, pulled it back, which is the noise the floor warns about.

**Decision.** The headline keeps thinking as-is, on both setups. With part 1, the thinking question is settled for the development suite: turning it off costs more, and trimming its replay is a wash. Its one remaining case is the harder held-out set, where replay was a third of tokens; if the third held-out set is hard enough to produce long runs, this arm can ride along at no extra authoring cost. Phase 3 spend: about $1.90 of $20.

## 2026-11-18 · Phase 3: h6, and the third held-out set

**h6: the review's h5 code issues, fixed (generic, no task knowledge).** The persistence streak now counts only calls that run clean and change the scene (a scene fingerprint tells an edit from an inspection), and any count falling resets it, so 270 → 40 → 6 open edges is progress while 160 → 264 intersecting pairs is not. Problems carry exact keys from the report itself, so digit-suffixed names (Leg1, Leg2) stay apart. Orientation turns every piece outward except a piece that sits inside another without touching it: that is a cavity, and stays one (h5 filled cavities; mirrored cutters are still fixed). The unchanged-volume warning compares against the cutter as well as the target, so a small hole in a big part no longer trips it; a call with a helper warning can't end the run on done=true once, and the agent is told why. Crashes and timeouts count toward the 8-call cap. The cap, the persistence rule and the warning hold are in the system prompt. Boot retries the port file while Blender replaces it, and a failed boot never leaves Blender running. A ten-case self-test proves each fix against a live Blender, free (`tests/harness_selftest.py`).

**Replay before spend (free, 408 recorded runs).** All 294 h5 runs (base and both thinking arms, development and second held-out) replay through h6 with identical verdicts and call counts (261 passes). The 114 h4 runs give 104 passes, as they did through h5, including the one pass the 8-call cap costs (a 9-call rib revision). One run differs: on the first held-out bottle, the agent's union sealed the bottom of the old bore into a closed void; h5 silently filled it before the next boolean, which made the agent's re-drill clean, while h6 keeps the void and the re-drill lands on its faces. Still a pass, 8 calls instead of 2. h6's behaviour stands: silently changing a model's volume is the bug the review flagged. h6 was frozen (committed) before any held-out task was written.

**Development matrix, 30 × 3, harness only** (no MCP's base runs stand; h5's development runs moved to `runs/_matrix-h5/` first, since the batch runner matches runs by prompt and arm, not version). 0 voids, $0.16.

| | No MCP | h5 | h6 |
|---|---|---|---|
| Pass | 80/90 | 79/90 | 81/90 (90%) |
| Tokens per pass | 26,727 | 8,202 (0.31) | 9,912 (0.37) |
| Revisions, tokens per pass | 37,025 | 13,101 | 21,908 |

The 21% rise sits at the noise floor and is all in revisions; every other group is flat or lower (layout 3,923 → 3,113). Most of it is one task: all three move-holes runs spent their 8 calls reading the plate (that task already reached 60k tokens and 7 calls on h5). The persistence notice and the warning hold never fired; the cap fired twice. About 8% of harness calls fail because the agent reuses a variable from its previous call while each call gets a fresh namespace (9 of 133 on h5, 13 of 152 on h6): an h7 candidate.

**A third held-out set (`heldout3/`, z01–z08), written after h6 was frozen,** at development difficulty, the caveat the review raised against `heldout2/`: fillets and chamfers on rounded corners, tapers, lofts between different sections, tilted and off-axis features, polar and linear patterns, and revisions that need the existing model read (a port row from three to four at the same pitch; fillets added to a tapered planter's slanted corners). Same group mix as before (3 hard-surface, 1 layout, 2 revisions, 2 multi-step). Four authoring agents in parallel, every task proven by `rig.verify_checks` with a 24-segment variant that must pass. Then two independent builders made each task from its prompt alone with a different construction (bmesh, Bevel modifiers, 32 segments): seven tasks passed first time. The eighth caught a real defect: z06's starting rim carried boolean-split vertices 2 mm from each inside corner, so the most natural edit (bevel the slanted edges) failed three checks. The rim was rebuilt, seamed at mid-side, and that edit now passes.

**Third held-out set, run once:** 8 tasks × 3 on no MCP and h6, 48 runs, 0 voids, $0.33. This spends `heldout3/`.

| | No MCP | Harness h6 | Ratio |
|---|---|---|---|
| Pass rate | 18/24 (75%) | 18/24 (75%) | tie |
| Tokens per passed task (headline) | 213,926 | 26,352 | 0.12 |
| Geometric mean tokens per task | 41,508 | 12,581 | **0.30** |
| Without z05: tokens per pass | 35,480 | 22,257 | **0.63** |
| Without z05: geometric mean | 26,441 | 11,500 | **0.43** |
| Model turns per run | 6.0 | 2.3 | |
| Wall time per run | 68.7 s | 29.9 s | 0.44 |
| Cost, 24 runs | $0.239 | $0.094 | 0.39 |

**Read it honestly: the 0.12 headline is one task.** z05 (four ports instead of three) failed all six runs on both setups, and no MCP spent 0.56–1.6 million tokens a run on it over 20–33 calls, 84% of its tokens on the whole set. Its failures are genuine (ports cut too shallow, a filler block standing 1 mm proud of the front, degenerate faces, inside-out normals), and the independent builder passed it in place, so it's a hard task, not a broken one. Without it, the result matches the first held-out set almost exactly: 0.63 overall and 0.43 typical (first set: 0.66 and 0.42). On hard, unseen tasks the harness is reliably about 2.3× cheaper on the typical task, and the overall figure is held back by its own long runs, now mostly revisions.

Both setups pass 75%, under the 82% guardrail, tied with each other: the set is harder, not the harness broken. On hard-surface, layout and multi-step tasks h6 passed 13 of 15, mostly in one call, at 3.5–21k tokens. The two revisions are where it struggles: z05 0/3, and z06 1/3 at 22–110k tokens against no MCP's 3/3 at 34–48k. The 110k z06 run bevelled itself into 105 self-intersecting face pairs, then spent its calls inspecting rather than trying fixes, two of them lost to the fresh-namespace NameError, until the cap. The persistence rule correctly didn't fire, since nothing was changing. One h6 mechanism showed its worth: a phone-stand build declared itself done while three of its cuts had missed; h5 would have accepted that model and failed, while h6 held the run open and the agent rebuilt it to a pass.

**Mining the revision transcripts (free).** 181 recorded revision runs (h1–h6), 528 calls: 210 are inspection-only calls before the first edit, 25% of revision tokens counting only their turns and up to 45% counting what they add to every later call. 205 of the 210 rebuild facts the opening read doesn't state: circular features' centres and radii (67 calls), repeated features' count and spacing (67), a revolved part's profile paired by level (35, plus 23 for a part revolved about X, which the read can't see at all), and each flat level's outline and corner radius (13). Only 4 re-check something the read stated. Control: on the three revisions where the read covers the edit, there were zero inspection calls in 27 runs. 60 of the 210 calls raised: 29 from variables not persisting between calls, 27 from writing `mesh.faces` (Blender's is `polygons`), 4 from an unimported `math`; about 12% of revision tokens together. Full write-up in `runs/_mining/findings.md` (git-ignored with the runs).

**Decided (owner).** h7 explores the opening scene read, generic additions only (circles, repeated features, paired profiles on any axis, flat-level outlines), with the namespace and `faces` fixes alongside. Each addition is built and checked free, one at a time; paid measurement is one bundle (a revision-only pilot first, about $0.05), with the mining script rerun to credit each addition from the traces, and a fresh fourth held-out set for any claim.

**Spend.** This session $0.49 (matrix $0.16, third held-out $0.33); Phase 3 about $2.40 of the $20 standing budget.
