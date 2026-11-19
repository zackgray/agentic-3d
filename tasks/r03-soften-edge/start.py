"""Starting scene for r03: the approved housing cover, before the revision.

Runs inside Blender on the empty scene. Cover: an open-bottom rounded box, 100 x 60 mm outside
(x -50..50, y -30..30), z 0..30, 8 mm vertical corner radii, 2 mm side walls and a 2 mm top
(cavity 96 x 56 mm with 6 mm corner radii, open at z = 0, ceiling at z = 28). All other edges sharp.
"""
from geom import MM, boolean, rename
from geom_r import slab

cover = slab("Cover", 50 * MM, 30 * MM, 8 * MM, 0.0, 30 * MM)
boolean(cover, slab("Cavity", 48 * MM, 28 * MM, 6 * MM, -1 * MM, 28 * MM), "DIFFERENCE")
rename(cover, "Cover")
