"""Extra reference helpers for the h01-h06 hard-surface tasks. Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, identity transforms.
"""
import math

import bmesh
from mathutils import Matrix

from geom import MM, _bridge, box, loft, to_object


def arc(cx, cz, r, a0, a1, n=12):
    """Points (r, z) of a circular arc in a lathe profile, centre (cx, cz), degrees a0 -> a1."""
    pts = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def slant_cylinder(name, r, z0, ztop, seg=96):
    """Solid cylinder about Z from a flat bottom at z0 up to a top cut by a plane: ztop(x, y) gives
    the plane's height. The top cap fans from the plane point above the axis."""
    bm = bmesh.new()
    bottom_pole = [bm.verts.new((0.0, 0.0, z0))]
    lo, hi = [], []
    for i in range(seg):
        t = 2 * math.pi * i / seg
        x, y = r * math.cos(t), r * math.sin(t)
        lo.append(bm.verts.new((x, y, z0)))
        hi.append(bm.verts.new((x, y, ztop(x, y))))
    top_pole = [bm.verts.new((0.0, 0.0, ztop(0.0, 0.0)))]
    for a, b in ((bottom_pole, lo), (lo, hi), (hi, top_pole)):
        _bridge(bm, a, b, seg)
    return to_object(name, bm)


def ellipse(a, b, seg=96):
    return [(a * math.cos(2 * math.pi * i / seg), b * math.sin(2 * math.pi * i / seg)) for i in range(seg)]


def ellipse_loft(name, sections, seg=96):
    """Loft through elliptical sections [(a, b, z), ...] (a = X semi-axis, b = Y semi-axis)."""
    return loft(name, [(ellipse(a, b, seg), z) for a, b, z in sections])


def rot_box(name, lo, hi, angle_deg):
    """Axis-aligned box lo..hi, then rotated about the world Z axis by angle_deg."""
    obj = box(name, lo, hi)
    obj.data.transform(Matrix.Rotation(math.radians(angle_deg), 4, "Z"))
    return obj


def transform(obj, matrix):
    obj.data.transform(matrix)
    return obj


__all__ = ["MM", "arc", "slant_cylinder", "ellipse", "ellipse_loft", "rot_box", "transform"]
