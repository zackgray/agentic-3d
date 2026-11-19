"""Reference layout for l02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Three lathed bottles (body, flat shoulder, 20 mm neck) in a row along X with 20 mm surface gaps, the
row's overall extent centred on x = 0. VARIANT selects deliberately broken layouts (set by verify_checks).
"""
from mathutils import Matrix

from geom import MM, lathe

VARIANT = globals().get("VARIANT", "good")
# (name, body r, neck r, height) in mm, small to large
SIZES = [("Bottle_S", 20, 8, 100), ("Bottle_M", 25, 10, 140), ("Bottle_L", 30, 12, 180)]
if VARIANT == "wrong_order":
    SIZES = SIZES[::-1]

gap = 0 if VARIANT == "touching" else 20
span = sum(2 * R for _n, R, _r, _H in SIZES) + gap * (len(SIZES) - 1)
x, centres = -span / 2, []
for _n, R, _r, _H in SIZES:
    centres.append(x + R)
    x += 2 * R + gap
if VARIANT == "centred_on_middle":  # the naive centring: the middle bottle's axis on x = 0
    centres = [c - centres[1] for c in centres]
elif VARIANT == "equal_pitch":  # equal centre spacing instead of equal surface gaps
    centres = [-75, 0, 75]

z0 = 5 if VARIANT == "floating" else 0
for (name, R, r, H), cx in zip(SIZES, centres):
    if VARIANT == "thin_neck_m" and name == "Bottle_M":
        r = 7
    if VARIANT == "no_necks":
        prof = [(0, z0), (R, z0), (R, z0 + H), (0, z0 + H)]
    else:
        prof = [(0, z0), (R, z0), (R, z0 + H - 20), (r, z0 + H - 20), (r, z0 + H), (0, z0 + H)]
    obj = lathe(name, [(a * MM, b * MM) for a, b in prof], seg=64)
    obj.data.transform(Matrix.Translation((cx * MM, 0.0, 0.0)))
