"""Starting scene for r02: the approved packaging mock-up, before the revision.

Runs inside Blender on the empty scene. Carton: a solid block, 70 mm in X by 40 mm in Y by 100 mm
tall (x -35..35, y -20..20, z 0..100), all edges sharp.
"""
from geom import MM, box

box("Carton", (-35 * MM, -20 * MM, 0.0), (35 * MM, 20 * MM, 100 * MM))
