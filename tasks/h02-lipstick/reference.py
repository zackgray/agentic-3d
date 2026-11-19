"""Reference model for h02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Case and sleeve are lathes of their (r, z) profiles. The bullet is a cylinder whose top ring sits
on the tilted cut plane, so its tip is one flat face. VARIANT selects broken versions.
"""
import math

from geom import MM, lathe
from geom_h1 import slant_cylinder

VARIANT = globals().get("VARIANT", "good")

# Case: 1 mm x 45 deg chamfer on the top edge
if VARIANT == "no_chamfer":
    case = [(0, 0.0), (10 * MM, 0.0), (10 * MM, 30 * MM), (0, 30 * MM)]
else:
    case = [(0, 0.0), (10 * MM, 0.0), (10 * MM, 29 * MM), (9 * MM, 30 * MM), (0, 30 * MM)]
lathe("Case", case, seg=96)

# Sleeve: a cup with a 2 mm floor and wall
dz = -0.4 * MM if VARIANT == "sleeve_on_case" else 0.0  # dropped onto the case
s0, s1 = 30.4 * MM + dz, 55 * MM + dz
if VARIANT == "solid_sleeve":
    sleeve = [(0, s0), (9 * MM, s0), (9 * MM, s1), (0, s1)]
else:
    sleeve = [(0, s0), (9 * MM, s0), (9 * MM, s1), (7 * MM, s1), (7 * MM, 32.4 * MM + dz), (0, 32.4 * MM + dz)]
lathe("Sleeve", sleeve, seg=96)

# Bullet: radius 6.5, tip plane through (x = +6.5, z = 62) rising towards -X at 40 deg
R = 6.5 * MM
slope = math.tan(math.radians(45 if VARIANT == "angle_45" else 40))
z_axis = 62 * MM + R * slope  # tip height on the axis


def tip(x, y):
    if VARIANT == "flat_tip":
        return z_axis
    if VARIANT == "tip_reversed":
        return 62 * MM + (R + x) * slope
    if VARIANT == "tip_tilted_y":
        return 62 * MM + (R - y) * slope
    return 62 * MM + (R - x) * slope


shift = -0.4 * MM if VARIANT == "bullet_on_floor" else 0.0
slant_cylinder("Bullet", R, 32.8 * MM + shift, lambda x, y: tip(x, y) + shift, seg=96)
