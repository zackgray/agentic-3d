"""Reference model for w08, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Stovetop espresso pot. Boiler: octagonal frustum with a valve boss along X unioned on. Valve: a
hexagonal prism along X. Jug: an inverted octagonal frustum minus an octagonal cavity, with a
rectangular handle bar unioned on. Lid: an octagonal plate with a chamfered top edge and a turned
knob with a filleted top edge. VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

from mathutils import Matrix

from geom import MM, boolean, box, cylinder, rename
from geom_m import clean, mm_lathe
from geom_wd import oct_loft, polygon, prism_x

VARIANT = globals().get("VARIANT", "good")
COARSE = VARIANT == "coarse24"
SEG = 24 if COARSE else 96

# Boiler: across flats 96 at z 0 to 80 at z 72, valve boss d 12 along X at z 36 out to x 50
f_top = 96 if VARIANT == "straight_boiler" else 80
boiler = oct_loft("Boiler", [(96, 0), (f_top, 72)], rot_deg=22.5 if VARIANT == "oct_rotated" else 0)
if VARIANT != "no_boss":
    boolean(boiler, cylinder("Boss", 6 * MM, 40 * MM, 50 * MM, 0.0, 36 * MM, seg=SEG, axis="X"), "UNION")
rename(clean(boiler), "Boiler")

# Valve: hexagon 14 across flats, flats facing up and down, x 50.5..56
x_v = 50.0 if VARIANT == "valve_on_boss" else 50.5
rename(prism_x("Valve", polygon(6, 14, 30 if VARIANT == "valve_rotated" else 0), x_v, 56, 0, 36), "Valve")

# Jug: across flats 80 at z 72.5 to 92 at z 150; cavity 74 at z 76.5 to 86 at z 150 (cutter runs on
# to z 151 at the same taper); handle bar y -7..7, z 112..124, out to x -105
jug = oct_loft("Jug", [(80, 72.5), (92, 150)])
if VARIANT != "jug_solid":
    boolean(jug, oct_loft("Cavity", [(74, 76.5), (86, 150), (86 + 12 / 73.5, 151)]), "DIFFERENCE")
handle = box("Handle", (-105 * MM, -7 * MM, 112 * MM), (-42 * MM, 7 * MM, 124 * MM))
if VARIANT == "handle_on_y":  # on the -Y face instead of -X
    handle.data.transform(Matrix.Rotation(math.pi / 2, 4, "Z"))
boolean(jug, handle, "UNION")
if VARIANT == "jug_on_boiler":
    jug.data.transform(Matrix.Translation((0.0, 0.0, -0.5 * MM)))
rename(clean(jug), "Jug")

# Lid: plate 92 across flats from z 150.5, sides to z 154, 2 mm chamfer to a top 88 across flats at
# z 156; knob stem radius 5 up to z 162, cap radius 12 from z 162 to z 170 with an r 3 top fillet
z_l = 150.0 if VARIANT == "lid_on_jug" else 150.5
if VARIANT == "no_lid_chamfer":
    lid = oct_loft("Lid", [(92, z_l), (92, 156)])
else:
    lid = oct_loft("Lid", [(92, z_l), (92, 154), (88, 156)])
if VARIANT == "no_fillet":
    prof = [(0, 155), (5, 155), (5, 162), (12, 162), (12, 170), (0, 170)]
else:
    k = 6 if COARSE else 16  # points per quarter round
    prof = [(0, 155), (5, 155), (5, 162), (12, 162), (12, 167)]
    prof += [(9 + 3 * math.cos(math.pi / 2 * i / k), 167 + 3 * math.sin(math.pi / 2 * i / k)) for i in range(1, k)]
    prof += [(9, 170), (0, 170)]
boolean(lid, mm_lathe("Knob", prof, seg=SEG), "UNION")
rename(clean(lid), "Lid")
