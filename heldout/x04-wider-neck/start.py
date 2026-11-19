"""Starting scene for x04 (held out): the lotion bottle and cap the client has already approved.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Bottle: a rounded-rectangle
body 56 x 40 mm, 8 mm corners, z 0..100, a neck 18 mm across up to z = 116 and a 10 mm bore down to
z = 90. Cap: hollow, 23 mm across, 2 mm side wall, 3 mm top wall, rim at z = 104, ceiling 0.5 mm over
the neck top and 0.5 mm clear of the neck side.
"""
from geom import MM, boolean, cylinder, lathe, loft, rename, rounded_rect

body = rounded_rect(28 * MM, 20 * MM, 8 * MM)
bottle = loft("Bottle", [(body, 0.0), (body, 100 * MM)])
boolean(bottle, cylinder("Neck", 9 * MM, 99 * MM, 116 * MM, seg=96), "UNION")
boolean(bottle, cylinder("Bore", 5 * MM, 90 * MM, 117 * MM, seg=64), "DIFFERENCE")
rename(bottle, "Bottle")

lathe("Cap", [(0, 119.5 * MM), (11.5 * MM, 119.5 * MM), (11.5 * MM, 104 * MM), (9.5 * MM, 104 * MM),
              (9.5 * MM, 116.5 * MM), (0, 116.5 * MM)], seg=96)
