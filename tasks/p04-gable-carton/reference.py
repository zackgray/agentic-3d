"""Reference model for p04, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The body and roof are one closed solid made from a side profile extruded along X; the fin is a box
unioned onto the ridge. VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

import bmesh
from mathutils import Matrix

from geom import MM, boolean, box, rename, to_object

VARIANT = globals().get("VARIANT", "good")


def prism(name, profile_yz, x0, x1):
    """Extrude a convex (y, z) polygon along X from x0 to x1 into a closed solid."""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in profile_yz]
    b = [bm.verts.new((x1, y, z)) for y, z in profile_yz]
    n = len(profile_yz)
    bm.faces.new(a)
    bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return to_object(name, bm)


ridge = 195 * MM if VARIANT == "flat_top" else 230 * MM
body = prism("Carton", [(-35 * MM, 0), (35 * MM, 0), (35 * MM, 195 * MM), (0, ridge),
                        (-35 * MM, 195 * MM)], -35 * MM, 35 * MM)

if VARIANT != "flat_top":
    half = 2 * MM if VARIANT == "thick_fin" else 1 * MM
    bottom = 231 * MM if VARIANT == "gap_fin" else 225 * MM
    fin = box("Fin", (-35 * MM, -half, bottom), (35 * MM, half, 242 * MM))
    if VARIANT == "gap_fin":  # left as a separate floating shell joined into the same mesh
        bm = bmesh.new()
        bm.from_mesh(body.data)
        bm.from_mesh(fin.data)
        bm.to_mesh(body.data)
        bm.free()
        import bpy
        bpy.data.objects.remove(fin, do_unlink=True)
    else:
        boolean(body, fin, "UNION")

if VARIANT == "ridge_along_y":
    body.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))
rename(body, "Carton")
