"""Reference model for h05, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The body is a loft of a rounded square along Z, turned so the loft runs along Y. Prong boxes are
unioned (rooted 1 mm inside the body) and the port box cut, both with exact booleans.
VARIANT selects broken versions.
"""
import math

from mathutils import Matrix

from geom import MM, box, boolean, loft, rename, rounded_rect
from geom_h1 import transform

VARIANT = globals().get("VARIANT", "good")

r = 0.01 * MM if VARIANT == "sharp_corners" else 6 * MM
section = rounded_rect(18 * MM, 18 * MM, r)
body = loft("Charger", [(section, -14 * MM), (section, 14 * MM)])
# local (x, y, z) -> world (x, -z, y + 18 mm): the section stands in XZ, the loft runs along Y
transform(body, Matrix.Translation((0, 0, 18 * MM)) @ Matrix.Rotation(math.pi / 2, 4, "X"))

hx, hz = (3.2 * MM, 0.75 * MM) if VARIANT == "prongs_rotated" else (0.75 * MM, 3.2 * MM)
if VARIANT == "prongs_on_front":
    y0, y1 = -30 * MM, -13 * MM
else:
    y0 = 14.5 * MM if VARIANT == "prongs_floating" else 13 * MM
    y1 = 24 * MM if VARIANT == "short_prongs" else 30 * MM
for x in (-6.35 * MM, 6.35 * MM):
    prong = box("Prong", (x - hx, y0, 18 * MM - hz), (x + hx, y1, 18 * MM + hz))
    boolean(body, prong, "UNION")

if VARIANT != "no_port":
    px, pz = (1.7 * MM, 4.5 * MM) if VARIANT == "port_vertical" else (4.5 * MM, 1.7 * MM)
    bottom = -11 * MM if VARIANT == "shallow_port" else -7 * MM
    boolean(body, box("Port", (-px, -15 * MM, 18 * MM - pz), (px, bottom, 18 * MM + pz)), "DIFFERENCE")
rename(body, "Charger")
