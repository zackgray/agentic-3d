"""Starting scene for y06 (held out): the small speaker box the client has already approved.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Speaker: a box 140 x 120 mm
in plan (X x Y) and 200 mm tall, standing on the ground plane (z 0..200), centred on the origin, with
6 mm rounded vertical corners, and a round recess 100 mm across and 4 mm deep in the front (-Y)
face, centred at x = 0, z = 110.
"""
from geom_yc import speaker

speaker()
