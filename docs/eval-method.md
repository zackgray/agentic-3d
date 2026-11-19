# Evaluation method

How results are measured and compared from Phase 3 on. Set 2026-11-17 from the Phase 2 baseline data, before any harness work, so the rules can't be fitted to the results.

## What is measured

- **Headline: tokens per passed task** (owner, 2026-11-17). Total tokens, input and output, over all runs of a setup, divided by its passes. Cost is reported alongside but isn't the headline, because caching makes dollars understate the gap.
- **Guardrail: pass rate.** Accuracy isn't the claim; it must not regress. The Phase 2 reference is no MCP at 80/90 (88.9%). With 90 runs, a pass rate's standard error is about 3.3 points, so anything below about 82% is a real drop and means something broke. Between 82% and 89%, rerun before concluding anything.
- **Speed: wall time per run,** reported per setup. About 85% of it is model generation, so it tracks output tokens.
- Void runs are excluded and rerun, never counted.

## The suites

- **Development suite:** the 30 tasks in `tasks/`. The harness is designed and tuned against these.
- **Held-out suite:** the tasks in `heldout/`, written before any harness work and **not run until the final claim**. A harness tuned for weeks on the development suite partly learns it; the held-out result is the one that stands up in public. Running a held-out task early, even to debug, spends it.

## Comparing a harness change with the baseline

Compare on the same 30 tasks and the same model and effort (Haiku 5.5, low), against the recorded no-MCP baseline (3 runs per task). Measure the ratio of geometric-mean tokens per task, which keeps one expensive task from dominating.

Tokens vary a lot from run to run: the within-task spread is 0.51 on a log scale. What that means for a comparison against the 3-run baseline:

| Candidate runs per task | 95% interval on the ratio | Smallest change reliably detected |
|---|---|---|
| 3 | ±16% | about 19% |
| 5 | ±14% | about 17% |
| 10 | ±13% | about 16% |

Rerunning the baseline at 5 per task as well narrows this to ±12% (about 15% detectable).

- **The Phase 3 target (half the tokens) is far outside the noise.** One matrix of 3 runs per task settles it.
- **Single-variable iterations that save less than about 15% can't be told from noise** at affordable repeat counts. Group small changes and measure them together, or accept that they're unproven.
- One iteration on the suite is about 150 runs at 5 repeats: about $0.60 and 80 minutes on no-MCP-sized runs.

## Phase 3 ground rules (owner, 2026-11-17)

- **Target:** at most half of no-MCP's tokens per passed task (26,727, so about 13,400), with the pass rate at or above 82%, on the development suite; confirmed once on the held-out suite.
- **Model settings stay fixed for the headline:** Haiku 5.5 at low effort, as the baselines ran. Changes to thinking (off, or a smaller budget) are measured as a separate arm and applied to the no-MCP baseline too, so a win can't be just a setting anyone could flip.
- **Validation tools are generic only:** facts any user would want about the mesh and scene (manifold, intersections, bounds, gaps between parts). Never the task's own probes or expected values.
- **Spend:** a standing $20 for Phase 3 iterations. Spend is reported in the journal each session; going past it needs the owner's go.
