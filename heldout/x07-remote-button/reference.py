"""Reference revision for x07, applied to the starting scene. Runs inside Blender via exec_code.py.

The power button and its pocket move 30 mm toward -Y, (0, +50) -> (0, +20), and grow 3 mm across:
button 13 -> 16 mm, pocket 14 -> 17 mm, heights and depth unchanged. The remote is rebuilt with the
old pocket gone. VARIANT selects deliberately broken revisions (set by verify_checks).
"""
from mathutils import Matrix

from geom import MM
from geom_x2 import remote, remote_button, remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT == "button_only":  # the naive edit: move and resize the Button object, leave the pocket
    remove("Button")
    remote_button(20, 16)
elif VARIANT == "scaled_button":  # pocket right, button scaled up 16/13 in every axis about its base
    remove("Remote")
    remove("Button")
    remote([(20, 17)])
    b = remote_button(20, 13)
    k = 16 / 13
    b.data.transform(Matrix.Translation((0, 20 * MM, 15.5 * MM)) @ Matrix.Scale(k, 4)
                     @ Matrix.Translation((0, -20 * MM, -15.5 * MM)))
elif VARIANT != "unchanged":
    bd, pd = (13, 14) if VARIANT == "not_resized" else (16, 17)
    pockets = [(20, pd)] + ([(50, 14)] if VARIANT == "old_left_open" else [])
    remove("Remote")
    remove("Button")
    remote(pockets, edge_r=0.0 if VARIANT == "rebuilt_sharp" else 3.0)
    remote_button(20, bd)
