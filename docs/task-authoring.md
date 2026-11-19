# Authoring a task

A task is a folder `tasks/<id>/` holding `task.toml` (prompt, starting scene, checks, variants) and `reference.py` (a hand-built model that proves the checks). Revision tasks add `start.py`, the model the client has already approved. A task is done only when `python -m rig.verify_checks tasks/<id>` prints OK for every variant and exits 0.

## Naming and groups

- `p01`–`p05`: the Phase 1 pilot tasks, all hard-surface; `p03` is the first long build.
- `h..`: hard-surface products (bottles, caps, compacts, housings, packaging). The heaviest group.
- `r..`: client-style revisions to an existing model (`starting_scene = "start.py"`).
- `l..`: layout: placing several parts or products relative to each other.
- `m..`: long multi-step builds: four or more parts, or many features on one part.

The folder name is `<id>-<short-slug>` and matches `id` in `task.toml`. Set `group` to `hard-surface`, `revision`, `layout` or `multi-step`.

## The prompt

- Hypothetical products only. No brand names, no real product reproduced.
- Copy the house style from `p02` (new build) or `r01` (revision): units sentence ("Units are metres (1 Blender unit = 1 m)."), where it stands relative to the ground plane and world axes, every dimension in millimetres with coordinates, then an "object(s)" block: object names, watertight, one connected piece, consistent outward normals, no self-intersections, transforms applied, a face budget, no other mesh objects.
- End with the clean-mesh paragraph and the closing line, verbatim:

  `Mesh hygiene: no duplicate or coincident vertices, no zero-length edges and no zero-area faces. Merge any coincident vertices before you finish.`

  `Tell me when you're done.`

- Specify everything a check measures, and nothing is measured that the prompt leaves to the agent. If a shape is "your choice", no probe may land on it and the volume tolerance must absorb the range of reasonable choices (or leave volume out).
- Revision prompts read like a client note: say what changes and what must stay. Don't restate the existing model's dimensions; reading the scene is part of the task and part of what the benchmark costs.

## Checks

Check types live in `rig/blender_side/checks_*.py`: `objects`, `transforms_applied`, `bbox`, `watertight`, `shells`, `self_intersection`, `topology`, `face_budget`, `no_overlap`, `volume`, `ray_probe`, `helical_thread`. Every task carries the structural set (objects, transforms, bbox, watertight, shells, self-intersection, topology, face budget) plus shape checks (volume, ray probes) for its features.

- **Fair to any valid construction.** A different segment count, a different modelling method, or a bevel built with a modifier must still pass. Aim probes at flat faces or at a curve's widest point, not at facet edges; use 0.3 mm probe tolerance unless the feature is smaller, and at least 1% volume tolerance for curved parts.
- **Volume from the spec, not from the reference.** Write the formula as a comment above the check, then confirm the reference lands within tolerance.
- **Surfaces that touch count as intersecting** in `no_overlap` and `self_intersection`. Where parts sit on each other, the prompt specifies a clearance (0.3–0.5 mm), as `p05` does.
- **Label** every check when a type appears more than once (`bbox_cap`, `probe_holes`).

## Variants

Each variant is a deliberately broken build of the reference (`VARIANT` is set by `verify_checks`) listed under `[variants]` with exactly the checks it must fail. Aim for one variant per mistake an agent plausibly makes: a missing feature, a wrong dimension, the naive edit, a floating part, a wrong orientation, a part at the wrong scale. Every shape check must be failed by at least one variant, or it isn't proven.

Revision tasks must include an `unchanged` variant (the reference does nothing): it fails exactly the checks the requested edit changes, which also proves the starting scene is otherwise clean. The first revision task caught a starting model whose cap already touched its bottle this way.

## Shared code

`tasks/_lib/geom.py` holds the reference helpers (`lathe`, `loft`, `rounded_rect`, `box`, `cylinder`, `boolean`, `rename`). Reference models build in world coordinates at identity transforms. Keep every file under about 300 lines.
