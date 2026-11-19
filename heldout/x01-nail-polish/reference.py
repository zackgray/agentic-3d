"""Reference model for x01 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

Bottle: a lofted rounded square plus a neck cylinder, minus the bore. Cap: one lathe profile that
carries the filleted top, the open cavity and the brush stem. VARIANT selects deliberately broken
versions (set by verify_checks).
"""
from geom import MM, boolean, cylinder, lathe, loft, rename, rounded_rect
from geom_h1 import arc

VARIANT = globals().get("VARIANT", "good")

if VARIANT == "round_body":  # a round bottle: body and neck in one lathe
    bottle = lathe("Bottle", [(0, 0), (18 * MM, 0), (18 * MM, 48 * MM), (8 * MM, 48 * MM), (8 * MM, 58 * MM),
                              (0, 58 * MM)], seg=96)
else:
    sq = rounded_rect(18 * MM, 18 * MM, 6 * MM)
    bottle = loft("Bottle", [(sq, 0.0), (sq, 48 * MM)])
    boolean(bottle, cylinder("Neck", 8 * MM, 47 * MM, 58 * MM, seg=96), "UNION")
if VARIANT != "no_bore":
    boolean(bottle, cylinder("Bore", 4 * MM, 20 * MM, 59 * MM, seg=64), "DIFFERENCE")
rename(bottle, "Bottle")

dz = -0.5 if VARIANT == "cap_resting" else 0.0  # resting: the whole cap dropped onto the shoulder
if VARIANT == "sharp_cap":
    top = [(0, 88), (10, 88)]
else:
    top = [(0, 88)] + arc(7, 85, 3, 90, 0, n=12)
if VARIANT == "solid_cap":
    under = [(10, 48.5), (0, 48.5)]
elif VARIANT == "no_stem":
    under = [(10, 48.5), (8.4, 48.5), (8.4, 58.5), (0, 58.5)]
else:
    under = [(10, 48.5), (8.4, 48.5), (8.4, 58.5), (2, 58.5), (2, 25), (0, 25)]
lathe("Cap", [(r * MM, (z + dz) * MM) for r, z in top + under], seg=96)
