"""Reference revision for w05 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

Four brush holes become six, evenly spaced on the same 28 mm pitch circle, one still on +X: 0, 60,
120, 180, 240, 300 degrees. Hole size and depth unchanged; the old holes at 90 and 270 are filled.
The centre well and the rounded top edge stay. VARIANT selects deliberately broken revisions.
"""
import math

import bpy

from geom import MM, boolean, cylinder
from geom_wc import brush_holder, merge_close, remove

VARIANT = globals().get("VARIANT", "good")
SIX = [0, 60, 120, 180, 240, 300]


def at(a, r=28.0):
    t = math.radians(a)
    return r * math.cos(t) * MM, r * math.sin(t) * MM


if VARIANT in ("natural", "natural_plug"):
    # The edits an agent would most likely make on the existing mesh, keeping everything else.
    # natural: delete the two old holes' wall and floor faces and cap each rim loop with one face.
    # natural_plug: union an oversize plug flush with the top into each old hole. Blender's exact
    # solver leaves the old rim's vertices doubled after a flush union (it does so on a primitive
    # cylinder too), so this route needs the merge the prompt asks for after each union.
    # Both then cut the four new holes with 32-segment cylinders.
    import bmesh
    body = bpy.data.objects["Holder"]
    if VARIANT == "natural":
        bm = bmesh.new()
        bm.from_mesh(body.data)
        old = [at(90), at(270)]
        inside = lambda f: any(math.hypot(f.calc_center_median().x - x, f.calc_center_median().y - y) < 8.1 * MM
                               for x, y in old) and f.calc_center_median().z < 49.9 * MM
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if inside(f)], context="FACES")
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
        bm.to_mesh(body.data)
        bm.free()
    else:
        for a in (90, 270):
            x, y = at(a)
            boolean(body, cylinder("Plug", 8.5 * MM, 11 * MM, 50 * MM, x, y, seg=32), "UNION")
            merge_close(body)
    for a in (60, 120, 240, 300):
        x, y = at(a)
        boolean(body, cylinder("Hole", 8 * MM, 12 * MM, 55 * MM, x, y, seg=32), "DIFFERENCE")
elif VARIANT != "unchanged":
    angles, kwargs = SIX, {}
    if VARIANT == "old_left_open":      # new holes cut, the old 90 / 270 holes never filled
        angles = SIX + [90, 270]
    elif VARIANT == "rotated":          # six evenly spaced, but none on +X (started at 30 degrees)
        angles = [30, 90, 150, 210, 270, 330]
    elif VARIANT == "wrong_circle":     # pitch radius misread as 30 mm
        kwargs["pitch"] = 30.0
    elif VARIANT == "hole_small":       # holes misread as 14 mm across
        kwargs["hole_r"] = 7.0
    elif VARIANT == "through":          # holes cut right through the base
        kwargs["floor"] = -1.0
    elif VARIANT == "centre_lost":      # rebuilt without the centre well
        kwargs["centre"] = False
    elif VARIANT == "round_lost":       # rebuilt with a sharp top edge
        kwargs["round_r"] = 0.0
    elif VARIANT == "coarse":           # valid: 24 segments per circle everywhere, axis-aligned (must pass)
        kwargs.update(n=6, phase=0)
    remove("Holder")
    if VARIANT == "through":
        # the lathe keeps the well floor at 12; only the brush holes go through
        body = brush_holder([], **{k: v for k, v in kwargs.items() if k != "floor"})
        for a in angles:
            x, y = at(a)
            boolean(body, cylinder("Hole", 8 * MM, -2 * MM, 52 * MM, x, y, seg=64), "DIFFERENCE")
    else:
        body = brush_holder(angles, **kwargs)
        if VARIANT == "coarse":  # axis-aligned top edges leave coincident verts; merged as the prompt asks
            merge_close(body)
