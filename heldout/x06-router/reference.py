"""Reference model for x06, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Router: a rounded-corner slab with four feet unioned on, then one exact boolean with every cutter
(vent slots, rear ports, front LED holes, button pocket) joined into a single cutter object. The
button is a plain cylinder. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, box, boolean, cylinder, rename
from geom_m import clean, cyl_along, join, rounded_slab

VARIANT = globals().get("VARIANT", "good")
R = 0.5 if VARIANT == "sharp_corners" else 8
SLOTS = [-35, -25, -15, -5, 5, 15, 25, 35] if VARIANT == "eight_slots" else [-40, -30, -20, -10, 0, 10, 20, 30, 40]
SLOT_FLOOR = 32.5 if VARIANT == "shallow_slots" else 31
BACK = -1 if VARIANT == "ports_on_front" else 1  # +Y is the back face

body = rounded_slab("Router", 80 * MM, 55 * MM, R * MM, 4 * MM, 34 * MM)

if VARIANT != "no_feet":
    top = 3.5 if VARIANT == "floating_feet" else 5  # good: 1 mm into the body so the union fuses
    feet = [cylinder("Foot", 6 * MM, 0.0, top * MM, x * MM, y * MM, seg=48)
            for x in (-60, 60) for y in (-35, 35)]
    boolean(body, join("Feet", feet), "UNION")

cutters = []
if VARIANT != "no_slots":
    cutters += [box("Slot", ((x - 2) * MM, -30 * MM, SLOT_FLOOR * MM), ((x + 2) * MM, 30 * MM, 35 * MM))
                for x in SLOTS]
y_in, y_out = BACK * 43 * MM, BACK * 56 * MM
for x in (-40, -20):
    lo = ((x - 7) * MM, min(y_in, y_out), 15 * MM)
    hi = ((x + 7) * MM, max(y_in, y_out), 23 * MM)
    cutters.append(box("Port", lo, hi))
cutters.append(cyl_along("Power", 4.5 * MM, (20 * MM, y_in, 19 * MM), (20 * MM, y_out, 19 * MM), seg=48))
if VARIANT != "no_leds":
    cutters += [cyl_along("Led", 1.5 * MM, (x * MM, -50 * MM, 24 * MM), (x * MM, -56 * MM, 24 * MM), seg=24)
                for x in (-10, 0, 10)]
cutters.append(cylinder("Pocket", 6 * MM, 31 * MM, 35 * MM, 60 * MM, -35 * MM, seg=64))
boolean(body, join("Cutters", cutters), "DIFFERENCE")
rename(clean(body), "Router")

z0 = 31 if VARIANT == "button_resting" else 31.5
rename(cylinder("Button", 5.5 * MM, z0 * MM, 36 * MM, 60 * MM, -35 * MM, seg=64), "Button")
