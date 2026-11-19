"""Reference model for m02, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Body: a lathed cylinder, feet unioned on, then one exact boolean with all 80 radial grille cutters
merged into a single cutter object, then the three button pockets. Buttons are lathed cylinders.
VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

from geom import MM, boolean, cylinder, rename
from geom_m import clean, cyl_along, join, mm_lathe

VARIANT = globals().get("VARIANT", "good")
R = 38 if VARIANT == "narrow_body" else 40
ROWS = (45, 60, 75, 90) if VARIANT == "grille_4_rows" else (45, 60, 75, 90, 105)
BUTTONS = {"ButtonMinus": -15, "ButtonPower": 0, "ButtonPlus": 15}

body = mm_lathe("Body", [(0, 5), (R, 5), (R, 150), (0, 150)])

if VARIANT != "no_feet":
    z1 = 4.5 if VARIANT == "floating_feet" else 6  # good: 1 mm into the body so the union fuses
    feet = [cylinder("Foot", 6 * MM, 0.0, z1 * MM, x * MM, y * MM, seg=48)
            for x, y in ((20, 20), (-20, 20), (-20, -20), (20, -20))]
    boolean(body, join("Feet", feet), "UNION")

if VARIANT != "no_grille":
    cutters = []
    for z in ROWS:
        for k in range(16):
            a = math.radians(22.5 * k)
            d = (math.cos(a), math.sin(a), 0.0)
            start = [38 * MM * c for c in d]
            end = [45 * MM * c for c in d]
            start[2] = end[2] = z * MM
            cutters.append(cyl_along("Hole", 2.5 * MM, start, end, seg=24))
    boolean(body, join("Grille", cutters), "DIFFERENCE")
    clean(body)

if VARIANT != "no_pockets":
    pockets = [cylinder("Pocket", 6 * MM, 147 * MM, 151 * MM, x * MM, 0.0, seg=64) for x in BUTTONS.values()]
    boolean(body, join("Pockets", pockets), "DIFFERENCE")

rename(body, "Body")

for name, x in BUTTONS.items():
    r = 6 if (VARIANT == "tight_plus" and name == "ButtonPlus") else 5.5
    z0 = 147 if (VARIANT == "power_on_floor" and name == "ButtonPower") else 147.5
    rename(cylinder(name, r * MM, z0 * MM, (z0 + 4.5) * MM, x * MM, 0.0, seg=64), name)
