"""Reference revision for y05 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

A round hanging hole 32 mm across goes straight through the board, its centre on the board's long
centre line (y = 0) and 40 mm in from the +X end: (140, 0). Everything else is unchanged. VARIANT
selects deliberately broken revisions (set by verify_checks).
"""
from geom_yc import board, remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    hole = {
        "wrong_end": (-140, 0, 32, 18),           # 40 mm in from the -X end instead
        "edge_measured": (124, 0, 32, 18),        # 40 mm measured to the hole's edge, not its centre
        "radius_as_diameter": (140, 0, 64, 18),   # 32 mm used as the radius
        "blind_hole": (140, 0, 32, 10),           # cutter too short: a 10 mm pocket, not through
    }.get(VARIANT, (140, 0, 32, 18))
    remove("Board")
    board(corner_r=0.01 if VARIANT == "rebuilt_sharp" else 20.0, hole=hole)  # rebuilt_sharp: corners lost
