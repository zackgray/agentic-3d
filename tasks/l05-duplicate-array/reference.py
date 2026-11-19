"""Reference layout for l05, applied to the starting scene. Runs inside Blender via exec_code.py.

Four real copies of "Product" (own mesh data, transforms applied) in a row centred on the original
at 80 mm pitch. VARIANT selects deliberately broken layouts (set by verify_checks).
"""
import math

import bpy
from mathutils import Matrix

from geom import MM, rename

VARIANT = globals().get("VARIANT", "good")
src = bpy.data.objects["Product"]
OFFSETS = {"Product_2": -160, "Product_3": -80, "Product_4": 80, "Product_5": 160}
if VARIANT == "all_right":  # the naive row: every copy to the +X side of the original
    OFFSETS = {"Product_2": 80, "Product_3": 160, "Product_4": 240, "Product_5": 320}
elif VARIANT == "wrong_pitch":
    OFFSETS = {k: v * 75 / 80 for k, v in OFFSETS.items()}

if VARIANT != "unchanged":
    for i, (name, dx) in enumerate(OFFSETS.items()):
        obj = src.copy()  # shares src.data until given its own below
        bpy.context.scene.collection.objects.link(obj)
        if VARIANT == "linked":  # linked duplicates placed by object location: transforms not applied
            obj.location.x = dx * MM
            obj.name = name
            continue
        obj.data = src.data.copy()
        turn = Matrix.Rotation(math.pi, 4, "Z") if VARIANT == "turned_copies" else Matrix.Identity(4)
        obj.data.transform(Matrix.Translation((dx * MM, 0.0, 0.0)) @ turn)
        rename(obj, f"Product.{i + 1:03d}" if VARIANT == "default_names" else name)
    if VARIANT == "joined":  # everything merged into the original object
        for name in OFFSETS:
            bpy.data.objects[name].select_set(True)
        src.select_set(True)
        bpy.context.view_layer.objects.active = src
        bpy.ops.object.join()
