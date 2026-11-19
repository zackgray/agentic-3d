"""Extra reference helpers for the r.. revision tasks. Runs inside Blender (bpy, bmesh).

Builds on geom.py: rounded slabs in any orientation, mesh transforms, and joining two meshes
without a boolean (for the "parts merged but not fused" variants).
"""
import math

import bmesh
import bpy
from mathutils import Matrix

from geom import MM, box, loft, rounded_rect

# Maps a loft built along +Z into one standing proud of the -Y face: (u, v, h) -> (u, -h, v).
FACE_MINUS_Y = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
# Lays a lathe built about +Z along +X instead: (x, y, z) -> (z, y, -x).
Z_TO_X = Matrix.Rotation(math.pi / 2, 4, "Y")


def xform(obj, matrix):
    obj.data.transform(matrix)
    obj.data.update()
    return obj


def slab(name, hx, hy, r, z0, z1, n=16):
    """A rounded-rectangle prism centred on the Z axis, from z0 to z1 (all in metres)."""
    pts = rounded_rect(hx, hy, r, n)
    return loft(name, [(pts, z0), (pts, z1)])


def fillet_slab(name, hx, hy, r, z0, z1, fr, steps=12, n=16):
    """A rounded-rectangle prism whose top perimeter edge carries a rolling-ball fillet of radius fr
    (fr < r). Each layer is the outline offset inward, so the fillet follows the corner radii."""
    layers = [(rounded_rect(hx, hy, r, n), z0), (rounded_rect(hx, hy, r, n), z1 - fr)]
    for k in range(1, steps + 1):
        a = math.pi / 2 * k / steps
        inset = fr * (1 - math.cos(a))
        layers.append((rounded_rect(hx - inset, hy - inset, r - inset, n), z1 - fr + fr * math.sin(a)))
    return loft(name, layers)


def rib_box(name, r0, r1, half_w, z0, z1, angle_deg):
    """A radial rib: a box from radius r0 to r1, half_w either side, z0..z1, turned to angle_deg."""
    obj = box(name, (r0, -half_w, z0), (r1, half_w, z1))
    return xform(obj, Matrix.Rotation(math.radians(angle_deg), 4, "Z"))


def merge(target, other):
    """Join other's mesh into target with no boolean (two shells), and delete other."""
    bm = bmesh.new()
    bm.from_mesh(target.data)
    bm.from_mesh(other.data)
    bm.to_mesh(target.data)
    bm.free()
    bpy.data.objects.remove(other, do_unlink=True)
    return target


def remove(name):
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)


__all__ = ["MM", "FACE_MINUS_Y", "Z_TO_X", "xform", "slab", "fillet_slab", "rib_box", "merge", "remove"]
