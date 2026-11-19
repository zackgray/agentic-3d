"""Reference revision for r01, applied to the starting scene. Runs inside Blender via exec_code.py.

The cap is rebuilt 10% taller (30 -> 33 mm) with the extra height in the side wall. VARIANT selects
deliberately broken revisions (set by verify_checks).
"""
import bpy
from mathutils import Matrix

from geom import MM, lathe, rename

VARIANT = globals().get("VARIANT", "good")
cap = bpy.data.objects["Cap"]
bottle = bpy.data.objects["Bottle"]

if VARIANT == "scaled":  # the naive edit: scale the whole cap 1.1 in Z about its rim
    cap.data.transform(Matrix.Translation((0, 0, 128 * MM)) @ Matrix.Scale(1.1, 4, (0, 0, 1))
                       @ Matrix.Translation((0, 0, -128 * MM)))
elif VARIANT == "moved_up":  # height unchanged, just lifted 3 mm
    cap.data.transform(Matrix.Translation((0, 0, 3 * MM)))
elif VARIANT == "scene_scaled":  # scaled everything, bottle included
    for o in (cap, bottle):
        o.data.transform(Matrix.Scale(1.1, 4, (0, 0, 1)))
elif VARIANT != "unchanged":
    top = 165 * MM if VARIANT == "too_tall" else 161 * MM
    bpy.data.objects.remove(cap, do_unlink=True)
    rename(lathe("Cap", [(0, top), (17 * MM, top), (17 * MM, 128 * MM), (15.5 * MM, 128 * MM),
                         (15.5 * MM, top - 3 * MM), (0, top - 3 * MM)], seg=96), "Cap")
