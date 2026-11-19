"""Reference revision for r04, applied to the starting scene. Runs inside Blender via exec_code.py.

The plate is rebuilt with its four mounting holes at 6.5 mm diameter, moved 5 mm inboard in X and in
Y: (+-50, +-30) -> (+-45, +-25) mm. Centre hole unchanged. VARIANT selects broken revisions.
"""
from geom import MM, boolean, cylinder, rename
from geom_r import remove, slab

VARIANT = globals().get("VARIANT", "good")
OLD, NEW = (50, 30), (45, 25)
DIAG = (50 - 5 * 50 / 58.3095, 30 - 5 * 30 / 58.3095)  # 5 mm along the line to the plate centre

if VARIANT != "unchanged":
    radius, spots, centre = 3.25, [NEW], 10
    if VARIANT == "enlarged_only":
        spots = [OLD]
    elif VARIANT == "moved_only":
        radius = 2.5
    elif VARIANT == "old_left_open":  # new holes cut, old ones never filled
        spots = [NEW, (OLD, 2.5)]
    elif VARIANT == "moved_outward":
        spots = [(55, 35)]
    elif VARIANT == "moved_diagonal":
        spots = [DIAG]
    elif VARIANT == "centre_grown":  # every hole scaled up 1.3x, the centre hole included
        centre = 13
    remove("Plate")
    plate = slab("Plate", 60 * MM, 40 * MM, 6 * MM, 0.0, 6 * MM)
    boolean(plate, cylinder("Hole", centre * MM, -1 * MM, 7 * MM, seg=96), "DIFFERENCE")
    for spot in spots:
        (x, y), r = (spot, radius) if isinstance(spot[0], (int, float)) else spot
        for sx in (1, -1):
            for sy in (1, -1):
                boolean(plate, cylinder("Hole", r * MM, -1 * MM, 7 * MM, sx * x * MM, sy * y * MM, seg=48),
                        "DIFFERENCE")
    rename(plate, "Plate")
