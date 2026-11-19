"""Reference model for x08, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Tray: a rounded-corner slab with two end tabs unioned on, then one exact boolean with all twelve
tapered pockets (square lofts) joined into a single cutter. VARIANT selects broken versions.
"""
from mathutils import Matrix

from geom import MM, box, boolean, loft, rename
from geom_m import clean, join, rounded_slab

VARIANT = globals().get("VARIANT", "good")
XS = (-68, -34, 0, 34, 68) if VARIANT == "ten_pockets" else (-85, -51, -17, 17, 51, 85)
FLOOR = 10 if VARIANT == "shallow_pockets" else 7
HALF_FLOOR = 15 if VARIANT == "straight_pockets" else 13


def square(h):
    return [(h, h), (-h, h), (-h, -h), (h, -h)]


def pocket(x, y):
    """Tapered square pocket cutter: HALF_FLOOR half-width at the floor, 15 at z = 35, carried on
    1 mm above the top along the same slope so the cut is clean."""
    slope = (15 - HALF_FLOOR) / (35 - FLOOR)
    p = loft("Pocket", [(square(HALF_FLOOR * MM), FLOOR * MM), (square((15 + slope) * MM), 36 * MM)])
    p.data.transform(Matrix.Translation((x * MM, y * MM, 0.0)))
    return p


R = 0.5 if VARIANT == "sharp_corners" else 6
tray = rounded_slab("Tray", 105 * MM, 38 * MM, R * MM, 0.0, 35 * MM)
if VARIANT != "no_tabs":
    x0 = 105.5 if VARIANT == "loose_tabs" else 104  # good: 1 mm into the end wall so the union fuses
    tabs = [box("Tab", (x0 * MM, -20 * MM, 32 * MM), (120 * MM, 20 * MM, 35 * MM)),
            box("Tab", (-120 * MM, -20 * MM, 32 * MM), (-x0 * MM, 20 * MM, 35 * MM))]
    boolean(tray, join("Tabs", tabs), "UNION")
boolean(tray, join("Pockets", [pocket(x, y) for x in XS for y in (-17, 17)]), "DIFFERENCE")
rename(clean(tray), "Tray")
