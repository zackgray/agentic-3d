"""Reference model for h04, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The ribbed outside is one loft of a star-shaped outline (shell arcs plus rib profiles), so no
boolean meets a coplanar face; the bore is an exact boolean with a cutter that overshoots the rim.
Floating and short ribs are unioned boxes (they never share a plane with the shell's top or bottom).
VARIANT selects broken versions.
"""
import math

from geom import MM, boolean, cylinder, lathe, loft, rename
from geom_h1 import rot_box

VARIANT = globals().get("VARIANT", "good")
R, RIB_R = 15 * MM, 16 * MM
count = 20 if VARIANT == "ribs_20" else 24
offset = 7.5 if VARIANT == "ribs_offset" else 0.0
half_w = 1.1 * MM if VARIANT == "wide_ribs" else 0.6 * MM
loft_ribs = VARIANT not in ("no_ribs", "floating_ribs", "short_ribs")


def outline(arc_pts=6):
    """Counter-clockwise outline: per rib its four corners, then shell arc points to the next rib."""
    if not loft_ribs:
        return [(R * math.cos(t), R * math.sin(t)) for t in (2 * math.pi * i / 128 for i in range(128))]
    pts, half = [], math.asin(half_w / R)
    root = math.sqrt(R * R - half_w * half_w)
    for k in range(count):
        c = math.radians(offset + 360.0 * k / count)
        cs, sn = math.cos(c), math.sin(c)
        for lx, ly in ((root, -half_w), (RIB_R, -half_w), (RIB_R, half_w), (root, half_w)):
            pts.append((lx * cs - ly * sn, lx * sn + ly * cs))
        a0, a1 = c + half, c + 2 * math.pi / count - half
        for j in range(1, arc_pts + 1):
            t = a0 + (a1 - a0) * j / (arc_pts + 1)
            pts.append((R * math.cos(t), R * math.sin(t)))
    return pts


ring = outline()
cap = loft("Cap", [(ring, 0.0), (ring, 18 * MM)])
if VARIANT != "solid":
    boolean(cap, cylinder("Bore", 12.5 * MM, -1 * MM, 15 * MM, seg=128), "DIFFERENCE")

if VARIANT in ("floating_ribs", "short_ribs"):
    root = 15.1 * MM if VARIANT == "floating_ribs" else 14 * MM  # floating: a 0.1 mm gap
    z0, z1 = (1 * MM, 17 * MM) if VARIANT == "short_ribs" else (0.0, 18 * MM)
    for k in range(count):
        boolean(cap, rot_box("Rib", (root, -half_w, z0), (RIB_R, half_w, z1), 360.0 * k / count), "UNION")
rename(cap, "Cap")
