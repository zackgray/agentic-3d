"""Reference model for y08, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Battery lantern: base and cap are cylinders with their recesses (and the cap's two square handle
pockets) cut by one exact boolean each; the diffuser is a closed-profile lathe (open tube); the
handle is three boxes unioned. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from mathutils import Matrix

from geom import MM, box, boolean, cylinder, rename
from geom_m import clean, join, mm_lathe

VARIANT = globals().get("VARIANT", "good")
ALONG_Y = VARIANT == "handle_along_y"  # handle and its pockets turned 90 degrees about Z


def turn(obj):
    if ALONG_Y:
        obj.data.transform(Matrix.Rotation(1.5707963267948966, 4, "Z"))
    return obj


base = cylinder("Base", 45 * MM, 0.0, 25 * MM, seg=128)
if VARIANT != "no_base_recess":
    boolean(base, cylinder("Seat", 36 * MM, 22 * MM, 30 * MM, seg=128), "DIFFERENCE")
rename(clean(base), "Base")

z0 = 22 if VARIANT == "diffuser_seated" else 22.5
r_in = 0 if VARIANT == "solid_diffuser" else (34 if VARIANT == "thin_wall" else 32.5)
if r_in:
    prof = [(r_in, z0),(35.5, z0), (35.5, 152.5), (r_in, 152.5)]
    diffuser = mm_lathe("Diffuser", prof, seg=128, closed=True)
else:
    diffuser = mm_lathe("Diffuser", [(0, z0), (35.5, z0), (35.5, 152.5), (0, 152.5)], seg=128)
rename(diffuser, "Diffuser")

cap = cylinder("Cap", 45 * MM, 150 * MM, 170 * MM, seg=128)
cutters = []
if VARIANT != "no_cap_recess":
    cutters.append(cylinder("Seat", 36 * MM, 145 * MM, 153 * MM, seg=128))
if VARIANT != "no_handle_pockets":
    cutters += [turn(box("Pocket", ((x - 3.5) * MM, -3.5 * MM, 160 * MM), ((x + 3.5) * MM, 3.5 * MM, 175 * MM)))
                for x in (-36, 36)]
if cutters:
    boolean(cap, join("Cutters", cutters), "DIFFERENCE")
rename(clean(cap), "Cap")

top = 196 if VARIANT == "handle_low" else 206
legs = [turn(box("Leg", ((x - 3) * MM, -3 * MM, 160.5 * MM), ((x + 3) * MM, 3 * MM, top * MM))) for x in (-36, 36)]
handle = turn(box("Handle", (-39 * MM, -3 * MM, (top - 6) * MM), (39 * MM, 3 * MM, top * MM)))
boolean(handle, join("Legs", legs), "UNION")
rename(clean(handle), "Handle")
