"""Reference model for z07, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Beard trimmer in its charging dock. Dock: rounded-rectangle loft with a chamfer band on top, minus
a rounded-rectangle socket. Body: loft tapering in X. Slider pocket and slider: stadium prisms
along Y. Head: loft between two different rounded rectangles. Blade: box minus nine slot boxes.
VARIANT selects deliberately broken versions (set by verify_checks).
"""
from mathutils import Matrix

from geom import MM, boolean, box, rename
from geom_m import clean, join
from geom_zd import prism_y, rr_loft, stadium_xz

VARIANT = globals().get("VARIANT", "good")
N = 6 if VARIANT == "coarse24" else 16  # points per quarter circle; coarse24 = a 24-segment build


def rr(name, sections):
    return rr_loft(name, sections, n=N)


def stadium(hx, z_lo, z_hi):
    return stadium_xz(hx, z_lo, z_hi, k=2 * N)


# Dock
if VARIANT == "no_chamfer":
    dock = rr("Dock", [(32, 25, 10, 0), (32, 25, 10, 24)])
else:
    dock = rr("Dock", [(32, 25, 10, 0), (32, 25, 10, 21), (29, 22, 7, 24)])
boolean(dock, rr("Socket", [(18, 13, 6, 8), (18, 13, 6, 25)]), "DIFFERENCE")
rename(clean(dock), "Dock")

# Body
z0 = 8.0 if VARIANT == "body_on_floor" else 8.5
top_hx = 17.5 if VARIANT == "no_taper" else 14.5
body = rr("Body", [(17.5, 12.5, 5.5, z0), (top_hx, 12.5, 5.5, 130)])
if VARIANT != "no_slider_pocket":
    boolean(body, prism_y("Pocket", stadium(4, 75, 95), -14, -11), "DIFFERENCE")
rename(clean(body), "Body")

# Slider button
y_back = -11.0 if VARIANT == "slider_on_floor" else -11.5
slider = prism_y("Slider", stadium(3.5, 75.5, 94.5), -14, y_back)
if VARIANT == "slider_scale":  # built ten times too large about its own centre
    slider.data.transform(Matrix.Translation((0, -0.01275, 0.085)) @ Matrix.Scale(10, 4)
                          @ Matrix.Translation((0, 0.01275, -0.085)))
rename(slider, "Slider")

# Head
if VARIANT == "head_straight":
    head = rr("Head", [(14.5, 12.5, 5.5, 130.5), (14.5, 12.5, 5.5, 150)])
else:
    z_h = 130 if VARIANT == "head_on_body" else 130.5
    head = rr("Head", [(14.5, 12.5, 5.5, z_h), (22, 6, 3, 150)])
rename(head, "Head")

# Blade
z_b = 150 if VARIANT == "blade_on_head" else 150.5
blade = box("Blade", (-20 * MM, -2 * MM, z_b * MM), (20 * MM, 2 * MM, 160 * MM))
if VARIANT != "blade_no_slots":
    slots = [box("Slot", ((x - 1) * MM, -3 * MM, 156 * MM), ((x + 1) * MM, 3 * MM, 161 * MM))
             for x in range(-16, 17, 4)]
    boolean(blade, join("Slots", slots), "DIFFERENCE")
if VARIANT == "blade_along_y":
    blade.data.transform(Matrix.Rotation(1.5707963267948966, 4, "Z"))
rename(clean(blade), "Blade")
