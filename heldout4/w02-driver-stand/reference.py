"""Reference model for w02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Screwdriver stand: a rounded-rectangle loft with a chamfer band, minus a linear row of five round
blind holes whose axes lean 20 degrees off vertical. Each cutter is a cylinder built along its own
axis with a square-cut end. All exact booleans. VARIANT selects deliberately broken versions.
"""
import math

from geom import MM, boolean, rename
from geom_m import clean
from geom_wa import axis_cylinder, rr_loft

VARIANT = globals().get("VARIANT", "good")
COARSE = VARIANT == "coarse"
N = 6 if COARSE else 16  # points per quarter circle on the plan corners
SEG = 24 if COARSE else 48

r = 0.01 if VARIANT == "sharp_corners" else 8
if VARIANT == "no_chamfer":
    block = rr_loft("DriverStand", [(50, 20, r, 0), (50, 20, r, 30)], n=N)
else:
    block = rr_loft("DriverStand", [(50, 20, r, 0), (50, 20, r, 27), (47, 17, max(0.01, r - 3), 30)], n=N)

tilt = {"vertical_holes": 0.0, "lean_wrong_way": -20.0}.get(VARIANT, 20.0)
d = (0.0, math.sin(math.radians(tilt)), -math.cos(math.radians(tilt)))  # down into the block
depth = 20 / math.cos(math.radians(20)) if VARIANT == "depth_measured_vertically" else 20
xs = {"pitch_20": [-40, -20, 0, 20, 40], "four_holes": [-27, -9, 9, 27]}.get(VARIANT, [-36, -18, 0, 18, 36])
for x in xs:
    boolean(block, axis_cylinder("Hole", 5, (x, 0, 30), d, -12, depth, seg=SEG), "DIFFERENCE")

rename(clean(block), "DriverStand")
