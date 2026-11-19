"""Reference layout for z04, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Five rounded-rectangle swatch blades fanned about a pivot pin on the world Z axis, each turned
15 degrees further counter-clockwise and stacked with 0.5 mm air gaps; the pin's shaft passes
through every blade's pivot hole with 0.5 mm radial clearance. VARIANT selects broken layouts.
"""
import math

from mathutils import Matrix

from geom import MM
from geom_m import mm_lathe
from geom_zb import blade

VARIANT = globals().get("VARIANT", "good")

step = {"clockwise": -15.0, "step_20": 20.0}.get(VARIANT, 15.0)
length = 150.0 if VARIANT == "short_blades" else 160.0
pitch = 3.0 if VARIANT == "touching_stack" else 3.5
for k in range(5):
    level = 4 - k if VARIANT == "reversed_stack" else k
    z0 = (2.5 + pitch * level) * MM
    angle = step * k
    if VARIANT == "centre_pivot":  # turned about the blade's own centre instead of the pivot
        obj = blade(f"Blade_{k + 1}", length * MM, 40 * MM, 6 * MM, z0, z0 + 3 * MM, 12 * MM, 3 * MM, 0.0)
        c = (length / 2 - 12) * MM
        obj.data.transform(Matrix.Translation((c, 0, 0)) @ Matrix.Rotation(math.radians(angle), 4, "Z")
                           @ Matrix.Translation((-c, 0, 0)))
    else:
        blade(f"Blade_{k + 1}", length * MM, 40 * MM, 6 * MM, z0, z0 + 3 * MM, 12 * MM, 3 * MM, angle,
              hole=VARIANT != "no_holes")

shaft = 3.0 if VARIANT == "thick_pin" else 2.5
top = 19.0 if VARIANT == "short_pin" else 20.0  # short: top head sunk into Blade_5
mm_lathe("Pin", [(0, 0), (6, 0), (6, 2), (shaft, 2), (shaft, top), (6, top), (6, top + 2), (0, top + 2)], seg=64)
