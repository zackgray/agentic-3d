"""Reference model for m01, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Every part is a lathe of a closed (r, z) profile in millimetres: the body carries the grip grooves,
the flare, the lens counterbore and the tail pocket in its profile. VARIANT selects broken versions.
"""
from geom_m import mm_lathe

VARIANT = globals().get("VARIANT", "good")


def body():
    prof = [(0, 8), (6.5, 8), (6.5, 3), (13, 3)]
    if VARIANT != "no_grooves":
        for c in (30, 40, 50, 60, 70, 80):
            prof += [(13, c - 1.5), (12, c - 1.5), (12, c + 1.5), (13, c + 1.5)]
    if VARIANT == "no_flare":  # a flat step up to the head instead of the cone
        prof += [(13, 110), (20, 110)]
    else:
        prof += [(13, 110), (20, 125)]
    prof += [(20, 150), (17, 150), (17, 146.5), (0, 146.5)]
    return mm_lathe("Body", prof)


def lens():
    z0 = 146.5 if VARIANT == "lens_touching" else 147
    return mm_lathe("Lens", [(0, z0), (16.5, z0), (16.5, z0 + 3), (0, z0 + 3)])


def bezel():
    z0 = 150 if VARIANT == "bezel_on_head" else 150.5
    if VARIANT == "solid_bezel":
        return mm_lathe("Bezel", [(0, z0), (21, z0), (21, z0 + 3.5), (0, z0 + 3.5)])
    return mm_lathe("Bezel", [(15.5, z0), (21, z0), (21, z0 + 3.5), (15.5, z0 + 3.5)], closed=True)


def button():
    r = 6.5 if VARIANT == "button_tight" else 6
    top = 8 if VARIANT == "button_flush" else 7.5
    return mm_lathe("Button", [(0, 0), (r, 0), (r, top), (0, top)], seg=64)


body()
lens()
bezel()
button()
