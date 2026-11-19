"""Reference model for y03 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

Tissue-box cover: an outer box, minus an inner box that runs out through the bottom (open
underside, 4 mm walls and top), minus a stadium-shaped prism through the top. VARIANT selects
deliberately broken builds (set by verify_checks).
"""
import math

from geom import MM, box, boolean, loft, rename

VARIANT = globals().get("VARIANT", "good")
WALL = 3 if VARIANT == "thin_wall" else 4


def stadium(half_len, r, n=24):
    """Convex outline of a slot: two semicircles of radius r centred at x = +-(half_len - r)."""
    c = half_len - r
    right = [(c + r * math.cos(a), r * math.sin(a))
             for a in (math.radians(-90 + 180 * k / n) for k in range(n + 1))]
    return right + [(-x, -y) for x, y in right]


# wall_outward: the walls thickened outward from the given size, as an outward Solidify would
GROW = 4 if VARIANT == "wall_outward" else 0
HX, HY, TOP = 120 + GROW, 62 + GROW, 90 + GROW
cover = box("Cover", (-HX * MM, -HY * MM, 0.0), (HX * MM, HY * MM, TOP * MM))
if VARIANT != "solid":
    floor = 4 if VARIANT == "closed_bottom" else -1  # good: cavity runs 1 mm out through the bottom
    boolean(cover, box("Cavity", ((-HX + WALL) * MM, (-HY + WALL) * MM, floor * MM),
                       ((HX - WALL) * MM, (HY - WALL) * MM, (TOP - WALL) * MM)), "DIFFERENCE")
if VARIANT == "rect_slot":
    outline = [(60, -15), (60, 15), (-60, 15), (-60, -15)]
    boolean(cover, loft("Slot", [([(x * MM, y * MM) for x, y in outline], z * MM) for z in (80, TOP + 1)]),
            "DIFFERENCE")
elif VARIANT != "no_slot":
    boolean(cover, loft("Slot", [(stadium(60 * MM, 15 * MM), z * MM) for z in (80, TOP + 1)]), "DIFFERENCE")
rename(cover, "Cover")
