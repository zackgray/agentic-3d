"""Reference revision for z06 (held out), applied to the starting scene. Runs inside Blender via exec_code.py.

The four slanted outside corner edges are rounded to 15 mm in horizontal section at every height,
the inside corners to 11 mm concentric with them, so the wall stays 4 mm thick. Taper, floor and
drain holes unchanged. VARIANT selects deliberately broken revisions.
"""
from geom_zc import planter, remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    kwargs = {"r_out": 15.0, "r_in": 11.0}
    if VARIANT == "outer_only":         # inside corners left sharp: they break out through the rounded outside corners
        kwargs["r_in"] = 0.0
    elif VARIANT == "same_radius_in":   # inside corners also 15 mm, wall thinned at the corners
        kwargs["r_in"] = 15.0
    elif VARIANT == "radius_10":        # 10 mm outside (6 mm inside) instead of 15 / 11
        kwargs.update(r_out=10.0, r_in=6.0)
    elif VARIANT == "taper_lost":       # rebuilt as a straight prism from the base outline
        kwargs["taper"] = False
    elif VARIANT == "coarse":           # valid: 24 segments per circle everywhere (must pass)
        kwargs["n"] = 6
    elif VARIANT == "holes_lost":       # rebuilt without the drain holes
        kwargs["holes"] = False
    remove("Planter")
    planter(**kwargs)
