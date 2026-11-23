"""The outside of one object, probed by rays: the scored spec-first arm's shape measure (rig/spec_arm.py).

    blender -b scene.blend --factory-startup --python outer_profile.py -- out.json Object

At each of LEVELS heights, RAYS horizontal rays fire from outside toward the Z axis and stop at the
first surface. The hits make a polygon whose area is the outside cross-section there; summed over
the height they give the outside volume. A hollow container and a solid one with the same outside
measure the same, which is the point: wall thickness is a modelling convention, not the shape.
"""
import json
import math
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LEVELS, RAYS = 120, 32

out_path, name = sys.argv[sys.argv.index("--") + 1:][:2]
obj = bpy.data.objects.get(name)
if obj is None or obj.type != "MESH":
    json.dump({"missing": name}, open(out_path, "w"))
    sys.exit(0)

bm = bmesh.new()
bm.from_object(obj, bpy.context.evaluated_depsgraph_get())
bm.transform(obj.matrix_world)
tree = BVHTree.FromBMesh(bm)
zs = [v.co.z for v in bm.verts]
z0, z1 = min(zs), max(zs)
far = 2 * max(max(abs(v.co.x), abs(v.co.y)) for v in bm.verts) + 1.0
dz = (z1 - z0) / LEVELS
step = 2 * math.pi / RAYS

levels = []
for i in range(LEVELS):
    z = z0 + (i + 0.5) * dz
    radii = []
    for j in range(RAYS):
        d = Vector((math.cos(j * step), math.sin(j * step), 0.0))
        hit = tree.ray_cast(d * far + Vector((0, 0, z)), -d, far)[0]
        radii.append((hit.xy.length if hit is not None else 0.0))
    area = 0.5 * sum(radii[j] * radii[(j + 1) % RAYS] for j in range(RAYS)) * math.sin(step)
    levels.append({"z_mm": round(z * 1000, 2), "area_mm2": round(area * 1e6, 2),
                   "r_eq_mm": round(math.sqrt(area / math.pi) * 1000, 3)})

json.dump({"object": name, "z0_mm": round(z0 * 1000, 2), "z1_mm": round(z1 * 1000, 2),
           "outer_ml": round(sum(l["area_mm2"] for l in levels) * dz * 1000 / 1000, 2),
           "enclosed_ml": round(abs(bm.calc_volume(signed=True)) * 1e6, 2), "levels": levels},
          open(out_path, "w"))
