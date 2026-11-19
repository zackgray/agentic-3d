# Roadmap

Drafted 2026-11-16. Each phase ends at a gate: a written exit check, and an owner decision before the next phase starts. Phases end on evidence, not dates.

## Phase 0 · Eval rig

**Builds:** the machinery every later number depends on.

- A task format: prompt, starting scene, reference values, list of checks.
- A check library: dimensions and scale, watertight, self-intersections, object names and counts, polygon budget, topology health for close-up product renders (shading artifacts, messy faces), geometric match to a reference model.
- A runner that launches Blender headless, connects one agent setup (an MCP server or none), runs a task, and records the verdict. One runner for every setup, so the comparison is fair.
- Token accounting per turn, split by source: tool definitions, images, agent-written code, scene reads, tool results, reasoning. Plus turns, failed calls, retries, wall time and cost.
- A run record: full transcript, verdict (pass / fail / void) and metrics, stored outside git.

**Exit:** one task runs end to end on one baseline with a correct verdict and a full token breakdown. A deliberately broken setup is recorded as void, not fail.

**Risk to check first:** whether a thin agent loop of our own can attribute every token to a source, with no system prompt or tools beyond the setup under test.

## Phase 1 · Pilot

**Runs:** 5 product tasks × 4 baselines × 3 repeats, on Claude Haiku 5.5 at low effort.

- Baselines: Blender's official MCP server; the popular community server (run-any-code plus a screenshot each turn); a ~200-tool typed server; no MCP (scripts run in headless Blender).
- The owner reviews a sample of verdicts by eye to catch broken checks before trusting them.

**Exit:** checks agree with the owner's eye; the cost per run is known; the full matrix is priced.

**Gate decisions:** does Haiku pass enough (about a third or more) to give the comparison signal, or does the baseline move to Sonnet 5.5? Is the full matrix affordable as specified?

## Phase 2 · Full suite and baseline report

**Builds:** about 30 tasks across four groups. Hard-surface products (bottles, caps and threads, cosmetics compacts, electronics housings, packaging) carry the most weight, then client-style revisions ("cap 10% taller", "add the logo emboss", "soften that edge"), then layout, then long multi-step builds.

**Runs:** the full matrix, 3 to 5 repeats per task.

**Exit:** a baseline report. Tokens per passed task, pass rate and wall time for each setup, and a breakdown of where each setup's tokens go.

**Publication checkpoint:** no Blender-specific agent benchmark exists today. This report is the first citable artifact: a measured account of what Blender agents cost and where the waste is. It will be published as a blog post (decided 2026-11-16), so it has to stand up in public:

- Every setup pinned to a recorded version, so the numbers can be reproduced.
- The task set and checks publishable alongside the post.
- Each baseline's authors treated fairly: run on its intended configuration, and any setup fault shown as void rather than counted against them.
- A draft of the post is part of this phase's exit. *Deferred by the owner (2026-11-17) until Phase 3 has results to write about; the phase closed on the measured baseline.*

## Phase 3 · Harness v1

**Builds:** the token-efficient harness, designed from the Phase 2 breakdown, not from assumptions.

- A handful of tools: run code; read the scene as structured data with computed facts; run the checks; render a multi-view grid on request.
- Named, bounded parameters as a core concept.
- Small atomic steps, each one undo step (needed for Phase 4).

**Exit:** on the same suite and model, it beats the best baseline on tokens per passed task by an agreed target, with an equal or better pass rate. Target (agreed 2026-11-16): half the tokens of the best baseline or fewer. It's a starting bar: the claim that current setups are heavy comes from reading, not first-hand measurement, so the target is revisited once the Phase 2 numbers exist.

**Then iterate:** each change is one variable, measured against the suite and recorded in the journal.

## Phase 4 · Watch mode

**Builds:** a stripped-down Blender interface. A viewport with no menu clutter, a panel showing the agent's current step, Stop / Undo-to-here / Redirect, and the model's parameters as sliders.

**Exit:** the owner directs a full product model from brief to finished geometry without touching a modeling tool, and interrupts and redirects at least once mid-build.

## Phase 5 · End-to-end piece

**Makes:** a finished hypothetical product shot. The agent models it under an artist's direction; it goes over USD to other software, where the artist lights and textures it for the final render.

**Exit:** a hero image, plus the numbers from its build (tokens, interruptions, time) beside a by-hand estimate.

**Write-up checkpoint:** the case study is complete: the problem, the benchmark, the harness and the finished piece.

## Phase 6 · Local model (gated)

Start only if Phase 3 logs show enough inner-loop volume for cost or latency to matter.

1. Test existing open fine-tunes (the 3DCodeVerse Qwen 27B LoRAs, the CadQuery 4B LoRA) on the suite before training anything.
2. If there's a gap: fine-tune on the harness's passing transcripts (a 7–14B model fits comfortably on the 4090, 27B with 4-bit training), with the checks as the reward signal later.
3. Split roles: the frontier model plans and critiques, the local model does the repetitive edits.

**Exit:** tokens or cost per passed task against Phase 3, at a stated pass-rate floor.

## Phase 7 · Product animation (later)

Turntables, a cap twisting off, exploded views, mechanical motion. New task group and checks, same method.

## Decided

- 2026-11-16: Phase 3 target is half the tokens of the best baseline at an equal or better pass rate, revisited after Phase 2.
- 2026-11-16: the Phase 2 baseline report is published as a blog post; the repo stays private.
- 2026-11-16: Kimi dropped, both as a baseline column and as an authoring worker. Anthropic models only.
