"""Starting scene for r07: the approved ribbed grip, before the revision.

Runs inside Blender on the empty scene. Grip: a solid cylinder r 12, z 0..80, with 12 axial ribs
evenly spaced every 30 deg starting on +X. Each rib is 2 mm wide with flat sides and a flat top
13.5 mm from the axis (1.5 mm proud), running z 10..70, fused into the cylinder.
"""
from geom import MM, boolean, cylinder, rename
from geom_r import rib_box

grip = cylinder("Grip", 12 * MM, 0.0, 80 * MM, seg=128)
for k in range(12):
    boolean(grip, rib_box("Rib", 11 * MM, 13.5 * MM, 1 * MM, 10 * MM, 70 * MM, 30 * k), "UNION")
rename(grip, "Grip")
