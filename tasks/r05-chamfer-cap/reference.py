"""Reference revision for r05, applied to the starting scene. Runs inside Blender via exec_code.py.

The cap is rebuilt with a 1.5 mm x 45 deg chamfer on its top outer edge: the profile corner (25, 18)
becomes (23.5, 18) -> (25, 16.5). VARIANT selects deliberately broken revisions.
"""
import math

from geom import MM, lathe
from geom_r import remove

VARIANT = globals().get("VARIANT", "good")
INNER = [(25, 0), (23, 0), (23, 15.5), (0, 15.5)]

if VARIANT != "unchanged":
    c = 3.0 if VARIANT == "too_big" else 1.5
    if VARIANT == "bottom_edge":  # the chamfer put on the bottom outer edge instead
        prof = [(0, 18), (25, 18), (25, 1.5), (23.5, 0), (23, 0), (23, 15.5), (0, 15.5)]
    elif VARIANT == "tapered":  # top face loop scaled in: the whole side becomes a cone
        prof = [(0, 18), (23.5, 18)] + INNER
    elif VARIANT == "fillet":  # a 1.5 mm round instead of a chamfer
        arc = [(23.5 + 1.5 * math.sin(a), 16.5 + 1.5 * math.cos(a))
               for a in (math.pi / 2 * k / 12 for k in range(13))]
        prof = [(0, 18)] + arc + INNER
    else:
        prof = [(0, 18), (25 - c, 18), (25, 18 - c)] + INNER
    remove("Cap")
    lathe("Cap", [(r * MM, z * MM) for r, z in prof], seg=128)
