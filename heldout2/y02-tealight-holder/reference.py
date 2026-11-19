"""Reference model for y02 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

Block: a loft of square sections (straight sides, then a 45-degree chamfer band at the top), minus
a cylinder for the tealight pocket. VARIANT selects deliberately broken versions (set by
verify_checks).
"""
from geom import MM, boolean, cylinder, loft, rename

VARIANT = globals().get("VARIANT", "good")
dz = 1.0 if VARIANT == "floating" else 0.0  # floating: the whole holder lifted off the ground


def square(h):
    return [(h, -h), (h, h), (-h, h), (-h, -h)]


if VARIANT == "sharp_top":
    layers = [(square(30 * MM), 0.0), (square(30 * MM), 40 * MM)]
else:
    layers = [(square(30 * MM), 0.0), (square(30 * MM), 36 * MM), (square(26 * MM), 40 * MM)]
block = loft("Holder", [(pts, z + dz * MM) for pts, z in layers])

floor = {"through_pocket": -1, "shallow_pocket": 30}.get(VARIANT, 22)
radius = 19.25 if VARIANT == "small_pocket" else 20
boolean(block, cylinder("Pocket", radius * MM, (floor + dz) * MM, (41 + dz) * MM, seg=96), "DIFFERENCE")
rename(block, "Holder")
