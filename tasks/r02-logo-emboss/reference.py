"""Reference revision for r02, applied to the starting scene. Runs inside Blender via exec_code.py.

A raised logo plaque, 40 x 20 mm with 4 mm corner radii, 2 mm proud of the -Y face (y -20 -> -22),
centred on that face at (x, z) = (0, 50) mm, fused with an exact union. VARIANT selects deliberately
broken revisions (set by verify_checks).
"""
import bpy
from mathutils import Matrix

from geom import MM, boolean
from geom_r import FACE_MINUS_Y, merge, slab, xform

VARIANT = globals().get("VARIANT", "good")
carton = bpy.data.objects["Carton"]


def plaque(h0, h1, r=4 * MM, zc=50 * MM, back=False):
    """Plaque from y = -h0 out to y = -h1 on the -Y side, centred at (x, z) = (0, zc)."""
    p = xform(slab("Plaque", 20 * MM, 10 * MM, r, h0, h1), Matrix.Translation((0, 0, zc)) @ FACE_MINUS_Y)
    if back:  # mirror onto the +Y face (two mirrors keep the winding)
        xform(p, Matrix.Scale(-1, 4, (0, 1, 0)) @ Matrix.Scale(-1, 4, (1, 0, 0)))
    return p


if VARIANT == "unchanged":
    pass
elif VARIANT == "recessed":  # debossed 2 mm into the face instead of raised
    boolean(carton, plaque(18 * MM, 21 * MM), "DIFFERENCE")
elif VARIANT == "not_fused":  # plaque pushed 0.5 mm into the face and joined, no boolean
    merge(carton, plaque(19.5 * MM, 22 * MM))
else:
    kw = {}
    top = 22 * MM
    if VARIANT == "sharp_corners":
        kw["r"] = 0.01 * MM
    elif VARIANT == "off_centre":  # centred on the lower half instead of the face
        kw["zc"] = 40 * MM
    elif VARIANT == "wrong_face":
        kw["back"] = True
    elif VARIANT == "too_high":
        top = 23 * MM
    boolean(carton, plaque(19 * MM, top, **kw), "UNION")
