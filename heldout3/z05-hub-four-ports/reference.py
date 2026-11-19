"""Reference revision for z05 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

Three front ports become four at the same 30 mm pitch, the row centred on x = 0: x = -45, -15, 15,
45. Port shape, depth and height unchanged; the old openings at -30, 0, 30 are filled. The top
fillet and the button recess stay. VARIANT selects deliberately broken revisions.
"""
from geom_zc import hub, remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    kwargs = {}
    ports = [-45, -15, 15, 45]
    if VARIANT == "appended":           # a fourth port added on the end, row no longer centred
        ports = [-30, 0, 30, 60]
    elif VARIANT == "squeezed":         # four ports fitted into the old row's span (20 mm pitch)
        ports = [-30, -10, 10, 30]
    elif VARIANT == "old_left_open":    # new row cut, old openings never filled
        ports = [-45, -15, 15, 45, -30, 0, 30]
    elif VARIANT == "port_resized":     # ports misread as 16 mm wide
        kwargs["port_w"] = 16.0
    elif VARIANT == "fillet_lost":      # rebuilt with a sharp top edge
        kwargs["top_fillet"] = 0.0
    elif VARIANT == "coarse":           # valid: 24 segments per circle everywhere (must pass)
        kwargs["n"] = 6
    elif VARIANT == "button_lost":      # rebuilt without the button recess
        kwargs["button"] = False
    remove("Hub")
    hub(ports, **kwargs)
