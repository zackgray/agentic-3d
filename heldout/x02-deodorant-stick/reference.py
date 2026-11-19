"""Reference model for x02 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

Barrel and cap: elliptical lofts minus elliptical cavities. Stick: an elliptical prism whose top is
the paraboloid z = 96 + 4 * (1 - (x/22.5)^2 - (y/12.5)^2) mm, lofted as shrinking ellipses. VARIANT
selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, boolean, loft, rename
from geom_h1 import ellipse, ellipse_loft

VARIANT = globals().get("VARIANT", "good")
SEG = 96


def ell(a, b, z):
    """One elliptical section; 'rotated' swaps the axes (long side along Y instead of X)."""
    return (b, a, z) if VARIANT == "rotated" else (a, b, z)


barrel = ellipse_loft("Barrel", [ell(25 * MM, 15 * MM, 0.0), ell(25 * MM, 15 * MM, 90 * MM)], SEG)
floor = -1 if VARIANT == "no_floor" else 3
boolean(barrel, ellipse_loft("Cavity", [ell(23 * MM, 13 * MM, floor * MM), ell(23 * MM, 13 * MM, 91 * MM)], SEG),
        "DIFFERENCE")
rename(barrel, "Barrel")

base = 3.0 if VARIANT == "stick_on_floor" else 3.5
a, b, _ = ell(22.5 * MM, 12.5 * MM, 0)
layers = [(ellipse(a, b, SEG), base * MM), (ellipse(a, b, SEG), 96 * MM)]
if VARIANT == "flat_top":
    layers[-1] = (ellipse(a, b, SEG), 100 * MM)
else:
    for k in range(1, 16):
        s = 1 - k / 16  # section scale; the paraboloid puts it at z = 96 + 4 * (1 - s^2)
        layers.append((ellipse(a * s, b * s, SEG), (96 + 4 * (1 - s * s)) * MM))
loft("Stick", layers)

dz = -0.5 if VARIANT == "cap_resting" else 0.0
cap = ellipse_loft("Cap", [ell(25 * MM, 15 * MM, (90.5 + dz) * MM), ell(25 * MM, 15 * MM, (110 + dz) * MM)], SEG)
if VARIANT != "solid_cap":
    boolean(cap, ellipse_loft("CapCavity", [ell(23 * MM, 13 * MM, (89.5 + dz) * MM),
                                            ell(23 * MM, 13 * MM, (107 + dz) * MM)], SEG), "DIFFERENCE")
rename(cap, "Cap")
