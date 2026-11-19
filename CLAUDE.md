# Working in Agentic 3D

Read `docs/handoff.md` if it exists, then `README.md` and the newest entries of `docs/journal.md`, before proposing work.

- **Measure before building.** No harness code until the eval suite and baselines exist. If a step is being skipped, name it and recommend doing it first.
- **Goal #1 is fewer tokens** for Blender modeling work; accuracy and speed follow. Every claim about efficiency needs a number from the eval.
- **Pass / fail / void.** A setup fault is void, never a failure. Fix the setup and rerun.
- **Hypothetical products only.** No client work.
- **Anthropic models only.** Kimi was dropped 2026-11-16; don't reintroduce another model family without the owner's go.
- **Spend:** get the owner's go before any run that isn't the agreed pilot or matrix.
- **Owner's split:** the agent models (and later animates); the owner lights, textures and finishes in other software. Don't build lighting or texturing tooling.
- **Documentation is part of the work.** At the end of every session, add a dated entry to `docs/journal.md`: what was done, decided (and why), and measured. Keep numbers and the reasons behind decisions; those are the story. When a measured result lands, update `docs/case-study.md`.
- Blender 5.2 is installed on this workstation (`C:/Program Files/Blender Foundation/Blender 5.2`).
- Files under ~300 lines; Markdown with no hard wraps.
