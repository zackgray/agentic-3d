"""Starting scene for r08: the approved planter liner, before the revision.

Runs inside Blender on the empty scene. Liner: an open-top lathed cup, outside r 30, z 0..90, with a
2 mm side wall (inner r 28), a 2 mm floor (floor top at z = 2) and an 8 mm drain hole through the
floor centre.
"""
from geom import MM, lathe

lathe("Liner", [(4 * MM, 0), (30 * MM, 0), (30 * MM, 90 * MM), (28 * MM, 90 * MM), (28 * MM, 2 * MM),
                (4 * MM, 2 * MM)], seg=128, closed=True)
