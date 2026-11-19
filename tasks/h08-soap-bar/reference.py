"""Reference model for h08, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The bar is a loft of rounded-rectangle contours with 8 mm roundover bands top and bottom; the logo
recess is a lofted rounded rectangle cut with an exact boolean. VARIANT selects broken versions.
"""
from mathutils import Matrix

from geom import MM, boolean, loft, rename, rounded_rect
from geom_m import rounded_slab

VARIANT = globals().get("VARIANT", "good")

plan_r = 0.01 * MM if VARIANT == "sharp_corners" else 15 * MM
edge_r = 0.0 if VARIANT == "sharp_edges" else 8 * MM
bar = rounded_slab("Bar", 45 * MM, 30 * MM, plan_r, 0.0, 28 * MM, r_bot=edge_r, r_top=edge_r)

logo = rounded_rect(20 * MM, 8 * MM, 3 * MM)
if VARIANT == "embossed":  # raised instead of recessed
    boolean(bar, loft("Logo", [(logo, 27 * MM), (logo, 29.5 * MM)]), "UNION")
elif VARIANT != "no_recess":
    floor = 25 if VARIANT == "deep_recess" else 26.5
    boolean(bar, loft("Logo", [(logo, floor * MM), (logo, 29 * MM)]), "DIFFERENCE")

if VARIANT == "rotated":  # long side along Y instead of X
    bar.data.transform(Matrix.Rotation(1.5707963267948966, 4, "Z"))

rename(bar, "Bar")
