"""Reference revision for y06 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

Four feet, plain cylinders 24 mm across and 10 mm tall, are fused into the Speaker mesh under its
base at (+-50, +-40) mm, 20 mm in from the side faces and from the front and back faces, z -10..0.
The box itself does not move. VARIANT selects deliberately broken revisions (set by verify_checks).
"""
import bmesh
import bpy

from geom import MM, cylinder, to_object
from geom_yc import remove, speaker

VARIANT = globals().get("VARIANT", "good")
SPOTS = [(sx * 50, sy * 40) for sx in (1, -1) for sy in (1, -1)]

if VARIANT == "joined_not_fused":  # feet built touching the base and joined into the mesh, no boolean
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects["Speaker"].data)
    for x, y in SPOTS:
        bm.from_mesh(cylinder("Foot", 12 * MM, -10 * MM, 0.0, x * MM, y * MM, seg=48).data)
        remove("Foot")
    remove("Speaker")
    to_object("Speaker", bm)
elif VARIANT != "unchanged":
    remove("Speaker")
    if VARIANT == "box_lifted":  # box raised 10 mm so the feet stand on the ground plane
        speaker(lift=10, feet=SPOTS)
    elif VARIANT == "edge_measured":  # 20 mm measured to the foot's edge, not its centre
        speaker(feet=[(sx * 38, sy * 28) for sx in (1, -1) for sy in (1, -1)])
    elif VARIANT == "feet_centred_on_base":  # 10 mm cylinders centred on the base plane: half buried
        speaker(feet=SPOTS, foot_h=5)
    elif VARIANT == "rebuilt_plain":  # box redrawn from scratch: corners sharp, front recess lost
        speaker(corner_r=0.01, recess=False, feet=SPOTS)
    else:
        speaker(feet=SPOTS)
