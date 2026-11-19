"""Reference model for z03, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A chamfered rounded-rectangle base with four underside foot recesses, a leaning back panel (a
parallelogram prism along X) pierced by a cable hole perpendicular to its faces, and a bullnosed
front lip, all fused with exact booleans. Panel and lip start 1 mm inside the base so no boolean
meets a coplanar face. VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

from geom import MM, boolean, box, cylinder, rename
from geom_m import clean
from geom_zb import bullnose_x, chamfer_slab, cyl_axis, prism_x

VARIANT = globals().get("VARIANT", "good")

corner = 2.5 if VARIANT == "sharp_corners" else 10.0
chamfer = 0.0 if VARIANT == "no_chamfer" else 2.0
stand = chamfer_slab("Stand", 40 * MM, 45 * MM, corner * MM, 0.0, 8 * MM, chamfer * MM)

if VARIANT != "no_recesses":
    for x in (-28, 28):
        for y in (-33, 33):
            boolean(stand, cylinder("Recess", 6 * MM, -1 * MM, 1.5 * MM, x * MM, y * MM, seg=40), "DIFFERENCE")

# Back panel: cross-section corners (y, z) = (0, 8), (8, 8), (38, 88), (30, 88), extended down to
# z = 7 along the same lean so it is buried 1 mm in the base.
thick = 10.0 if VARIANT == "thick_panel" else 8.0
z_low = 8.5 if VARIANT == "floating_panel" else 7.0
if VARIANT == "upright_panel":
    sec = [(0, z_low), (thick, z_low), (thick, 88), (0, 88)]
else:
    y_low = (z_low - 8) * 30 / 80
    sec = [(y_low, z_low), (y_low + thick, z_low), (38 + thick - 8, 88), (30, 88)]
boolean(stand, prism_x("Panel", [(y * MM, z * MM) for y, z in sec], -35 * MM, 35 * MM), "UNION")

if VARIANT != "no_hole":
    L = math.hypot(30, 80)
    n = (0.0, 80 / L, -30 / L)  # into the panel, perpendicular to its faces
    t_mid = 8 * 80 / L / 2
    mid = (0.0, (8.25 + t_mid * n[1]) * MM, (30 + t_mid * n[2]) * MM)
    if VARIANT in ("horizontal_hole", "upright_panel"):
        n = (0.0, 1.0, 0.0)
        mid = (0.0, 8.25 * MM, 30 * MM) if VARIANT == "horizontal_hole" else (0.0, 4 * MM, 30 * MM)
    boolean(stand, cyl_axis("Hole", 8 * MM, mid, n, 15 * MM), "DIFFERENCE")

if VARIANT == "square_lip":
    lip = box("Lip", (-35 * MM, -40 * MM, 7 * MM), (35 * MM, -34 * MM, 20 * MM))
else:
    lip = bullnose_x("Lip", -40 * MM, -34 * MM, 7 * MM, 20 * MM, -35 * MM, 35 * MM)
boolean(stand, lip, "UNION")
clean(stand)  # dissolve the sliver an exact boolean leaves where a recess meets the base fan
rename(stand, "Stand")
