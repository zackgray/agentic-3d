"""Renders a scene's mesh objects from four views for the owner's review sheet. Never shown to agents.

    blender -b scene.blend --factory-startup --python review_render.py -- out_dir

Front, side and top are orthographic (dimensions read straight off them); the fourth is a
three-quarter view. Workbench engine: flat studio light, outlines, one colour per object.
The scene file is not saved, so the run's record stays exactly as the agent left it.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

out_dir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out_dir, exist_ok=True)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.visible_get()]
scene = bpy.context.scene
if not meshes:
    open(os.path.join(out_dir, "EMPTY"), "w").close()
    sys.exit(0)

pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
centre, size = (lo + hi) / 2, max((hi - lo).length, 1e-4)

scene.render.engine = "BLENDER_WORKBENCH"
for flag in [a for a in dir(scene.render) if a.startswith("use_stamp")]:  # no metadata: it holds local paths
    setattr(scene.render, flag, False)
shading = scene.display.shading
shading.light, shading.color_type = "STUDIO", "OBJECT"
shading.show_cavity = shading.show_object_outline = True
shading.show_backface_culling = False
scene.render.resolution_x = scene.render.resolution_y = 480
scene.render.film_transparent = False
scene.world = scene.world or bpy.data.worlds.new("World")
palette = [(0.85, 0.55, 0.35, 1), (0.40, 0.62, 0.85, 1), (0.55, 0.78, 0.45, 1), (0.82, 0.70, 0.40, 1),
           (0.70, 0.50, 0.80, 1)]
for i, o in enumerate(sorted(meshes, key=lambda o: o.name)):
    o.color = palette[i % len(palette)]

cam_data = bpy.data.cameras.new("ReviewCam")
cam_data.type, cam_data.ortho_scale = "ORTHO", size * 1.15
cam_data.clip_start, cam_data.clip_end = size * 0.01, size * 20
cam = bpy.data.objects.new("ReviewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

VIEWS = {  # name: direction from the centre to the camera
    "front": Vector((0, -1, 0)),
    "side": Vector((1, 0, 0)),
    "top": Vector((0, 0, 1)),
    "three_quarter": Vector((1, -1, 0.8)).normalized(),
}
for name, d in VIEWS.items():
    cam.location = centre + d * size * 4
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    if name == "top":
        cam.rotation_euler = (0, 0, 0)
    scene.render.filepath = os.path.join(out_dir, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("review renders:", math.floor(size * 1000), "mm across")
