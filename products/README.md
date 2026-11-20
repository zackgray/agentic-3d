# Product-page briefs

Invented products briefed the way a real job arrives: a product page's text and one front product shot, with no dimensions. They exist to test the spec-first workflow, where the agent writes a dimensioned spec from the brief (tracing the profile from the shot, solving scale from the net contents, taking necks and caps from packaging standards), the owner approves it, and then the agent builds.

Every product here is hypothetical. Names, shapes and colours are invented; no real brand, trade dress or client job belongs in this folder.

## Each product

- `product.toml`: the page text the agent sees (`page`), plus the object names, the shot's colours and the printed label band (the band is in the picture only, never in the model).
- `shot.png`: the one image the agent sees. A front view from slightly above, white background, long lens, no scale cue.
- `reference.py`: the hidden reference model, built with the task helpers in `tasks/_lib`.
- `facts.json`: the hidden key, measured from the reference: each object's size and closed volume, and the overall size.

The agent sees only `page` and `shot.png`. Run anything that gives it these briefs on the sandboxed setups, where the agent's code can't read the repository.

## Products

| Product | Container | Net contents | Reference size (mm) | Outer volume |
|---|---|---|---|---|
| Volta Citrus Soda | Contoured PET bottle, screw cap | 591 mL | 68 × 223 | 655 mL bottle |
| Halden Sparkling Water | Aluminium can | 355 mL | 66 × 122.2 | 390 mL |
| Northpeak Spring Water | Ribbed PET bottle, screw cap | 500 mL | 63 × 195 | 500 mL bottle |
| Orchard Row Apple Juice | Gable-top carton | 1.54 L | 90 × 90 × 237 | 1.68 L |

Rebuild the shots and keys with `python -m rig.product_briefs` (free, no model calls).
