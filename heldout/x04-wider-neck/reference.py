"""Reference revision for x04 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

The neck grows from 18 to 24 mm across with its 10 mm bore unchanged, and the cap is rebuilt round it
with the same 2 mm side wall, 3 mm top wall, 0.5 mm clearances and rim height. VARIANT selects
deliberately broken revisions (set by verify_checks).
"""
import bpy
from mathutils import Matrix

from geom import MM, boolean, cylinder, lathe, loft, rename, rounded_rect

VARIANT = globals().get("VARIANT", "good")


def rebuild_bottle(neck_r, bore_r, corner_r=8):
    bpy.data.objects.remove(bpy.data.objects["Bottle"], do_unlink=True)
    body = rounded_rect(28 * MM, 20 * MM, corner_r * MM)
    bottle = loft("Bottle", [(body, 0.0), (body, 100 * MM)])
    boolean(bottle, cylinder("Neck", neck_r * MM, 99 * MM, 116 * MM, seg=96), "UNION")
    boolean(bottle, cylinder("Bore", bore_r * MM, 90 * MM, 117 * MM, seg=64), "DIFFERENCE")
    rename(bottle, "Bottle")


def rebuild_cap(inner_r):
    bpy.data.objects.remove(bpy.data.objects["Cap"], do_unlink=True)
    outer_r = inner_r + 2
    lathe("Cap", [(0, 119.5 * MM), (outer_r * MM, 119.5 * MM), (outer_r * MM, 104 * MM), (inner_r * MM, 104 * MM),
                  (inner_r * MM, 116.5 * MM), (0, 116.5 * MM)], seg=96)


if VARIANT == "neck_scaled":  # the naive edit on the bottle: scale the neck, bore and all, by 12/9
    rebuild_bottle(12, 5 * 12 / 9)
    rebuild_cap(12.5)
elif VARIANT == "cap_scaled":  # the naive edit on the cap: scale it in X and Y until it is 29 mm across
    rebuild_bottle(12, 5)
    k = 14.5 / 11.5
    bpy.data.objects["Cap"].data.transform(Matrix.Diagonal((k, k, 1.0, 1.0)))
elif VARIANT == "cap_left":  # neck widened, cap forgotten
    rebuild_bottle(12, 5)
elif VARIANT == "radius_plus_6":  # 6 mm added to the radius instead of the diameter
    rebuild_bottle(15, 5)
    rebuild_cap(15.5)
elif VARIANT == "body_rebuilt_sharp":  # bottle redrawn from scratch, body corner radii lost
    rebuild_bottle(12, 5, corner_r=0.01)
    rebuild_cap(12.5)
elif VARIANT != "unchanged":
    rebuild_bottle(12, 5)
    rebuild_cap(12.5)
