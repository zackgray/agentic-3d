"""Reference model for y01 (held out), built by hand to prove the checks. Runs inside Blender via exec_code.py.

Jar: one lathe profile, an open cup with a flat floor and a 4 mm wall. Lid: one lathe profile, a
flat disc with a solid plug hanging into the jar mouth. VARIANT selects deliberately broken
versions (set by verify_checks).
"""
from geom import MM, lathe

VARIANT = globals().get("VARIANT", "good")
SEG = 96

if VARIANT == "solid_jar":  # forgot the cavity
    jar = [(0, 0), (40, 0), (40, 90), (0, 90)]
else:
    floor = -1 if VARIANT == "no_floor" else 6  # no_floor: the cavity cut straight through
    if floor < 0:
        jar = [(36, 0), (40, 0), (40, 90), (36, 90)]
    else:
        jar = [(0, 0), (40, 0), (40, 90), (36, 90), (36, floor), (0, floor)]
lathe("Jar", [(r * MM, z * MM) for r, z in jar], seg=SEG, closed=(VARIANT == "no_floor"))

dz = -0.4 if VARIANT == "lid_resting" else 0.0  # resting: the whole lid dropped onto the rim
plug_r = 36.0 if VARIANT == "tight_plug" else 35.6  # tight: plug sized to the bore, no clearance
if VARIANT == "no_plug":
    lid = [(0, 90.4), (40, 90.4), (40, 96), (0, 96)]
else:
    lid = [(0, 80), (plug_r, 80), (plug_r, 90.4), (40, 90.4), (40, 96), (0, 96)]
lathe("Lid", [(r * MM, (z + dz) * MM) for r, z in lid], seg=SEG)
