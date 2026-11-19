"""Starting scene for x07: the TV remote the client has already approved, before the revision.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Remote: 45 x 160 x 18 mm,
10 mm plan corners, 3 mm rounded top edge, a 30 x 60 x 1 mm battery-door recess underneath, and a
power-button pocket 14 mm across and 3 mm deep at (0, +50). Button: 13 mm across, z 15.5..20, so
0.5 mm clear of the pocket floor and wall.
"""
from geom_x2 import remote, remote_button

remote([(50, 14)])
remote_button(50, 13)
