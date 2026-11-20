"""Renders a product-page style front shot of a scene and measures it. Never shown to agents as a scene.

    blender -b ref.blend --factory-startup --python product_shot.py -- spec.json

spec.json: {"shot": png path, "facts": json path, "colours": {object: rgb}, "label_mm": [z0, z1] or null}
The shot is what a product page shows: one front view from slightly above, white background, a long lens (so a
little perspective, as a photo has), no scale cue. A printed label band can be added as a thin sleeve
for the picture only; it is not part of the measured model. Facts are the hidden key: each object's
size and closed volume, and the whole product's overall size.
"""
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector

spec = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
scene = bpy.context.scene
meshes = sorted((o for o in scene.objects if o.type == "MESH"), key=lambda o: o.name)


def measure(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.transform(o.matrix_world)
    vol = bm.calc_volume(signed=False)
    open_edges = sum(not e.is_manifold for e in bm.edges)
    bm.free()
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = [min(p[i] for p in pts) * 1000 for i in range(3)]
    hi = [max(p[i] for p in pts) * 1000 for i in range(3)]
    return {"min_mm": [round(v, 2) for v in lo], "max_mm": [round(v, 2) for v in hi],
            "size_mm": [round(h - l, 2) for l, h in zip(lo, hi)], "volume_ml": round(vol * 1e6, 1),
            "open_edges": open_edges}


facts = {"objects": {o.name: measure(o) for o in meshes}}
lo = [min(f["min_mm"][i] for f in facts["objects"].values()) for i in range(3)]
hi = [max(f["max_mm"][i] for f in facts["objects"].values()) for i in range(3)]
facts["overall_mm"] = {"width_x": round(hi[0] - lo[0], 2), "depth_y": round(hi[1] - lo[1], 2),
                       "height_z": round(hi[2] - lo[2], 2)}
json.dump(facts, open(spec["facts"], "w", encoding="utf-8"), indent=2)



def smooth_by_angle(o, limit=math.radians(30)):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    sharp = [not e.is_manifold or e.calc_face_angle(0) > limit for e in bm.edges]
    bm.free()
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    attr = o.data.attributes.get("sharp_edge") or o.data.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
    attr.data.foreach_set("value", sharp)


colours = spec.get("colours", {})
for o in meshes:
    o.color = (*colours.get(o.name, (0.8, 0.8, 0.8)), 1)
    smooth_by_angle(o)  # a photo shows no facets, but keeps a carton's creases
if spec.get("label_mm"):  # printed sleeve, picture only: a band just proud of the widest ring inside it
    z0, z1 = (v / 1000 for v in spec["label_mm"])
    body = max(meshes, key=lambda o: o.dimensions.z)
    r = max(math.hypot(v.co.x, v.co.y) for v in body.data.vertices if z0 - 0.01 <= v.co.z <= z1 + 0.01) + 0.0003  # rings sit only at profile points
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=r, depth=z1 - z0, location=(0, 0, (z0 + z1) / 2))
    bpy.context.object.color = (*colours.get("Label", (0.9, 0.9, 0.9)), 1)

scene.render.engine = "BLENDER_WORKBENCH"
for flag in [a for a in dir(scene.render) if a.startswith("use_stamp")]:  # no metadata: it holds local paths
    setattr(scene.render, flag, False)
sh = scene.display.shading
sh.light, sh.color_type = "STUDIO", "OBJECT"
sh.show_cavity, sh.show_object_outline, sh.show_shadows = True, False, False
scene.world = scene.world or bpy.data.worlds.new("World")
scene.world.color = (1, 1, 1)
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x, scene.render.resolution_y = 600, 800
scene.render.film_transparent = False

h, w = hi[2] - lo[2], hi[0] - lo[0]
cam_data = bpy.data.cameras.new("Shot")
cam_data.lens, cam_data.sensor_fit, cam_data.sensor_height = 100, "VERTICAL", 24
frame = max(h / 0.85, w / 0.85 * 800 / 600) / 1000  # product fills about 85% of the frame
dist = frame * cam_data.lens / cam_data.sensor_height
cam = bpy.data.objects.new("Shot", cam_data)
scene.collection.objects.link(cam)
TILT = math.radians(8)  # product shots look slightly down, which shows a lid or a gable roof
cam.location = ((lo[0] + hi[0]) / 2000, -dist * math.cos(TILT), (lo[2] + hi[2]) / 2000 + dist * math.sin(TILT))
cam.rotation_euler = (math.pi / 2 - TILT, 0, 0)
cam_data.clip_start, cam_data.clip_end = dist * 0.1, dist * 10
scene.camera = cam
scene.render.filepath = spec["shot"]
bpy.ops.render.render(write_still=True)
