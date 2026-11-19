"""Reference model for p03, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Bottle, collar and dip tube are lathes of closed (r, z) profiles; the actuator is a lathe with the
nozzle unioned on and the outlet bore cut. VARIANT selects deliberately broken versions.
"""
import math

import bmesh
import bpy

from geom import MM, boolean, cylinder, lathe

VARIANT = globals().get("VARIANT", "good")


def shoulder(r0, z0, r1, z1, n=12):
    return [(r1 + (r0 - r1) * (1 + math.cos(math.pi * k / n)) / 2, z0 + (z1 - z0) * k / n)
            for k in range(1, n)]


def bottle():
    outer = [(0, 0), (25, 0), (25, 120)] + shoulder(25, 120, 12, 130) + [(12, 130), (12, 145)]
    if VARIANT == "solid_bottle":
        prof = outer + [(0, 145)]
    else:
        inner = [(r - 1.5, z - 1.5) for r, z in shoulder(25, 120, 12, 130)]
        prof = outer + [(10.5, 145), (10.5, 128.5)] + inner[::-1] + [(23.5, 118.5), (23.5, 1.5), (0, 1.5)]
    return lathe("Bottle", [(r * MM, z * MM) for r, z in prof], seg=96)


def collar():
    z0 = 131 if VARIANT == "collar_low" else 132
    d = z0 - 132
    prof = [(5, 147 + d), (15, 147 + d), (15, z0), (12.2, z0), (12.2, 145.2 + d), (5, 145.2 + d)]
    return lathe("Collar", [(r * MM, z * MM) for r, z in prof], seg=96, closed=True)


def actuator():
    prof = [(0, 135), (4, 135), (4, 155), (11, 155), (11, 175), (0, 175)]
    act = lathe("Actuator", [(r * MM, z * MM) for r, z in prof], seg=64)
    sign = -1 if VARIANT == "nozzle_left" else 1
    start = 12 if VARIANT == "loose_nozzle" else 0
    noz = cylinder("Nozzle", 3 * MM, start * MM, 30 * MM, 0.0, 168 * MM, seg=40, axis="X")
    if sign < 0:
        noz.data.transform(__import__("mathutils").Matrix.Scale(-1, 4, (1, 0, 0)))
        noz.data.flip_normals()
    if VARIANT == "loose_nozzle":  # a separate shell joined into the same mesh, not fused
        bm = bmesh.new()
        bm.from_mesh(act.data)
        bm.from_mesh(noz.data)
        bm.to_mesh(act.data)
        bm.free()
        bpy.data.objects.remove(noz, do_unlink=True)
    else:
        boolean(act, noz, "UNION")
    if VARIANT != "no_bore":
        bore = cylinder("Bore", 1 * MM, 20 * MM, 31 * MM, 0.0, 168 * MM, seg=24, axis="X")
        if sign < 0:
            bore.data.transform(__import__("mathutils").Matrix.Scale(-1, 4, (1, 0, 0)))
            bore.data.flip_normals()
        boolean(act, bore, "DIFFERENCE")
    return act


def dip_tube():
    top = 137 if VARIANT == "long_tube" else 134.5
    if VARIANT == "solid_tube":
        prof = [(0, 3), (3, 3), (3, top), (0, top)]
        return lathe("DipTube", [(r * MM, z * MM) for r, z in prof], seg=32)
    prof = [(2, top), (3, top), (3, 3), (2, 3)]
    return lathe("DipTube", [(r * MM, z * MM) for r, z in prof], seg=32, closed=True)


bottle()
collar()
actuator()
dip_tube()
