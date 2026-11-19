"""Starting scene for r01: the bottle and cap the client has already approved, before the revision.

Runs inside Blender on the empty scene (rig.blender.make_starting_scene). Bottle: a solid lathed
bottle. Cap: a hollow cap, 34 mm across, 30 mm tall (z 128..158), 1.5 mm side wall, 3 mm top wall, 0.5 mm clear of the neck top.
"""
from geom import MM, lathe

lathe("Bottle", [(0, 0), (30 * MM, 0), (30 * MM, 110 * MM), (12 * MM, 125 * MM), (12 * MM, 154.5 * MM),
                 (0, 154.5 * MM)], seg=96)
lathe("Cap", [(0, 158 * MM), (17 * MM, 158 * MM), (17 * MM, 128 * MM), (15.5 * MM, 128 * MM),
              (15.5 * MM, 155 * MM), (0, 155 * MM)], seg=96)
