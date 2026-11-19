"""Reference model for z02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A lathed tapered body with a chamfered top, minus twelve vertical scallop cylinders in a polar
pattern, a D-shaped blind shaft bore (a loft of a D outline) and an off-axis pointer dimple. All
exact booleans. VARIANT selects broken versions.
"""
import math

from geom import MM, boolean, cylinder, lathe, loft, rename
from geom_m import clean
from geom_za import d_outline

VARIANT = globals().get("VARIANT", "good")

r_base = 19 if VARIANT == "no_taper" else 21  # no_taper: straight 19 mm side, chamfer unchanged
chamfer_top = 19 if VARIANT == "no_chamfer" else 17
prof = [(0, 0), (r_base, 0), (19, 14), (chamfer_top, 16), (0, 16)]
if VARIANT == "no_chamfer":
    prof = [(0, 0), (r_base, 0), (19, 14), (19, 16), (0, 16)]
knob = lathe("Knob", [(r * MM, z * MM) for r, z in prof], seg=96)

if VARIANT != "no_scallops":
    count = 10 if VARIANT == "scallops_10" else 12
    start = 0.0 if VARIANT == "scallops_rotated" else 15.0
    for k in range(count):
        t = math.radians(start + 360.0 * k / count)
        boolean(knob, cylinder("Scallop", 3 * MM, -1 * MM, 17 * MM, 21.5 * MM * math.cos(t),
                               21.5 * MM * math.sin(t), seg=47 if start == 0 else 48), "DIFFERENCE")

if VARIANT == "round_bore":
    bore = cylinder("Bore", 3 * MM, -1 * MM, 12 * MM, seg=96)
else:
    d = [(x * MM, y * MM) for x, y in d_outline(3, 1.5)]
    if VARIANT == "flat_wrong_side":
        d = [(-x, -y) for x, y in d]
    top = 17 if VARIANT == "bore_through" else 12
    bore = loft("Bore", [(d, -1 * MM), (d, top * MM)])
boolean(knob, bore, "DIFFERENCE")

if VARIANT != "no_pointer":
    px = -12 if VARIANT == "pointer_wrong_side" else 12
    boolean(knob, cylinder("Pointer", 1.5 * MM, 14.5 * MM, 17 * MM, px * MM, 0.0, seg=48), "DIFFERENCE")

rename(clean(knob), "Knob")
