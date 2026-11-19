"""Reference helpers for the held-out tasks x05-x08 (heldout/). Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import bpy

from geom import MM, box, boolean, cylinder, rename
from geom_m import rounded_slab


def remove(name):
    obj = bpy.data.objects.get(name)
    if obj is not None:
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def remote(pockets, edge_r=3.0):
    """x07's remote body: 45 x 160 x 18 mm, 10 mm plan corners, top perimeter edge rounded with
    edge_r, a battery-door recess 30 x 60 x 1 mm in the underside, and round 3 mm-deep pockets in
    the top at [(y_mm, diameter_mm), ...] on the X = 0 line."""
    body = rounded_slab("Remote", 22.5 * MM, 80 * MM, 10 * MM, 0.0, 18 * MM, r_top=edge_r * MM, n=12)
    boolean(body, box("Recess", (-15 * MM, -60 * MM, -1 * MM), (15 * MM, 0.0, 1 * MM)), "DIFFERENCE")
    for y, d in pockets:
        boolean(body, cylinder("Pocket", d / 2 * MM, 15 * MM, 19 * MM, 0.0, y * MM, seg=64), "DIFFERENCE")
    return rename(body, "Remote")


def remote_button(y, d, z0=15.5, z1=20.0):
    return rename(cylinder("Button", d / 2 * MM, z0 * MM, z1 * MM, 0.0, y * MM, seg=64), "Button")
