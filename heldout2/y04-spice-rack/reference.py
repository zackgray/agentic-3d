"""Reference layout for y04 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

A two-tier stepped rack (two overlapping boxes fused) with two spice jars on the front tier and two
on the back tier, each jar 0.4 mm clear of its tier. VARIANT selects deliberately broken layouts
(set by verify_checks).
"""
from geom import MM, box, boolean, cylinder, rename

VARIANT = globals().get("VARIANT", "good")
CLEAR = 0.0 if VARIANT == "resting" else 0.4
LOW, HIGH = 25, 60

if VARIANT == "one_tier":  # the whole rack at the back tier's height
    rack = box("Rack", (-90 * MM, -45 * MM, 0.0), (90 * MM, 45 * MM, HIGH * MM))
else:
    rack = box("Rack", (-90 * MM, 0.0, 0.0), (90 * MM, 45 * MM, HIGH * MM))
    boolean(rack, box("Low", (-90 * MM, -45 * MM, 0.0), (90 * MM, 1 * MM, LOW * MM)), "UNION")
rename(rack, "Rack")

height = 60 if VARIANT == "short_jars" else 72
front_x, back_x = (25, 50) if VARIANT == "swapped_x" else (50, 25)
if VARIANT == "back_pitch":  # 14 mm gap read as nothing: the back jars touch
    back_x = 18
back_z = LOW if VARIANT == "back_low" else HIGH
jars = (("Jar_FL", -front_x, -22.5, LOW), ("Jar_FR", front_x, -22.5, LOW),
        ("Jar_BL", -back_x, 22.5, back_z), ("Jar_BR", back_x, 22.5, back_z))
for name, x, y, z in jars:
    z0 = (z + CLEAR) * MM
    if VARIANT == "square_jars":
        box(name, ((x - 18) * MM, (y - 18) * MM, z0), ((x + 18) * MM, (y + 18) * MM, z0 + height * MM))
    else:
        cylinder(name, 18 * MM, z0, z0 + height * MM, x=x * MM, y=y * MM, seg=96)
