"""Reference helpers for the held-out tasks z01-z02 (heldout3/). Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

from mathutils import Matrix

from geom import loft

__all__ = ["prism_x", "d_outline"]

# Maps a loft built along +Z onto +X: (a, b, h) -> (h, a, b), so loft points (a, b) read as (y, z).
_Z_TO_X = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def prism_x(name, yz_pts, x0, x1):
    """A prism along X from x0 to x1 whose section is the convex polygon yz_pts [(y, z), ...] given
    counter-clockwise seen from +X (metres)."""
    cy = sum(p[0] for p in yz_pts) / len(yz_pts)  # loft fans its caps from (0, 0): centre the section
    cz = sum(p[1] for p in yz_pts) / len(yz_pts)
    pts = [(y - cy, z - cz) for y, z in yz_pts]
    obj = loft(name, [(pts, x0), (pts, x1)])
    obj.data.transform(Matrix.Translation((0.0, cy, cz)) @ _Z_TO_X)
    obj.data.update()
    return obj


def d_outline(r, flat_x, seg=96):
    """Counter-clockwise outline of a D: a circle of radius r about the origin cut off by the flat
    line x = flat_x (0 < flat_x < r). The flat faces +X."""
    a = math.acos(flat_x / r)
    pts = []
    for i in range(seg + 1):
        t = a + (2 * math.pi - 2 * a) * i / seg
        pts.append((r * math.cos(t), r * math.sin(t)))
    return pts
