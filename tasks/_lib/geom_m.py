"""Extra reference helpers for tasks h07, h08, m01-m04. Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from geom import MM, lathe, loft, rounded_rect


def mm_lathe(name, prof_mm, seg=96, closed=False):
    """lathe() with the (r, z) profile given in millimetres."""
    return lathe(name, [(r * MM, z * MM) for r, z in prof_mm], seg=seg, closed=closed)


def cyl_along(name, radius, start, end, seg=32):
    """Closed cylinder between two world points (metres), any direction."""
    a, b = Vector(start), Vector(end)
    length = (b - a).length
    obj = lathe(name, [(0, 0.0), (radius, 0.0), (radius, length), (0, length)], seg=seg)
    rot = Vector((0, 0, 1)).rotation_difference((b - a).normalized()).to_matrix().to_4x4()
    obj.data.transform(Matrix.Translation(a) @ rot)
    return obj


def join(name, objs):
    """Merge several mesh objects into one mesh (no boolean) and delete the inputs."""
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    for o in objs:
        mesh = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(mesh)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def rounded_slab(name, hx, hy, plan_r, z0, z1, r_bot=0.0, r_top=0.0, n=12, plan_n=16):
    """Loft of a rounded rectangle from z0 to z1 whose bottom and/or top edges are rounded over
    with radius r_bot / r_top (the plan radius shrinks with the inset through each band)."""
    def contour(inset):
        return rounded_rect(hx - inset, hy - inset, max(0.01 * MM, plan_r - inset), n=plan_n)

    layers = []
    if r_bot > 0:
        for k in range(n, 0, -1):
            phi = math.pi / 2 * k / n
            layers.append((contour(r_bot * (1 - math.cos(phi))), z0 + r_bot - r_bot * math.sin(phi)))
    layers.append((contour(0), z0 + r_bot))
    layers.append((contour(0), z1 - r_top))
    if r_top > 0:
        for k in range(1, n + 1):
            phi = math.pi / 2 * k / n
            layers.append((contour(r_top * (1 - math.cos(phi))), z1 - r_top + r_top * math.sin(phi)))
    return loft(name, layers)


def clean(obj, dist=1e-7):
    """Dissolve zero-area slivers an exact boolean can leave behind (e.g. many radial cutters)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
    bm.to_mesh(obj.data)
    bm.free()
    return obj
