"""Reference layout for l03, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A cylinder plinth and eight flat-sided products on a 120 mm circle, each turned so its label flat
faces radially outward. VARIANT selects deliberately broken layouts (set by verify_checks).
"""
from geom import MM, cylinder
from geom_l import flat_prism, place, radial

VARIANT = globals().get("VARIANT", "good")

cylinder("Plinth", (70 if VARIANT == "wide_plinth" else 60) * MM, 0.0, 100 * MM, seg=96)

radius = 110 if VARIANT == "wrong_radius" else 120
height = 70 if VARIANT == "short_products" else 80
start = 22.5 if VARIANT == "offset_angle" else 0.0
count = 7 if VARIANT == "missing_product" else 8
flat = 19.999 if VARIANT == "no_flats" else 15  # a flat 19.999 from the axis is no flat at all
for k in range(count):
    angle = start + 45 * k
    x, y = radial(radius, angle)
    turn = {"flats_inward": angle + 180, "flats_all_x": 0.0}.get(VARIANT, angle)
    obj = flat_prism(f"Product_{k + 1}", 20 * MM, flat * MM, 0.0, height * MM, n=64)
    place(obj, x, y, 0.0, turn)
