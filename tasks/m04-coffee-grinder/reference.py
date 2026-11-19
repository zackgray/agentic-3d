"""Reference model for m04, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Body: a lofted rounded block minus a box for the drawer recess. Hopper, lid and knob are lathes of
closed (r, z) profiles; the crank is shaft + arm box + pin, unioned. VARIANT selects broken versions.
"""
from mathutils import Matrix

from geom import MM, boolean, box, cylinder, loft, rename, rounded_rect
from geom_m import mm_lathe

VARIANT = globals().get("VARIANT", "good")
SIGN = -1 if VARIANT == "crank_reversed" else 1


def body():
    plan = rounded_rect(40 * MM, 40 * MM, 8 * MM)
    b = loft("Body", [(plan, 0.0), (plan, 100 * MM)])
    if VARIANT != "no_drawer":
        boolean(b, box("Drawer", (-30 * MM, -41 * MM, 20 * MM), (30 * MM, -35 * MM, 55 * MM)), "DIFFERENCE")
    return rename(b, "Body")


def hopper():
    d = -0.5 if VARIANT == "hopper_on_body" else 0.0
    if VARIANT == "solid_hopper":
        prof = [(0, 100.5), (35, 100.5), (35, 140), (0, 140)]
    else:
        prof = [(0, 100.5), (35, 100.5), (35, 140), (32, 140), (32, 103.5), (0, 103.5)]
    return mm_lathe("Hopper", [(r, z + d) for r, z in prof])


def lid():
    if VARIANT == "lid_no_hole":
        return mm_lathe("Lid", [(0, 140.5), (37, 140.5), (37, 144.5), (0, 144.5)])
    return mm_lathe("Lid", [(4.5, 140.5), (37, 140.5), (37, 144.5), (4.5, 144.5)], closed=True)


def mirror_x(obj):
    if SIGN < 0:
        obj.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
        obj.data.flip_normals()
    return obj


def crank():
    c = cylinder("Crank", 4 * MM, 115 * MM, 151 * MM, seg=48)  # 1 mm into the arm so the union fuses
    boolean(c, mirror_x(box("Arm", (-8 * MM, -5 * MM, 150 * MM), (60 * MM, 5 * MM, 158 * MM))), "UNION")
    boolean(c, cylinder("Pin", 3 * MM, 157 * MM, 178 * MM, SIGN * 55 * MM, 0.0, seg=48), "UNION")
    return rename(c, "Crank")


def knob():
    z0 = 158 if VARIANT == "knob_on_arm" else 158.5
    if VARIANT == "knob_no_bore":
        prof = [(0, z0), (8, z0), (8, 185), (0, 185)]
    else:
        prof = [(0, z0 + 20), (3.5, z0 + 20), (3.5, z0), (8, z0), (8, 185), (0, 185)]
    k = mm_lathe("Knob", prof, seg=64)
    k.data.transform(Matrix.Translation((SIGN * 55 * MM, 0.0, 0.0)))
    return k


body()
hopper()
lid()
crank()
knob()
