# Agentic 3D

An agent harness that drives Blender to model products for commercial CGI, built to use far fewer tokens than today's Blender MCP servers while getting more right. Started 2026-11-16.

The intended split: the agent models, and later animates; a human artist lights, textures and finishes in their own software. The aim is for the artist to art-direct 3D work rather than model it by hand.

## Goals, in order

1. **Fewer tokens** per finished modeling task than existing Blender agent setups, measured, not claimed.
2. **More accurate**: more tasks pass their checks on the first full run.
3. **Faster** wall-clock per task.

Later, if the numbers justify it: a small local model on the RTX 4090, fine-tuned on this harness's own successful runs.

## Method

Measure before building. The order is fixed:

1. **Eval suite.** About 30 hypothetical product-modeling tasks, each with a starting scene and automatic checks. Groups: layout, hard-surface products, client-style revisions to an existing model, long multi-step builds, then product animation later.
2. **Baselines.** The same tasks run through existing setups, on the same model: Blender's official MCP server, the most popular community server (runs any code, screenshot every turn), a ~200-tool typed server, and no MCP at all (the agent writes scripts and runs Blender in the background).
3. **Pilot first.** Five tasks across all baselines to prove the checks and price the full run.
4. **Our harness**, built only after the baselines show where the tokens go.

Every run records pass / fail / **void**. A void is a setup fault (a broken check, a crashed Blender, a bad task), never counted as the agent failing. Lesson carried from earlier agent work, where setup errors were once misread as model limits.

## What gets measured per run

Pass/fail/void; tokens split by source (tool definitions, images, agent code, scene reads, reasoning); turns; failed tool calls and retries; wall time; dollar cost. Each task runs 3 to 5 times. Full transcripts are kept: they are the fine-tuning data if that phase happens.

## Models

- **Anthropic:** Claude Haiku 5.5 at low effort, the least token-hungry option. If it passes fewer than about a third of the pilot, the baseline moves to Claude Sonnet 5.5 at low effort.
- Anthropic models only (decided 2026-11-16). Harnesses are compared within one model, since token counts aren't comparable across model families.

All tasks are hypothetical products. No client work goes into this repo.

## Harness principles (to be tested, not assumed)

- Few tools: run code, read the scene as structured data, render a multi-view grid, run checks.
- Structured scene summary by default; renders only when the question is about appearance.
- Deterministic checks (dimensions, watertight, intersections, topology, polygon budget) before any vision judge.
- Named, bounded parameters that both the agent and the artist's UI edit.
- Small atomic steps, each one undo step, so the artist can interrupt, roll back and redirect.

## Interface

A stripped-down Blender viewport so the artist can watch the agent work live and stop it at a step boundary. Evals run Blender headless and in parallel. Finished models hand off to other software over USD.

## Docs

- `docs/journal.md`: dated record of what was done, decided and measured. Written every session. Phases 0–2 are in `docs/journal-phases-0-2.md`.
- `docs/research.md`: the landscape as of 2026-11-16, with sources.
- `docs/roadmap.md`: phases, exit checks and gates.
- `docs/case-study.md`: the write-up, filled in as results land.

## License

GPL-3.0-or-later (see `LICENSE`). The Blender-side code runs inside Blender and uses its Python API, so the whole repository follows Blender's licence.
