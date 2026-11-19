"""Reference helpers for the held-out revision tasks z05-z06 (heldout3/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity. Arguments
are in millimetres unless noted.
"""
from mathutils import Matrix

from geom import MM, boolean, cylinder, loft, rename, rounded_rect
from geom_r import FACE_MINUS_Y, fillet_slab, slab, xform

__all__ = ["MM", "hub", "planter", "remove"]


def remove(name):
    import bpy
    obj = bpy.data.objects.get(name)
    if obj is not None:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def hub(ports, port_w=14.0, top_fillet=4.0, button=True, n=16):
    """z05's charging hub: a solid rounded slab 140 x 70 mm (x -70..70, y -35..35), z 0..28, 10 mm
    plan corners, its top perimeter edge filleted top_fillet mm (0 = sharp). Port recesses in the
    front (-Y) face: rounded rectangles port_w wide (X) x 7 mm tall (Z), 1.5 mm corners, centred at
    z = 12 and at each x in ports, 15 mm deep (back wall at y = -20). Optional button recess on top:
    12 mm across, 1 mm deep, centred at (45, 0). n = segments per quarter circle."""
    if top_fillet > 0:
        body = fillet_slab("Hub", 70 * MM, 35 * MM, 10 * MM, 0.0, 28 * MM, top_fillet * MM,
                           steps=min(n, 12), n=n)
    else:
        body = slab("Hub", 70 * MM, 35 * MM, 10 * MM, 0.0, 28 * MM, n=n)
    for x in ports:
        # slab along +Z, then (u, v, h) -> (u, -h, v): h 20..36 becomes y -36..-20.
        cut = slab("Port", port_w / 2 * MM, 3.5 * MM, 1.5 * MM, 20 * MM, 36 * MM, n=8)
        xform(cut, FACE_MINUS_Y)
        xform(cut, Matrix.Translation((x * MM, 0.0, 12 * MM)))
        boolean(body, cut, "DIFFERENCE")
    if button:
        boolean(body, cylinder("Button", 6 * MM, 27 * MM, 29 * MM, 45 * MM, 0.0, seg=4 * n), "DIFFERENCE")
    return rename(body, "Hub")


def _outline(hx, hy, r, n=16):
    if r <= 0:
        return [(hx, hy), (-hx, hy), (-hx, -hy), (hx, -hy)]
    return rounded_rect(hx, hy, r, n)


def planter(r_out=0.0, r_in=0.0, taper=True, holes=True, wall=4.0, n=16):
    """z06's planter: an open-top tapered box, outside 160 x 100 mm at z = 0 growing linearly to
    180 x 120 mm at z = 100. Wall `wall` mm thick measured horizontally (the inside outline is the
    outside one offset inward), floor solid z 0..6. Plan-view corner radii r_out outside and r_in
    inside (0 = sharp). Four 8 mm drain holes through the floor at (+-40, +-20)."""
    top = (90.0, 60.0) if taper else (80.0, 50.0)

    def half(z):  # outside half-sizes at height z (mm)
        f = z / 100.0
        return 80.0 + (top[0] - 80.0) * f, 50.0 + (top[1] - 50.0) * f

    def layer(z, inset, r):
        hx, hy = half(z)
        return [(x * MM, y * MM) for x, y in _outline(hx - inset, hy - inset, r, n)], z * MM

    body = loft("Planter", [layer(0.0, 0.0, r_out), layer(100.0, 0.0, r_out)])
    boolean(body, loft("Cavity", [layer(6.0, wall, r_in), layer(101.0, wall, r_in)]), "DIFFERENCE")
    if holes:
        for sx in (1, -1):
            for sy in (1, -1):
                boolean(body, cylinder("Drain", 4 * MM, -1 * MM, 7 * MM, sx * 40 * MM, sy * 20 * MM, seg=3 * n),
                        "DIFFERENCE")
    return rename(body, "Planter")
