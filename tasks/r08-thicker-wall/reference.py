"""Reference revision for r08, applied to the starting scene. Runs inside Blender via exec_code.py.

The liner is rebuilt with a 3 mm side wall thickened inward (inner r 28 -> 27); outside, floor and
drain hole unchanged. VARIANT selects deliberately broken revisions (set by verify_checks).
"""
from geom import MM, lathe
from geom_r import remove

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    outer, inner, floor, hole = {
        "outward": (31, 28, 2, 4),  # thickened outward (a solidify offset the wrong way)
        "centred": (30.5, 27.5, 2, 4),  # thickened half each way
        "floor_thickened": (30, 27, 3, 4),  # floor taken to 3 mm as well
        "no_drain": (30, 27, 2, 0),  # rebuilt without the drain hole
    }.get(VARIANT, (30, 27, 2, 4))
    remove("Liner")
    prof = [(hole * MM, 0), (outer * MM, 0), (outer * MM, 90 * MM), (inner * MM, 90 * MM),
            (inner * MM, floor * MM), (hole * MM, floor * MM)]
    lathe("Liner", prof, seg=128, closed=bool(hole))
