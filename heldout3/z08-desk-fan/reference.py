"""Reference model for z08, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Desk fan. Stand: rounded-rectangle loft with a chamfer band, a tapered post (lathe) unioned on,
minus the dial pocket. Motor: a lathe along Y with a filleted rear edge. Rotor: hub cylinder along
Y with five radial blade boxes rotated about the fan axis and unioned. Dial: lathe with a chamfered
top edge. VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

from mathutils import Matrix

from geom import MM, boolean, box, cylinder, rename
from geom_m import clean, mm_lathe
from geom_zd import rr_loft, z_to_y

VARIANT = globals().get("VARIANT", "good")
COARSE = VARIANT == "coarse24"
SEG = 24 if COARSE else 96
N = 6 if COARSE else 16
AXIS_Z = 135.5  # fan axis height, mm

# Stand
if VARIANT == "no_chamfer":
    stand = rr_loft("Stand", [(60, 45, 15, 0), (60, 45, 15, 18)], n=N)
else:
    stand = rr_loft("Stand", [(60, 45, 15, 0), (60, 45, 15, 14), (56, 41, 11, 18)], n=N)
r_top = 15 if VARIANT == "straight_post" else 10
r_17 = 15 + (15 - r_top) / 92  # the post starts 1 mm inside the base so the union fuses
boolean(stand, mm_lathe("Post", [(0, 17), (r_17, 17), (r_top, 110), (0, 110)], seg=SEG), "UNION")
boolean(stand, cylinder("Pocket", 11 * MM, 12 * MM, 19 * MM, 38 * MM, -20 * MM, seg=SEG), "DIFFERENCE")
rename(clean(stand), "Stand")

# Motor: profile (r, along-axis) with the along-axis coordinate becoming world Y
dz = -0.5 if VARIANT == "motor_on_post" else 0.0
if VARIANT == "no_fillet":
    prof = [(0, -20), (25, -20), (25, 40), (0, 40)]
else:
    prof = [(0, -20), (25, -20), (25, 34)]
    prof += [(19 + 6 * math.cos(math.pi / 2 * k / 8), 34 + 6 * math.sin(math.pi / 2 * k / 8)) for k in range(1, 8)]
    prof += [(19, 40), (0, 40)]
motor = z_to_y(mm_lathe("Motor", prof, seg=SEG), AXIS_Z + dz)
rename(motor, "Motor")

# Rotor: hub from y = -36 to -20.5, five blades 16 wide, 3 thick (y -30..-27), out to 78 mm
y_hub = 20 if VARIANT == "rotor_on_motor" else 20.5
rotor = z_to_y(mm_lathe("Rotor", [(0, y_hub), (15, y_hub), (15, 36), (0, 36)], seg=SEG), AXIS_Z)
rotor.data.transform(Matrix.Scale(-1, 4, (0, 1, 0)))
rotor.data.flip_normals()
count = 4 if VARIANT == "four_blades" else 5
offset = 36 if VARIANT == "blades_rotated" else 0
tip = 156 if VARIANT == "blades_too_long" else 78  # too long: 78 mm taken as the blade length past the hub, doubled
for i in range(count):
    blade = box("Blade", (-8 * MM, -30 * MM, 5 * MM), (8 * MM, -27 * MM, tip * MM))
    a = math.radians(offset + i * 360 / count)
    blade.data.transform(Matrix.Translation((0, 0, AXIS_Z * MM)) @ Matrix.Rotation(a, 4, "Y"))
    boolean(rotor, blade, "UNION")
rename(clean(rotor), "Rotor")

# Dial: radius 10.5 from z 12.5 to 24 with a 1.5 mm chamfer on the top edge
r_d = 11 if VARIANT == "dial_tight" else 10.5
dial = mm_lathe("Dial", [(0, 12.5), (r_d, 12.5), (r_d, 22.5), (r_d - 1.5, 24), (0, 24)], seg=SEG)
dial.data.transform(Matrix.Translation((38 * MM, -20 * MM, 0.0)))
rename(dial, "Dial")
