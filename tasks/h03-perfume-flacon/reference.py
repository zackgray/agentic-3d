"""Reference model for h03, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The body is a loft of the chamfered-rectangle outline (convex, eight sides), the collar a cylinder
unioned onto it, the neck bore an exact boolean. The cap is a lathe. VARIANT selects broken versions.
"""
from geom import MM, boolean, cylinder, lathe, loft, rename, rounded_rect

VARIANT = globals().get("VARIANT", "good")
HX, HY, C = 25 * MM, 15 * MM, 5 * MM

if VARIANT == "no_chamfer":
    outline = [(HX, -HY), (HX, HY), (-HX, HY), (-HX, -HY)]
elif VARIANT == "round_edges":
    outline = rounded_rect(HX, HY, C)
else:
    outline = [(HX, -HY + C), (HX, HY - C), (HX - C, HY), (-HX + C, HY),
               (-HX, HY - C), (-HX, -HY + C), (-HX + C, -HY), (HX - C, -HY)]
bottle = loft("Bottle", [(outline, 0.0), (outline, 70 * MM)])

collar_z0 = 70.5 * MM if VARIANT == "collar_floating" else 69 * MM  # 69: overlaps the body to fuse
boolean(bottle, cylinder("Collar", 8 * MM, collar_z0, 80 * MM, seg=96), "UNION")
if VARIANT != "no_neck_bore":
    boolean(bottle, cylinder("Bore", 3 * MM, 60 * MM, 81 * MM, seg=64), "DIFFERENCE")
rename(bottle, "Bottle")

rim = 70 * MM if VARIANT == "cap_on_shoulder" else 72 * MM
if VARIANT == "solid_cap":
    cap = [(0, rim), (12 * MM, rim), (12 * MM, 95 * MM), (0, 95 * MM)]
else:
    bore_r, ceil = (8 * MM, 80 * MM) if VARIANT == "cap_tight" else (8.4 * MM, 80.4 * MM)
    cap = [(0, ceil), (bore_r, ceil), (bore_r, rim), (12 * MM, rim), (12 * MM, 95 * MM), (0, 95 * MM)]
lathe("Cap", cap, seg=96)
