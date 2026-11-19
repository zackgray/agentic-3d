"""Reference helpers for the held-out tasks z03-z04 (heldout3/). Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

from mathutils import Matrix, Vector

from geom import MM, boolean, cylinder, loft, rounded_rect

# Lays a loft built along +Z along +X instead, mapping (u, v, h) -> (h, u, v): a contour drawn in
# (u, v) becomes a cross-section in the YZ plane, extruded along X.
Z_TO_X_YZ = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def chamfer_slab(name, hx, hy, r, z0, z1, ch, n=16):
    """Rounded-rectangle prism from z0 to z1 whose top perimeter edge carries a 45-degree chamfer of
    size ch (the plan corner radius shrinks with the inset)."""
    def contour(inset):
        return rounded_rect(hx - inset, hy - inset, r - inset, n)
    layers = [(contour(0), z0), (contour(0), z1 - ch)]
    if ch > 0:
        layers.append((contour(ch), z1))
    return loft(name, layers)


def prism_x(name, pts_yz, x0, x1):
    """A prism along X from x0 to x1 whose cross-section is the convex (y, z) polygon pts_yz, given
    counter-clockwise seen from +X."""
    cy = sum(p[0] for p in pts_yz) / len(pts_yz)  # loft fans its caps to (0, 0): centre first
    cz = sum(p[1] for p in pts_yz) / len(pts_yz)
    obj = loft(name, [([(y - cy, z - cz) for y, z in pts_yz], x0), ([(y - cy, z - cz) for y, z in pts_yz], x1)])
    obj.data.transform(Matrix.Translation((0.0, cy, cz)) @ Z_TO_X_YZ)
    return obj


def cyl_axis(name, radius, centre, direction, half_len, seg=64):
    """Closed cylinder of the given radius whose axis passes through centre (metres) along
    direction, extending half_len either side of centre."""
    d = Vector(direction).normalized()
    obj = cylinder(name, radius, -half_len, half_len, seg=seg)
    rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    obj.data.transform(Matrix.Translation(Vector(centre)) @ rot)
    return obj


def bullnose_x(name, y0, y1, z0, z1, x0, x1, n=16):
    """A bar along X: rectangle y0..y1 from z0 up to the springing line, topped by a semicircle of
    diameter y1 - y0, so its highest point is at z1."""
    r = (y1 - y0) / 2
    yc, zc = (y0 + y1) / 2, z1 - r
    pts = [(y0, z0), (y1, z0)]
    for k in range(n + 1):
        a = math.pi * k / n
        pts.append((yc + r * math.cos(a), zc + r * math.sin(a)))
    return prism_x(name, pts, x0, x1)


def blade(name, length, width, r, z0, z1, hole_x, hole_r, angle_deg, hole=True):
    """A flat rounded-rectangle blade in local coordinates: long axis along +X from -hole_x to
    length - hole_x (so the pivot hole is at the local origin), width across Y. Turned by angle_deg
    about the world Z axis through the origin (the pivot)."""
    pts = rounded_rect(length / 2, width / 2, r)
    obj = loft(name, [(pts, z0), (pts, z1)])
    obj.data.transform(Matrix.Translation((length / 2 - hole_x, 0.0, 0.0)))
    if hole:
        boolean(obj, cylinder("Hole", hole_r, z0 - 1 * MM, z1 + 1 * MM, seg=48), "DIFFERENCE")
    obj.data.transform(Matrix.Rotation(math.radians(angle_deg), 4, "Z"))
    return obj
