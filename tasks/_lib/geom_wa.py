"""Reference helpers for the held-out hard-surface tasks w01-w02 (heldout4/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity. Arguments
are in millimetres unless noted.
"""
import math

from mathutils import Matrix, Vector

from geom import MM, boolean, cylinder, lathe, loft, rounded_rect

__all__ = ["MM", "arc", "lathe_mm", "polar_holes", "rr_loft", "axis_cylinder"]


def arc(cx, cz, r, a0, a1, n):
    """n + 1 points (r, z) on a circular arc about (cx, cz) from angle a0 to a1 (degrees), ends included."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def lathe_mm(name, prof, seg=96):
    """lathe() with the (r, z) profile in millimetres."""
    return lathe(name, [(r * MM, z * MM) for r, z in prof], seg=seg)


def polar_holes(target, count, radius, start_deg, r_hole, z0, z1, seg=48, phase=0.0):
    """Subtract count vertical round holes of radius r_hole, z0..z1, centred on a circle of the
    given radius about the Z axis, the first at start_deg (from +X towards +Y). phase (degrees)
    turns each cutter about its own axis, to keep its vertices off edges of the target."""
    for k in range(count):
        t = math.radians(start_deg + 360.0 * k / count)
        cut = cylinder("Hole", r_hole * MM, z0 * MM, z1 * MM, seg=seg)
        cut.data.transform(Matrix.Translation((radius * MM * math.cos(t), radius * MM * math.sin(t), 0.0))
                           @ Matrix.Rotation(math.radians(phase), 4, "Z"))
        boolean(target, cut, "DIFFERENCE")
    return target


def rr_loft(name, sections, n=16):
    """Loft through rounded-rectangle sections [(hx, hy, r, z), ...] (mm), bottom to top."""
    return loft(name, [(rounded_rect(hx * MM, hy * MM, r * MM, n=n), z * MM) for hx, hy, r, z in sections])


def axis_cylinder(name, radius, point, direction, s0, s1, seg=48):
    """Closed cylinder of the given radius whose axis passes through point (mm) along direction,
    from axial distance s0 to s1 (mm) measured from point. End caps are square to the axis."""
    d = Vector(direction).normalized()
    obj = lathe(name, [(0, s0 * MM), (radius * MM, s0 * MM), (radius * MM, s1 * MM), (0, s1 * MM)], seg=seg)
    rot = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    obj.data.transform(Matrix.Translation(Vector(point) * MM) @ rot)
    obj.data.update()
    return obj
