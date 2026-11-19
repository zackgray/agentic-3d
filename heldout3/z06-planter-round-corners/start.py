"""Starting scene for z06 (held out): the approved moulded planter, before the revision.

Runs inside Blender on the empty scene. Planter: an open-top tapered box, outside 160 x 100 mm at
the base (z = 0) growing linearly to 180 x 120 mm at the rim (z = 100), centred on the Z axis. Side
walls 4 mm thick measured horizontally, floor solid z 0..6, four 8 mm drain holes through the floor
at (+-40, +-20). Every edge sharp, the slanted corner edges included.
"""
from geom_zc import MM, planter

planter()


def clean_rim(name="Planter", z=100.0):
    """The cavity boolean leaves the rim top split, with a vertex on the inside edge 2 mm from each
    inside corner. A natural 11 mm bevel of the inside corners slides onto that 2 mm edge and fails
    (independent re-verification, 2026-11-18). Rebuild the rim as four faces seamed at mid-side, so
    no rim edge runs into a corner: a bevel of a slanted corner edge then has the whole side to
    slide along."""
    import math

    import bmesh
    import bpy

    obj = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    at_rim = lambda v: abs(v.co.z - z * MM) < 1e-7
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(at_rim(v) for v in f.verts)], context="FACES_ONLY")
    bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context="EDGES")
    corner = lambda v: (round(abs(v.co.x) / MM, 3) in (90.0, 86.0)) and (round(abs(v.co.y) / MM, 3) in (60.0, 56.0))
    bmesh.ops.dissolve_verts(bm, verts=[v for v in bm.verts if at_rim(v) and not corner(v)])
    rim_edges = [e for e in bm.edges if all(at_rim(v) for v in e.verts)]
    assert len(rim_edges) == 8 and len([v for v in bm.verts if at_rim(v)]) == 8, len(rim_edges)
    bmesh.ops.subdivide_edges(bm, edges=rim_edges, cuts=1)
    rim = [v for v in bm.verts if at_rim(v)]
    ang = lambda v: math.atan2(v.co.y, v.co.x) % (2 * math.pi)
    is_outer = lambda v: round(abs(v.co.x) / MM, 3) == 90.0 or round(abs(v.co.y) / MM, 3) == 60.0
    outer = sorted((v for v in rim if is_outer(v)), key=ang)
    inner = sorted((v for v in rim if not is_outer(v)), key=ang)
    assert len(outer) == 8 and len(inner) == 8
    k0 = 0 if not corner(outer[0]) else 1  # start each face at a mid-side vertex
    for i in range(4):
        a, c, b = (k0 + 2 * i) % 8, (k0 + 2 * i + 1) % 8, (k0 + 2 * i + 2) % 8
        bm.faces.new((outer[a], outer[c], outer[b], inner[b], inner[c], inner[a]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


clean_rim()
