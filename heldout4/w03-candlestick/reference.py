"""Reference model for w03 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

A loft of polar-sampled outlines: the chamfered rounded-square foot (plan radius shrinking with the
chamfer inset), straight-blended at every angle to a 15 mm circle at the top. The candle socket and
the felt recess are exact boolean cuts. VARIANT selects deliberately broken builds.
"""
from geom_wb import candlestick

VARIANT = globals().get("VARIANT", "good")

kwargs = {}
if VARIANT == "coarse":            # valid: 24 segments per full circle everywhere (must pass)
    kwargs["seg"] = 24
elif VARIANT == "no_chamfer":      # bottom edge left sharp
    kwargs["chamfer"] = 0.0
elif VARIANT == "sharp_corners":   # foot modelled as a plain square, corners not rounded
    kwargs["r"] = 0.0
elif VARIANT == "square_top":      # stem lofted to a 30 mm rounded square (r 6) instead of a circle
    kwargs["top_square"] = (15.0, 6.0)
elif VARIANT == "no_foot":         # stem lofts straight from the chamfer, no vertical foot band
    kwargs["foot_top"] = 3.0
elif VARIANT == "twisted":         # top circle joined 30 degrees out of step (a twisted bridge)
    kwargs["twist_deg"] = 30.0
elif VARIANT == "shallow_socket":  # socket only 10 mm deep
    kwargs["well_floor"] = 110.0
elif VARIANT == "no_recess":
    kwargs["recess"] = False

candlestick(**kwargs)
