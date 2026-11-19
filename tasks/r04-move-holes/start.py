"""Starting scene for r04: the approved mounting plate, before the revision.

Runs inside Blender on the empty scene. Plate: 120 x 80 mm (x -60..60, y -40..40), 6 mm thick
(z 0..6), 6 mm vertical corner radii, a 20 mm centre hole, and four 5 mm mounting holes at
(+-50, +-30) mm, all straight through.
"""
from geom import MM, boolean, cylinder, rename
from geom_r import slab

plate = slab("Plate", 60 * MM, 40 * MM, 6 * MM, 0.0, 6 * MM)
boolean(plate, cylinder("Hole", 10 * MM, -1 * MM, 7 * MM, seg=96), "DIFFERENCE")
for sx in (1, -1):
    for sy in (1, -1):
        boolean(plate, cylinder("Hole", 2.5 * MM, -1 * MM, 7 * MM, sx * 50 * MM, sy * 30 * MM, seg=48),
                "DIFFERENCE")
rename(plate, "Plate")
