"""Reference model for h07, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Jar and lid are lathes of closed (r, z) profiles in millimetres; the lid's top edge roundover is a
quarter arc in the profile. VARIANT selects deliberately broken versions (set by verify_checks).
"""
import math

from geom_m import mm_lathe

VARIANT = globals().get("VARIANT", "good")


def jar():
    if VARIANT == "solid_jar":
        prof = [(0, 0), (35, 0), (35, 70), (32, 70), (32, 85), (0, 85)]
        return mm_lathe("Jar", prof)
    floor = 1.5 if VARIANT == "thin_floor" else 3
    if VARIANT == "no_shoulder":  # straight-sided jar, no neck step
        prof = [(0, 0), (35, 0), (35, 85), (32.5, 85), (32.5, floor), (0, floor)]
        return mm_lathe("Jar", prof)
    prof = [(0, 0), (35, 0), (35, 70), (32, 70), (32, 85), (29.5, 85), (29.5, 67.5),
            (32.5, 67.5), (32.5, floor), (0, floor)]
    return mm_lathe("Jar", prof)


def lid():
    z0 = 70 if VARIANT == "lid_sitting" else 70.5
    bore = 32 if VARIANT == "tight_lid" else 32.5
    if VARIANT == "sharp_lid":
        top = [(35, 88)]
    else:  # 2 mm roundover: quarter arc centred at (r, z) = (33, 86)
        top = [(33 + 2 * math.cos(math.pi / 2 * k / 12), 86 + 2 * math.sin(math.pi / 2 * k / 12))
               for k in range(13)]
    if VARIANT == "lid_no_cavity":
        return mm_lathe("Lid", [(0, z0), (35, z0)] + top + [(0, 88)])
    prof = [(0, 85.5), (bore, 85.5), (bore, z0), (35, z0)] + top + [(0, 88)]
    return mm_lathe("Lid", prof)


jar()
lid()
