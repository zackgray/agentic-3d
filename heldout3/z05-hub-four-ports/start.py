"""Starting scene for z05 (held out): the approved desktop charging hub, before the revision.

Runs inside Blender on the empty scene. Hub: a solid rounded slab 140 x 70 mm (x -70..70,
y -35..35), z 0..28, 10 mm plan corner radii, a 4 mm fillet round the top perimeter edge. Three
port recesses in the front (-Y) face: 14 mm wide x 7 mm tall, 1.5 mm corners, centred at z = 12 and
x = -30, 0, 30 (30 mm pitch), 15 mm deep. A 12 mm button recess, 1 mm deep, on top at (45, 0).
"""
from geom_zc import hub

hub([-30, 0, 30])
