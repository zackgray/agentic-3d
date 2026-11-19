"""Writes the 'empty' starting scene: factory settings, no objects, metric units at scale 1.

    blender -b --factory-startup --python empty_scene.py -- out.blend
"""
import sys

import bpy

out = sys.argv[sys.argv.index("--") + 1]
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
    for block in list(coll):
        coll.remove(block)
units = bpy.context.scene.unit_settings
units.system = "METRIC"
units.scale_length = 1.0
units.length_unit = "MILLIMETERS"
bpy.ops.wm.save_as_mainfile(filepath=out)
