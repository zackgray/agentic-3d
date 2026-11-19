"""Reference model for m03, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Dock: a lofted rounded block minus the socket, plus the charging post. Handle and brush head are
lathes of closed (r, z) profiles; the button pocket is a radial cutter and the bristle block a box,
both exact booleans. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, boolean, box, cylinder, loft, rename, rounded_rect
from geom_m import cyl_along, mm_lathe

VARIANT = globals().get("VARIANT", "good")


def dock():
    plan = rounded_rect(30 * MM, 25 * MM, 10 * MM)
    d = loft("Dock", [(plan, 0.0), (plan, 30 * MM)])
    sock = 13 if VARIANT == "tight_socket" else 13.5
    boolean(d, cylinder("Socket", sock * MM, 8 * MM, 31 * MM, seg=96), "DIFFERENCE")
    if VARIANT != "no_post":
        boolean(d, cylinder("Post", 4 * MM, 7 * MM, 20 * MM, seg=48), "UNION")
    return rename(d, "Dock")


def handle():
    z0 = 8 if VARIANT == "handle_on_floor" else 8.5
    taper = [(13, 185)] if VARIANT == "no_taper" else [(13, 170), (6, 185)]
    prof = [(0, 20.5), (4.5, 20.5), (4.5, z0), (13, z0)] + taper + [(2.5, 185),
            (2.5, 200), (0, 200)]
    h = mm_lathe("Handle", prof)
    if VARIANT != "no_button_pocket":
        cut = cyl_along("Pocket", 4.5 * MM, (0.0, -11 * MM, 110 * MM), (0.0, -20 * MM, 110 * MM), seg=48)
        boolean(h, cut, "DIFFERENCE")
    return rename(h, "Handle")


def button():
    y0 = 11 if VARIANT == "button_flush" else 11.5
    b = cyl_along("Button", 4 * MM, (0.0, -y0 * MM, 110 * MM), (0.0, -(y0 + 3) * MM, 110 * MM), seg=48)
    return rename(b, "Button")


def brush_head():
    z0 = 185 if VARIANT == "head_seated" else 185.5
    prof = [(0, z0 + 15), (3, z0 + 15), (3, z0), (5, z0), (5, 245), (0, 245)]
    h = mm_lathe("BrushHead", prof, seg=64)
    if VARIANT != "no_bristles":
        boolean(h, box("Bristles", (-5 * MM, -12 * MM, 222 * MM), (5 * MM, -4 * MM, 242 * MM)), "UNION")
    return rename(h, "BrushHead")


dock()
handle()
button()
brush_head()
