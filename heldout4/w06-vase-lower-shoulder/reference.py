"""Reference revision for w06 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

The shoulder (widest point, r 36) drops 20 mm, from z 60 to z 40; both cones stay straight, so the
lower cone now runs from (24, 8) to (36, 40) and the upper one from (36, 40) to the unchanged neck
start (12, 110). Foot, neck, lip, height and bore unchanged. VARIANT selects deliberately broken
revisions.
"""
import bpy
from mathutils import Vector

from geom import MM
from geom_wc import bud_vase, remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT == "natural":
    # The edit an agent would most likely make on the existing mesh: select the shoulder's vertex
    # ring (r 36 at z 60) and move it straight down 20 mm.
    vase = bpy.data.objects["Vase"]
    ring = [v for v in vase.data.vertices if abs(v.co.z - 60 * MM) < 1e-6 and abs(v.co.xy.length - 36 * MM) < 1e-6]
    assert len(ring) == 64, len(ring)
    for v in ring:
        v.co -= Vector((0.0, 0.0, 20 * MM))
    vase.data.update()
elif VARIANT == "neck_dropped":
    # everything from the shoulder up moved down 20 mm with it: neck, lip and bore floor follow
    vase = bpy.data.objects["Vase"]
    for v in vase.data.vertices:
        if v.co.z > 59 * MM or (v.co.xy.length < 6.5 * MM and v.co.z > 39 * MM):
            v.co -= Vector((0.0, 0.0, 20 * MM))
    vase.data.update()
elif VARIANT != "unchanged":
    kwargs = {"shoulder_z": 40.0}
    if VARIANT == "lower_10":          # shoulder lowered 10 mm instead of 20
        kwargs["shoulder_z"] = 50.0
    elif VARIANT == "slope_kept":      # upper cone kept its slope, so the neck now starts 20 mm lower
        kwargs["neck_z"] = 90.0
    elif VARIANT == "bore_lost":       # rebuilt solid, without the bore
        kwargs["bore"] = False
    elif VARIANT == "lip_sharp":       # rebuilt with a sharp lip
        kwargs["lip"] = False
    elif VARIANT == "coarse":          # valid: 24 segments per circle everywhere (must pass)
        kwargs["n"] = 6
    remove("Vase")
    bud_vase(**kwargs)
