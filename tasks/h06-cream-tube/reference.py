"""Reference model for h06, built by hand to prove the checks. Runs inside Blender via exec_code.py.

The tube's round section and transition are one loft through elliptical sections (corresponding
points move in straight lines, so every section in between is the exact ellipse with linear
semi-axes); the crimp is a box unioned on top. The cap is a lathe with the groove in its profile.
VARIANT selects broken versions.
"""
from geom import MM, boolean, box, lathe, rename
from geom_h1 import ellipse_loft

VARIANT = globals().get("VARIANT", "good")

g0, g1, gr = 14 * MM, 15 * MM, 14.2 * MM
if VARIANT == "no_groove":
    cap = [(0, 0.0), (15 * MM, 0.0), (15 * MM, 20 * MM), (0, 20 * MM)]
else:
    cap = [(0, 0.0), (15 * MM, 0.0), (15 * MM, g0), (gr, g0), (gr, g1), (15 * MM, g1),
           (15 * MM, 20 * MM), (0, 20 * MM)]
lathe("Cap", cap, seg=128)

A0, A1, B1 = 15 * MM, 23 * MM, 2 * MM
z_bottom = 20.0 * MM if VARIANT == "tube_on_cap" else 20.4 * MM


def section(z, z0=40 * MM, z1=128 * MM):
    s = (z - z0) / (z1 - z0)
    if VARIANT == "eased_transition":
        s = s * s * (3 - 2 * s)
    a, b = A0 + (A1 - A0) * s, A0 + (B1 - A0) * s
    return (b, a, z) if VARIANT == "crimp_wrong_axis" else (a, b, z)


if VARIANT == "no_round_section":
    sections = [(A0, A0, z_bottom), section(128 * MM, z0=z_bottom)]
elif VARIANT == "eased_transition":
    sections = [(A0, A0, z_bottom)] + [section((40 + 88 * k / 32) * MM) for k in range(33)]
else:
    sections = [(A0, A0, z_bottom), section(40 * MM), section(128 * MM)]
tube = ellipse_loft("Tube", sections, seg=128)

if VARIANT != "no_crimp":
    hx, hy = 24 * MM, (1.5 * MM if VARIANT == "thin_crimp" else 2 * MM)
    if VARIANT == "crimp_wrong_axis":
        hx, hy = hy, hx
    boolean(tube, box("Crimp", (-hx, -hy, 128 * MM), (hx, hy, 140 * MM)), "UNION")
rename(tube, "Tube")
