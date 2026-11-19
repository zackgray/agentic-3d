"""Reference model for h01, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Base and lid are lathes of their (r, z) profiles; the lid's top roundover is an arc in the profile.
VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, lathe
from geom_h1 import arc

VARIANT = globals().get("VARIANT", "good")

R = 33 * MM if VARIANT == "small_base" else 35 * MM
pan_r = 25 * MM if VARIANT == "narrow_recess" else 28 * MM
floor = 3 * MM if VARIANT == "deep_recess" else 6 * MM

if VARIANT == "no_recess":
    base_profile = [(0, 0.0), (R, 0.0), (R, 10 * MM), (0, 10 * MM)]
else:
    base_profile = [(0, 0.0), (R, 0.0), (R, 10 * MM), (pan_r, 10 * MM), (pan_r, floor), (0, floor)]
lathe("Base", base_profile, seg=128)

shift = -0.4 * MM if VARIANT == "lid_touching" else 0.0  # touching: lid dropped onto the base
z0, z1 = 10.4 * MM + shift, 16 * MM + shift
LR = 35 * MM
if VARIANT == "sharp_lid":
    lid_profile = [(0, z0), (LR, z0), (LR, z1), (0, z1)]
else:
    rho = 3 * MM
    lid_profile = [(0, z0), (LR, z0)] + arc(LR - rho, z1 - rho, rho, 0, 90, n=16) + [(0, z1)]
lathe("Lid", lid_profile, seg=128)
