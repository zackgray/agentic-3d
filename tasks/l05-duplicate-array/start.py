"""Starting scene for l05: the single product the client has already approved.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Product: a solid bottle
body 50 mm across and 120 mm tall (z 0..120) on the world Z axis, with a full-height label flat
20 mm from its axis facing -Y.
"""
from geom import MM
from geom_l import flat_prism, place

place(flat_prism("Product", 25 * MM, 20 * MM, 0.0, 120 * MM, n=64), rot_deg=-90)
