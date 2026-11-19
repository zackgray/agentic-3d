"""Reference model for y07, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Table clock: the body is a disc lying along Y with one exact boolean taking off the flat bottom,
the front face recess and the crown pocket (cutters joined into one object). Crown and feet are
plain cylinder and boxes. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, box, boolean, cylinder, rename
from geom_m import clean, cyl_along, join

VARIANT = globals().get("VARIANT", "good")
FRONT = 1 if VARIANT == "recess_on_back" else -1  # the front face is the -Y side
DEPTH = 1 if VARIANT == "shallow_recess" else 3

body = cyl_along("Body", 55 * MM, (0.0, -20 * MM, 62 * MM), (0.0, 20 * MM, 62 * MM), seg=128)
cutters = []
if VARIANT != "round_bottom":
    cutters.append(box("Flat", (-60 * MM, -25 * MM, 0.0), (60 * MM, 25 * MM, 12 * MM)))
if VARIANT != "no_recess":
    y_floor = FRONT * (20 - DEPTH) * MM
    y_out = FRONT * 25 * MM
    cutters.append(cyl_along("Recess", 40 * MM, (0.0, y_floor, 62 * MM), (0.0, y_out, 62 * MM), seg=128))
if VARIANT != "no_crown_pocket":
    cutters.append(cylinder("Pocket", 6 * MM, 112 * MM, 125 * MM, seg=64))
boolean(body, join("Cutters", cutters), "DIFFERENCE")
rename(clean(body), "Body")

z0 = 112 if VARIANT == "crown_seated" else 112.5
rename(cylinder("Crown", 5.5 * MM, z0 * MM, 122 * MM, seg=64), "Crown")

top = 12 if VARIANT == "feet_touching" else 11.5
x0, x1 = (23, 37) if VARIANT == "feet_outboard" else (6, 20)
rename(box("FootLeft", (-x1 * MM, -15 * MM, 0.0), (-x0 * MM, 15 * MM, top * MM)), "FootLeft")
rename(box("FootRight", (x0 * MM, -15 * MM, 0.0), (x1 * MM, 15 * MM, top * MM)), "FootRight")
