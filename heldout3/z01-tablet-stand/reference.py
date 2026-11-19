"""Reference model for z01, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A rounded-rectangle slab with a rolling-ball fillet round its top perimeter (a loft of inward-offset
outlines), minus a slot whose walls lean 15 degrees (a parallelogram prism along X), minus four
round foot recesses in the underside. All exact booleans. VARIANT selects broken versions.
"""
import math

from geom import MM, boolean, cylinder, rename
from geom_m import clean, rounded_slab
from geom_za import prism_x

VARIANT = globals().get("VARIANT", "good")
T15 = math.tan(math.radians(15))

plan_r = 3 * MM if VARIANT == "small_corners" else 8 * MM
r_top = 0.0 if VARIANT == "no_fillet" else 3 * MM
n = 1 if VARIANT == "chamfer_edge" else 12
stand = rounded_slab("Stand", 40 * MM, 35 * MM, plan_r, 0.0, 20 * MM, r_top=r_top, n=n)

if VARIANT != "no_slot":
    lean = {"vertical_slot": 0.0, "lean_wrong_way": -T15}.get(VARIANT, T15)
    half_len = 40.5 if VARIANT == "slot_full_width" else 30.0
    floor = 5.0 if VARIANT == "slot_too_deep" else 8.0

    def y_at(y_top, z):  # a wall through (y_top, z = 20) leaning back: lower is further to -Y
        return y_top - (20.0 - z) * lean

    top = 21.0  # the cutter overshoots the top face along the same lean
    sect = [(y_at(-10, floor), floor), (y_at(0, floor), floor), (y_at(0, top), top), (y_at(-10, top), top)]
    slot = prism_x("Slot", [(y * MM, z * MM) for y, z in sect], -half_len * MM, half_len * MM)
    boolean(stand, slot, "DIFFERENCE")

if VARIANT != "no_recesses":
    spots = [(24, 18), (-24, 18), (-24, -18), (24, -18)] if VARIANT == "recesses_inboard" else \
        [(30, 25), (-30, 25), (-30, -25), (30, -25)]
    for x, y in spots:
        boolean(stand, cylinder("Recess", 5 * MM, -1 * MM, 1.5 * MM, x * MM, y * MM, seg=64), "DIFFERENCE")

rename(clean(stand), "Stand")
