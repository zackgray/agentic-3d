"""Reference revision for r03, applied to the starting scene. Runs inside Blender via exec_code.py.

The cover is rebuilt with a 3 mm rolling-ball fillet round its top outside perimeter edge (a loft of
inward-offset outlines), cavity unchanged. VARIANT selects deliberately broken revisions.
"""
import bpy

from geom import MM, boolean, rename
from geom_r import fillet_slab, remove, slab

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    remove("Cover")
    fr, steps, ceiling = 3 * MM, 12, 28 * MM
    if VARIANT == "too_small":  # 2 mm instead of 3 mm
        fr = 2 * MM
    elif VARIANT == "chamfer":  # a 3 mm flat bevel instead of a round
        steps = 1
    elif VARIANT == "ceiling_lowered":  # rebuilt with the top wall 3 mm thick
        ceiling = 27 * MM
    cover = fillet_slab("Cover", 50 * MM, 30 * MM, 8 * MM, 0.0, 30 * MM, fr, steps=steps)
    boolean(cover, slab("Cavity", 48 * MM, 28 * MM, 6 * MM, -1 * MM, ceiling), "DIFFERENCE")
    rename(cover, "Cover")
