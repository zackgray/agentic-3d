"""Helpers for the layout (l..) reference models. Runs inside Blender, next to geom.py.

Layout tasks place many simple parts, so these build a part once at the origin and then move it in
mesh data, keeping every object at identity transforms.
"""
import math

from mathutils import Matrix

from geom import MM, loft


def flat_circle(r, d, n=64):
    """Convex contour of a circle of radius r with a flat chord at x = d facing +X, counter-clockwise.
    The closing edge (last point back to the first) is the flat."""
    a0 = math.acos(d / r)
    return [(r * math.cos(a0 + (2 * math.pi - 2 * a0) * k / n), r * math.sin(a0 + (2 * math.pi - 2 * a0) * k / n))
            for k in range(n + 1)]


def flat_prism(name, r, d, z0, z1, n=64):
    """A vertical cylinder of radius r from z0 to z1 with a full-height flat at distance d, facing +X."""
    pts = flat_circle(r, d, n)
    return loft(name, [(pts, z0), (pts, z1)])


def place(obj, x=0.0, y=0.0, z=0.0, rot_deg=0.0):
    """Rotate about the world Z axis (degrees), then translate, in mesh data."""
    obj.data.transform(Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot_deg), 4, "Z"))
    return obj


def radial(radius_mm, angle_deg):
    """(x, y) in metres of a point at radius_mm and angle_deg (from +X, counter-clockwise)."""
    a = math.radians(angle_deg)
    return radius_mm * MM * math.cos(a), radius_mm * MM * math.sin(a)
