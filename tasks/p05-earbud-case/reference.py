"""Reference model for p05, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Base and lid are lofts of rounded-rectangle contours: the plan corner radius shrinks with the inset
through each roundover band. Pockets are cut with exact booleans. VARIANT selects broken versions.
"""
import math

from geom import MM, boolean, cylinder, loft, rounded_rect

VARIANT = globals().get("VARIANT", "good")
HX, HY = 30 * MM, 15 * MM
PLAN_R = 0.01 * MM if VARIANT == "sharp_corners" else 12 * MM
EDGE_R = 0.0 if VARIANT == "sharp_edges" else 4 * MM
N = 12  # layers per roundover band


def contour(inset):
    return rounded_rect(HX - inset, HY - inset, max(0.01 * MM, PLAN_R - inset))


def band(z_flat, sign):
    """Roundover layers from the flat side (inset 0 at z_flat) out to the face (inset EDGE_R)."""
    if EDGE_R == 0:
        return []
    out = []
    for k in range(1, N + 1):
        phi = math.pi / 2 * k / N
        out.append((contour(EDGE_R * (1 - math.cos(phi))), z_flat + sign * EDGE_R * math.sin(phi)))
    return out


base_layers = band(EDGE_R, -1)[::-1] + [(contour(0), EDGE_R), (contour(0), 24 * MM)]
base = loft("Base", base_layers)

lid_z0 = 24 * MM if VARIANT == "lid_touching" else 24.3 * MM
lid_layers = [(contour(0), lid_z0), (contour(0), 36 * MM - EDGE_R)] + band(36 * MM - EDGE_R, 1)
lid = loft("Lid", lid_layers)

if VARIANT != "no_pockets":
    floor = 12 * MM if VARIANT == "shallow_pockets" else 9 * MM
    for x in (14, -14):
        boolean(base, cylinder("Pocket", 6 * MM, floor, 25 * MM, x * MM, 0.0, seg=48), "DIFFERENCE")
