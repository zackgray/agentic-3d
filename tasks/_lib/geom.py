"""Geometry helpers for hand-built reference models. Runs inside Blender (bpy, bmesh).

Everything is built in world coordinates in metres, with transforms left at identity, so a
reference model meets the "transforms applied" rule by construction. verify_checks puts this
folder on sys.path before running a task's reference.py.
"""
import math

import bmesh
import bpy
from mathutils import Matrix

MM = 0.001


def to_object(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _bridge(bm, a, b, seg):
    for i in range(seg):
        j = (i + 1) % seg
        if len(a) == 1:
            bm.faces.new((a[0], b[j], b[i]))
        elif len(b) == 1:
            bm.faces.new((a[i], a[j], b[0]))
        else:
            bm.faces.new((a[i], a[j], b[j], b[i]))


def lathe(name, profile, seg=96, closed=False, radial=None):
    """Revolve a (r, z) profile about Z. r == 0 marks a pole. closed=True joins the last ring to
    the first, for profiles that are a closed loop with no poles (tubes, rings)."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r == 0:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            rr = radial(t, z, r) if radial else r
            ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        rings.append(ring)
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        _bridge(bm, a, b, seg)
    return to_object(name, bm)


def rounded_rect(hx, hy, r, n=16):
    """Points of a rounded rectangle centred on the origin, counter-clockwise, 4 * n + 4 points."""
    pts = []
    for cx, cy, a0 in ((hx - r, hy - r, 0), (-hx + r, hy - r, 90), (-hx + r, -hy + r, 180),
                       (hx - r, -hy + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def loft(name, layers):
    """Stack of convex closed contours [(points, z), ...] with equal point counts, bottom to top,
    capped at both ends by a fan to the contour's centre. Watertight by construction."""
    bm = bmesh.new()
    seg = len(layers[0][0])
    first, last = layers[0], layers[-1]
    rings = [[bm.verts.new((0.0, 0.0, first[1]))]]
    for pts, z in layers:
        rings.append([bm.verts.new((x, y, z)) for x, y in pts])
    rings.append([bm.verts.new((0.0, 0.0, last[1]))])
    for a, b in zip(rings, rings[1:]):
        _bridge(bm, a, b, seg)
    return to_object(name, bm)


def box(name, lo, hi):
    bm = bmesh.new()
    verts = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    size = [h - l for l, h in zip(lo, hi)]
    centre = [(l + h) / 2 for l, h in zip(lo, hi)]
    bmesh.ops.scale(bm, vec=size, verts=verts)
    bmesh.ops.translate(bm, vec=centre, verts=verts)
    return to_object(name, bm)


def cylinder(name, radius, z0, z1, x=0.0, y=0.0, seg=64, axis="Z"):
    """A closed cylinder along Z from z0 to z1 at (x, y); axis='X' lays it along +X instead, with
    z0..z1 then read as the x range and (x, y) as the (y, z) of its axis."""
    obj = lathe(name, [(0, z0), (radius, z0), (radius, z1), (0, z1)], seg=seg)
    if axis == "X":
        obj.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))  # +Z -> +X
        obj.data.transform(Matrix.Translation((0.0, x, y)))
    else:
        obj.data.transform(Matrix.Translation((x, y, 0.0)))
    return obj


def boolean(target, cutter, op):
    """Apply a boolean (DIFFERENCE / UNION / INTERSECT) to target's mesh data and delete cutter."""
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation, mod.object, mod.solver = op, cutter, "EXACT"
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.remove(mod)
    old, target.data = target.data, new
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def rename(obj, name):
    obj.name = name
    obj.data.name = name
    return obj
