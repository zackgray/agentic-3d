"""Reference helpers for the held-out multi-step tasks z07-z08 (heldout3/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

import bmesh
from mathutils import Matrix

from geom import MM, loft, rounded_rect, to_object


def rr_loft(name, sections, n=16):
    """Loft through rounded-rectangle sections [(hx, hy, r, z), ...] in millimetres, bottom to top.
    Corresponding points are joined by straight lines, so half-widths and radius vary linearly."""
    return loft(name, [(rounded_rect(hx * MM, hy * MM, r * MM, n=n), z * MM) for hx, hy, r, z in sections])


def stadium_xz(hx, z_lo, z_hi, k=16):
    """A vertical stadium in the X-Z plane (mm): width 2 * hx, from z_lo to z_hi, round ends of
    radius hx. Counter-clockwise points, no duplicates."""
    pts = []
    for i in range(k + 1):  # top arc, 0 -> 180 degrees
        a = math.pi * i / k
        pts.append((hx * math.cos(a), z_hi - hx + hx * math.sin(a)))
    for i in range(k + 1):  # bottom arc, 180 -> 360 degrees
        a = math.pi + math.pi * i / k
        pts.append((hx * math.cos(a), z_lo + hx + hx * math.sin(a)))
    return pts


def prism_y(name, pts_xz, y0, y1):
    """Closed prism of a convex X-Z contour (mm) extruded along Y from y0 to y1 (mm)."""
    bm = bmesh.new()
    seg = len(pts_xz)
    cx = sum(p[0] for p in pts_xz) / seg
    cz = sum(p[1] for p in pts_xz) / seg
    rings = [[bm.verts.new((cx * MM, y0 * MM, cz * MM))]]
    for y in (y0, y1):
        rings.append([bm.verts.new((x * MM, y * MM, z * MM)) for x, z in pts_xz])
    rings.append([bm.verts.new((cx * MM, y1 * MM, cz * MM))])
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    return to_object(name, bm)


def z_to_y(obj, z_axis_mm):
    """Turn a mesh built along +Z (about the origin) to run along +Y, its axis at height z_axis_mm."""
    obj.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))  # +Z -> +Y
    obj.data.transform(Matrix.Translation((0.0, 0.0, z_axis_mm * MM)))
    return obj
