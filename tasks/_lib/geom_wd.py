"""Reference helpers for the held-out multi-step tasks w07-w08 (heldout4/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

import bmesh
from mathutils import Matrix

from geom import MM, lathe, loft, to_object


def polygon(n, across_flats, rot_deg=0.0):
    """Regular n-gon centred on the origin (metres in, metres out), counter-clockwise. With
    rot_deg = 0 one flat faces +X (an octagon then has flats facing +-X, +-Y and the diagonals)."""
    r = across_flats / 2 / math.cos(math.pi / n)
    return [(r * math.cos(math.pi / n + 2 * math.pi * k / n + math.radians(rot_deg)),
             r * math.sin(math.pi / n + 2 * math.pi * k / n + math.radians(rot_deg))) for k in range(n)]


def oct_loft(name, sections, rot_deg=0.0):
    """Loft of regular octagons [(across_flats_mm, z_mm), ...], bottom to top."""
    return loft(name, [(polygon(8, f * MM, rot_deg), z * MM) for f, z in sections])


def lay_x(obj, y_mm, z_mm):
    """Turn a mesh built about the Z axis so that axis runs along +X, at (y, z) in millimetres."""
    obj.data.transform(Matrix.Rotation(math.pi / 2, 4, "Y"))  # +Z -> +X
    obj.data.transform(Matrix.Translation((0.0, y_mm * MM, z_mm * MM)))
    return obj


def lathe_x(name, prof_mm, y_mm, z_mm, seg=96, closed=False):
    """Revolve an (r, x) profile in millimetres about an X-parallel axis at (y, z)."""
    obj = lathe(name, [(r * MM, x * MM) for r, x in prof_mm], seg=seg, closed=closed)
    return lay_x(obj, y_mm, z_mm)


def prism_x(name, pts_mm, x0, x1, y_mm, z_mm):
    """Convex contour pts (a, b) in mm about the origin, extruded from x0 to x1 (mm); a becomes
    world -Z offset and b world +Y offset under lay_x, so pass contours symmetric where it matters."""
    obj = loft(name, [([(a * MM, b * MM) for a, b in pts_mm], x * MM) for x in (x0, x1)])
    return lay_x(obj, y_mm, z_mm)


def strip_plate(name, xs, tops, z_bot, y0, y1):
    """Plate of constant thickness in Y (y0..y1, mm) whose outline in the X-Z plane is x-monotone:
    a flat bottom at z_bot and a top edge through (xs[i], tops[i]) (mm), e.g. a serrated edge."""
    bm = bmesh.new()
    rows = []
    for y in (y0, y1):
        rows.append(([bm.verts.new((x * MM, y * MM, z_bot * MM)) for x in xs],
                     [bm.verts.new((x * MM, y * MM, t * MM)) for x, t in zip(xs, tops)]))
    (fb, ft), (bb, bt) = rows
    n = len(xs)
    for i in range(n - 1):
        j = i + 1
        bm.faces.new((fb[i], fb[j], ft[j], ft[i]))
        bm.faces.new((bb[i], bt[i], bt[j], bb[j]))
        bm.faces.new((fb[i], bb[i], bb[j], fb[j]))
        bm.faces.new((ft[i], ft[j], bt[j], bt[i]))
    bm.faces.new((fb[0], ft[0], bt[0], bb[0]))
    bm.faces.new((fb[-1], bb[-1], bt[-1], ft[-1]))
    return to_object(name, bm)
