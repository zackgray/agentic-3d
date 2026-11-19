"""Reference model for p02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A lofted rounded box minus a lofted rounded cavity, plus four boss cylinders, minus four pilot
holes, all with exact booleans. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, boolean, cylinder, loft, rename, rounded_rect

VARIANT = globals().get("VARIANT", "good")
BOSSES = [(42, 22), (-42, 22), (-42, -22), (42, -22)]

outer_r = 0.01 * MM if VARIANT == "sharp_corners" else 5 * MM
outer = rounded_rect(50 * MM, 30 * MM, outer_r)
housing = loft("Housing", [(outer, 0.0), (outer, 25 * MM)])

if VARIANT != "solid":
    wall = 3 * MM if VARIANT == "thick_walls" else 2 * MM
    inner = rounded_rect(50 * MM - wall, 30 * MM - wall, max(0.01 * MM, outer_r - wall))
    boolean(housing, loft("Cavity", [(inner, 2 * MM), (inner, 26 * MM)]), "DIFFERENCE")

if VARIANT not in ("no_bosses", "solid"):
    base = 2.5 * MM if VARIANT == "floating_bosses" else 1 * MM  # floating: starts above the floor
    for x, y in BOSSES:
        boolean(housing, cylinder("Boss", 3.5 * MM, base, 22 * MM, x * MM, y * MM), "UNION")
    if VARIANT != "no_holes":
        for x, y in BOSSES:
            boolean(housing, cylinder("Hole", 1.25 * MM, 4 * MM, 23 * MM, x * MM, y * MM, seg=36),
                    "DIFFERENCE")

rename(housing, "Housing")
