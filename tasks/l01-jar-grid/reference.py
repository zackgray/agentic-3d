"""Reference layout for l01, built by hand to prove the checks. Runs inside Blender via exec_code.py.

A slab tray and twelve cylinders on a 4 x 3 grid at 70 mm pitch, 0.5 mm above the tray. VARIANT
selects deliberately broken layouts (set by verify_checks).
"""
from geom import MM, box, cylinder

VARIANT = globals().get("VARIANT", "good")

tray_top = 5 * MM if VARIANT == "thin_tray" else 10 * MM
box("Tray", (-150 * MM, -110 * MM, 0.0), (150 * MM, 110 * MM, tray_top))

pitch = 65 * MM if VARIANT == "wrong_pitch" else 70 * MM
gap = 0.0 if VARIANT == "touching_tray" else 0.5 * MM
radius = 23 * MM if VARIANT == "small_jars" else 25 * MM
cols, rows = (3, 4) if VARIANT == "transposed" else (4, 3)
count = 11 if VARIANT == "missing_jar" else 12
for k in range(count):
    row, col = divmod(k, cols)
    x = (col - (cols - 1) / 2) * pitch
    y = (row - (rows - 1) / 2) * pitch
    cylinder(f"Jar_{k + 1}", radius, tray_top + gap, tray_top + gap + 60 * MM, x, y, seg=64)
