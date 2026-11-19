"""Reference revision for r06, applied to the starting scene. Runs inside Blender via exec_code.py.

The barrel grows 20 mm (x 15..125 -> 15..145); the tip stays put and the end cap and clip move 20 mm
along +X unchanged in shape. VARIANT selects broken revisions; "scaled_uniform" is the naive edit.
"""
import bpy
from mathutils import Matrix

from geom import MM, boolean, box, lathe, rename
from geom_r import Z_TO_X, remove, xform

VARIANT = globals().get("VARIANT", "good")


def pen(extra):
    end = 125 + extra
    p = xform(lathe("Pen", [(0, 0), (0.5 * MM, 0), (5 * MM, 15 * MM), (5 * MM, end * MM),
                            (5.5 * MM, end * MM), (5.5 * MM, (end + 15) * MM), (0, (end + 15) * MM)],
                    seg=96), Z_TO_X)
    boolean(p, box("Clip", ((end + 2) * MM, -1.5 * MM, 4.5 * MM), ((end + 14) * MM, 1.5 * MM, 7 * MM)),
            "UNION")
    return rename(p, "Pen")


obj = bpy.data.objects["Pen"]
if VARIANT == "scaled_uniform":  # the naive edit: scale the whole pen 160/140 along X about the tip
    xform(obj, Matrix.Scale(160 / 140, 4, (1, 0, 0)))
elif VARIANT == "scaled_all_axes":  # uniform scale in every axis
    xform(obj, Matrix.Scale(160 / 140, 4))
elif VARIANT == "stretched_rear":  # everything behind the tip cone stretched: cap and clip too
    for v in obj.data.vertices:
        if v.co.x > 15 * MM + 1e-6:
            v.co.x = 15 * MM + (v.co.x - 15 * MM) * 145 / 125
elif VARIANT == "tip_end_extended":  # the barrel grown at the tip end: the whole pen shifts back
    remove("Pen")
    xform(pen(20), Matrix.Translation((-20 * MM, 0, 0)))
elif VARIANT != "unchanged":
    remove("Pen")
    pen(25 if VARIANT == "too_long" else 20)
