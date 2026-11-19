"""Reference model for w01, built by hand to prove the checks. Runs inside Blender via exec_code.py.

Hand shower head: one lathe (body with a filleted top edge, fused neck with a chamfered top),
minus the inlet bore and two polar rings of blind nozzle holes in the underside. All exact
booleans. VARIANT selects deliberately broken versions (set by verify_checks).
"""
from geom import MM, boolean, cylinder, rename
from geom_m import clean, join
from geom_wa import arc, lathe_mm, polar_holes

VARIANT = globals().get("VARIANT", "good")
COARSE = VARIANT == "coarse"
SEG = 24 if COARSE else 96
N = 6 if COARSE else 16  # points per quarter circle in the fillet

side_top = 5 if VARIANT == "fillet_inside_height" else 10  # misread: fillet taken out of the 10 mm
top = side_top + 5
if VARIANT == "no_fillet":
    rim = [(32, side_top), (32, top)]
elif VARIANT == "chamfer_not_fillet":
    rim = [(32, side_top), (27, top)]
else:
    fr = 3 if VARIANT == "fillet_r3" else 5
    rim = [(32, top - fr)] + arc(32 - fr, top - fr, fr, 0, 90, N)[1:]
    if fr != 5:
        rim = [(32, side_top)] + rim
body_prof = [(0, 0), (32, 0)] + rim
neck_top = [(9, 34), (0, 34)] if VARIANT == "no_neck_chamfer" else [(9, 32.5), (7.5, 34), (0, 34)]

if VARIANT == "floating_neck":
    head = lathe_mm("Body", body_prof + [(0, top)], seg=SEG)
    neck = lathe_mm("Neck", [(0, top + 0.5), (9, top + 0.5)] + neck_top, seg=SEG)
    head = join("ShowerHead", [head, neck])
else:
    head = lathe_mm("ShowerHead", body_prof + [(9, top)] + neck_top, seg=SEG)

if VARIANT != "bore_through":
    boolean(head, cylinder("Bore", 5 * MM, 7 * MM, 35 * MM, seg=SEG), "DIFFERENCE")
else:
    boolean(head, cylinder("Bore", 5 * MM, -1 * MM, 35 * MM, seg=47), "DIFFERENCE")

hole_seg = SEG if COARSE else 48
phase = 0.0
if VARIANT in ("outer_ring_on_axes", "nozzles_through"):
    hole_seg, phase = 48, 3.75  # keeps cutter vertices off the lathe's radial edges (clean boolean)
if VARIANT != "no_nozzles":
    outer_start = 0 if VARIANT == "outer_ring_on_axes" else 15
    ceiling = 15.5 if VARIANT == "nozzles_through" else 4
    polar_holes(head, 12, 22, outer_start, 1.5, -1, ceiling, seg=hole_seg, phase=phase)
    if VARIANT != "no_inner_ring":
        polar_holes(head, 6, 11, 0, 1.5, -1, ceiling, seg=hole_seg, phase=phase)

rename(clean(head), "ShowerHead")
