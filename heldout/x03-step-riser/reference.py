"""Reference layout for x03 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

A two-step riser (two overlapping boxes fused), two lidded jars on the low step and a carton turned
30 degrees on the high step, each product 0.5 mm clear of its step. VARIANT selects deliberately
broken layouts (set by verify_checks).
"""
import math

from mathutils import Matrix

from geom import MM, box, boolean, lathe, rename

VARIANT = globals().get("VARIANT", "good")
CLEAR = 0.0 if VARIANT == "resting" else 0.5

if VARIANT == "one_step":  # the whole riser at the high step's height
    riser = box("Riser", (-80 * MM, -50 * MM, 0.0), (80 * MM, 60 * MM, 60 * MM))
else:
    riser = box("Riser", (-80 * MM, 0.0, 0.0), (80 * MM, 60 * MM, 60 * MM))
    boolean(riser, box("Low", (-80 * MM, -50 * MM, 0.0), (80 * MM, 1 * MM, 30 * MM)), "UNION")
rename(riser, "Riser")

jar_x = 15 if VARIANT == "jar_pitch" else 35  # jar_pitch: 30 mm read as centre-to-centre
z0 = 30 + CLEAR
if VARIANT == "no_lids":
    prof = [(0, 0), (20, 0), (20, 50), (0, 50)]
else:
    prof = [(0, 0), (20, 0), (20, 40), (22, 40), (22, 50), (0, 50)]
for name, sx in (("Jar_L", -1), ("Jar_R", 1)):
    jar = lathe(name, [(r * MM, (z + z0) * MM) for r, z in prof], seg=96)
    jar.data.transform(Matrix.Translation((sx * jar_x * MM, -25 * MM, 0.0)))

height = 80 if VARIANT == "box_short" else 90
carton = box("Carton", (-30 * MM, -15 * MM, (60 + CLEAR) * MM), (30 * MM, 15 * MM, (60 + CLEAR + height) * MM))
angle = {"unrotated": 0, "wrong_way": -30}.get(VARIANT, 30)
carton.data.transform(Matrix.Translation((0.0, 30 * MM, 0.0)) @ Matrix.Rotation(math.radians(angle), 4, "Z"))
