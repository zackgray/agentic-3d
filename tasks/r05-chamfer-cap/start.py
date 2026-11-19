"""Starting scene for r05: the approved jar cap, before the revision.

Runs inside Blender on the empty scene. Cap: a hollow lathed cap, 50 mm across (r 25), z 0..18,
2 mm side wall (inner r 23), 2.5 mm top (ceiling at z = 15.5), open at the bottom, all edges sharp.
"""
from geom import MM, lathe

lathe("Cap", [(0, 18 * MM), (25 * MM, 18 * MM), (25 * MM, 0), (23 * MM, 0), (23 * MM, 15.5 * MM),
              (0, 15.5 * MM)], seg=128)
