"""Starting scene for y05 (held out): the cutting board the client has already approved.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Board: a flat slab
360 x 240 mm (X x Y), 18 mm thick, standing on the ground plane (z 0..18), centred on the origin,
with 20 mm rounded plan corners and square top and bottom edges.
"""
from geom_yc import board

board()
