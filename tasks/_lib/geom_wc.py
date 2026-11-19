"""Reference helpers for the held-out revision tasks w05-w06 (heldout4/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity. Arguments
are in millimetres unless noted.
"""
import math

from geom import MM, boolean, cylinder, lathe, rename

__all__ = ["MM", "arc", "brush_holder", "bud_vase", "merge_close", "remove"]


def remove(name):
    import bpy
    obj = bpy.data.objects.get(name)
    if obj is not None:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def arc(cr, cz, r, a0, a1, steps):
    """Points (r, z) in mm on a profile arc about (cr, cz), from angle a0 to a1 in degrees, ends included."""
    return [(cr + r * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]


def merge_close(obj, dist=1e-6):
    """Weld vertices closer than dist (m) and drop the zero-length edges the exact boolean can leave."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=dist)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return obj


def brush_holder(angles, pitch=28.0, hole_r=8.0, floor=12.0, centre=True, round_r=4.0, n=16, phase=0.5):
    """w05's makeup-brush holder: a solid turned puck, 90 mm across (r 45), z 0..50, its top outer
    edge rounded round_r mm (0 = sharp). A 20 mm centre well (r 10) and round brush holes of radius
    hole_r on a pitch circle of radius `pitch`, one at each angle in `angles` (degrees from +X,
    counter-clockwise), all with flat floors at z = floor. n = segments per quarter circle.

    phase turns the lathe by that fraction of a segment. With 0, the long radial edges of the top
    face lie on the axes, exactly through the cutters' outermost vertices, and the exact boolean
    leaves coincident vertices there; the starting scene is built with the default 0.5."""
    prof = [(0.0, 0.0), (45.0, 0.0)]
    if round_r > 0:
        prof += arc(45.0 - round_r, 50.0 - round_r, round_r, 0, 90, min(n, 8))
    else:
        prof += [(45.0, 50.0)]
    if centre:
        prof += [(10.0, 50.0), (10.0, floor), (0.0, floor)]
    else:
        prof += [(0.0, 50.0)]
    body = lathe("Holder", [(r * MM, z * MM) for r, z in prof], seg=4 * n)
    if phase:
        from mathutils import Matrix
        body.data.transform(Matrix.Rotation(phase * math.pi / (2 * n), 4, "Z"))
    for a in angles:
        t = math.radians(a)
        cut = cylinder("Hole", hole_r * MM, floor * MM, 52 * MM, pitch * math.cos(t) * MM,
                       pitch * math.sin(t) * MM, seg=4 * n)
        boolean(body, cut, "DIFFERENCE")
    return rename(body, "Holder")


def bud_vase(shoulder_z=60.0, shoulder_r=36.0, neck_z=110.0, top=150.0, bore=True, lip=True, n=16):
    """w06's turned bud vase, solid: a foot ring r 30 from z 0 to 8, a step in to r 24, a straight
    cone out to the shoulder (shoulder_r at shoulder_z), a straight cone in to the neck (r 12 at
    neck_z), a straight neck up to the top. The outer lip edge is rounded 1.5 mm. A 12 mm bore
    (r 6) runs from the top down to z = 40 with a flat floor. n = segments per quarter circle."""
    prof = [(0.0, 0.0), (30.0, 0.0), (30.0, 8.0), (24.0, 8.0), (shoulder_r, shoulder_z), (12.0, neck_z)]
    if lip:
        prof += arc(10.5, top - 1.5, 1.5, 0, 90, 4)
    else:
        prof += [(12.0, top)]
    if bore:
        prof += [(6.0, top), (6.0, 40.0), (0.0, 40.0)]
    else:
        prof += [(0.0, top)]
    return lathe("Vase", [(r * MM, z * MM) for r, z in prof], seg=4 * n)
