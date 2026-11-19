"""Reference model for w07, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Desk tape dispenser. Body: rounded-rectangle loft with a chamfer band at the bottom, minus a
cylindrical cradle along X and a blade slot. Tape: an annulus revolved about the X axis. Hub: a
stepped revolved spool with flanges and an axle bore. Blade: a serrated plate. VARIANT selects
deliberately broken versions (set by verify_checks).
"""
import math

from mathutils import Matrix

from geom import MM, boolean, box, cylinder, rename
from geom_m import clean
from geom_wd import lathe_x, strip_plate
from geom_zd import rr_loft

VARIANT = globals().get("VARIANT", "good")
COARSE = VARIANT == "coarse24"
SEG = 24 if COARSE else 96
N = 6 if COARSE else 16
AXIS_Y = 5.0
AXIS_Z = 47.5 if VARIANT == "roll_low" else 48.0  # roll_low: tape and hub dropped onto the cradle


def phase(obj, z_mm=48.0):
    """coarse24 turns round parts half a segment about the tape axis, so flats (not vertices) sit
    at the top, bottom, front and back: the worst case for bbox and probe tolerances."""
    if COARSE:
        p = Matrix.Translation((0.0, AXIS_Y * MM, z_mm * MM))
        obj.data.transform(p @ Matrix.Rotation(math.radians(7.5), 4, "X") @ p.inverted())
    return obj


# Body: 50 x 115 plan (y -65..+50), radius 8, chamfered bottom edge
if VARIANT == "no_chamfer":
    body = rr_loft("Body", [(25, 57.5, 8, 0), (25, 57.5, 8, 40)], n=N)
else:
    body = rr_loft("Body", [(23, 55.5, 6, 0), (25, 57.5, 8, 2), (25, 57.5, 8, 40)], n=N)
body.data.transform(Matrix.Translation((0.0, -7.5 * MM, 0.0)))
r_cradle = 36.0 if VARIANT == "cradle_tight" else 36.5
boolean(body, phase(cylinder("Cradle", r_cradle * MM, -30 * MM, 30 * MM, AXIS_Y * MM, 48 * MM,
                             seg=SEG, axis="X")), "DIFFERENCE")
boolean(body, box("Slot", (-20.5 * MM, -60.5 * MM, 30 * MM), (20.5 * MM, -57.5 * MM, 41 * MM)),
        "DIFFERENCE")
rename(clean(body), "Body")

# Tape roll: outer radius 36, bore radius 19, x -12..+12
x_t = 12.5 if VARIANT == "tape_wide" else 12.0
if VARIANT == "tape_no_bore":
    tape = lathe_x("Tape", [(0, -x_t), (36, -x_t), (36, x_t), (0, x_t)], AXIS_Y, AXIS_Z, seg=SEG)
else:
    tape = lathe_x("Tape", [(19, -x_t), (36, -x_t), (36, x_t), (19, x_t)], AXIS_Y, AXIS_Z,
                   seg=SEG, closed=True)
rename(phase(tape, AXIS_Z), "Tape")

# Hub: core radius 18.5 between flanges of radius 24 (x 12.5..14 each side), axle bore radius 4
r_bore = 0 if VARIANT == "hub_no_bore" else 4
if VARIANT == "hub_no_flanges":
    prof = [(18.5, -14), (18.5, 14)]
else:
    prof = [(24, -14), (24, -12.5), (18.5, -12.5), (18.5, 12.5), (24, 12.5), (24, 14)]
if r_bore:
    hub = lathe_x("Hub", [(r_bore, -14)] + prof + [(r_bore, 14)], AXIS_Y, AXIS_Z, seg=SEG, closed=True)
else:
    hub = lathe_x("Hub", [(0, -14)] + prof + [(0, 14)], AXIS_Y, AXIS_Z, seg=SEG)
rename(phase(hub, AXIS_Z), "Hub")

# Blade: x -20..+20, y -60..-58, from z 30.5 to a serrated top, valleys z 46 at x = -20, -16 ...,
# peaks z 48 at x = -18, -14 ...
xs = [x / 1.0 for x in range(-20, 21, 2)]
if VARIANT == "blade_no_teeth":
    tops = [48.0] * len(xs)
elif VARIANT == "teeth_shifted":  # peaks where the valleys should be
    tops = [48.0 if i % 2 == 0 else 46.0 for i in range(len(xs))]
else:
    tops = [46.0 if i % 2 == 0 else 48.0 for i in range(len(xs))]
z_bl = 30.0 if VARIANT == "blade_on_floor" else 30.5
rename(strip_plate("Blade", xs, tops, z_bl, -60, -58), "Blade")
