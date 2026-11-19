"""Reference model for x05, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Base and post are lathes with booleans for the switch pocket and the cross hole; the arm is a rod,
a neck and a lathed hollow shade unioned into one solid. VARIANT selects broken versions.
"""
from mathutils import Matrix

from geom import MM, box, boolean, cylinder, rename
from geom_m import clean, mm_lathe

VARIANT = globals().get("VARIANT", "good")


def base():
    prof = [(0, 0), (60, 0), (60, 15), (57, 18)] if VARIANT != "no_chamfer" else [(0, 0), (60, 0), (60, 18)]
    if VARIANT == "no_socket":
        prof += [(0, 18)]
    else:
        prof += [(8, 18), (8, 6), (0, 6)]
    b = mm_lathe("Base", prof)
    if VARIANT != "no_switch_pocket":
        boolean(b, box("Pocket", (-41 * MM, -4 * MM, 15 * MM), (-29 * MM, 4 * MM, 19 * MM)), "DIFFERENCE")
    return rename(b, "Base")


def post():
    z0 = 6 if VARIANT == "post_seated" else 6.5
    p = mm_lathe("Post", [(0, z0), (7.5, z0), (7.5, 250), (0, 250)], seg=64)
    if VARIANT != "no_hole":
        hole = cylinder("Hole", 4 * MM, -10 * MM, 10 * MM, 0.0, 240 * MM, seg=48, axis="X")
        if VARIANT == "hole_along_y":
            hole.data.transform(Matrix.Translation((0, 0, 240 * MM)) @ Matrix.Rotation(1.5707963, 4, "Z")
                                @ Matrix.Translation((0, 0, -240 * MM)))
        boolean(p, hole, "DIFFERENCE")
    return rename(p, "Post")


def arm():
    ax = 145 if VARIANT == "arm_short" else 165
    rod = cylinder("Arm", 3.5 * MM, -20 * MM, ax * MM, 0.0, 240 * MM, seg=48, axis="X")
    if VARIANT == "solid_shade":
        prof = [(0, 230), (15, 230), (45, 180), (0, 180)]
    else:
        prof = [(0, 230), (15, 230), (45, 180), (43.5, 180), (14.7, 228), (0, 228)]
    shade = mm_lathe("Shade", prof, seg=96)
    shade.data.transform(Matrix.Translation((ax * MM, 0, 0)))
    if VARIANT != "loose_shade":
        neck = cylinder("Neck", 6 * MM, 229 * MM, 246 * MM, ax * MM, 0.0, seg=48)
        boolean(rod, neck, "UNION")
        boolean(rod, shade, "UNION")
    else:  # neck stops 0.5 mm short of the shade: the shade is a second shell in the same mesh
        boolean(rod, cylinder("Neck", 6 * MM, 230.5 * MM, 246 * MM, ax * MM, 0.0, seg=48), "UNION")
        boolean(rod, shade, "UNION")
    return rename(clean(rod), "Arm")


def switch():
    top = 18 if VARIANT == "switch_flush" else 20
    return rename(box("Switch", (-40.5 * MM, -3.5 * MM, 15.5 * MM), (-29.5 * MM, 3.5 * MM, top * MM)), "Switch")


base()
post()
arm()
switch()
