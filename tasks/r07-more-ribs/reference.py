"""Reference revision for r07, applied to the starting scene. Runs inside Blender via exec_code.py.

The grip is rebuilt with 16 ribs of the same profile, every 22.5 deg, the rib on +X kept in place.
VARIANT selects deliberately broken revisions (set by verify_checks).
"""
from geom import MM, boolean, cylinder, rename
from geom_r import remove, rib_box

VARIANT = globals().get("VARIANT", "good")

if VARIANT != "unchanged":
    angles, half_w, z0 = [22.5 * k for k in range(16)], 1.0, 0.0
    if VARIANT == "added_four":  # four ribs squeezed in at 45/135/225/315, the old 12 left alone
        angles = [30 * k for k in range(12)] + [45, 135, 225, 315]
    elif VARIANT == "rotated":  # 16 evenly spaced, but none on +X
        angles = [11.25 + a for a in angles]
    elif VARIANT == "thin_ribs":  # 16 ribs at 3/4 width, keeping the total rib width
        half_w = 0.75
    elif VARIANT == "rebuilt_centred":  # rebuilt from a centred primitive: z -40..40
        z0 = -40.0
    remove("Grip")
    grip = cylinder("Grip", 12 * MM, z0 * MM, (z0 + 80) * MM, seg=128)
    for a in angles:
        boolean(grip, rib_box("Rib", 11 * MM, 13.5 * MM, half_w * MM, (z0 + 10) * MM, (z0 + 70) * MM, a),
                "UNION")
    rename(grip, "Grip")
