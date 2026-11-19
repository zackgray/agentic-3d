"""Starting scene for r06: the approved pen, before the revision.

Runs inside Blender on the empty scene. Pen: lathed about the X axis, tip at x = 0. Tip cone
x 0..15 (r 0.5 -> 5), barrel x 15..125 (r 5), end cap x 125..140 (r 5.5, flat end), and a clip bar
on top of the end cap: x 127..139, y -1.5..1.5, top at z = 7, fused into the cap.
"""
from geom import MM, boolean, box, lathe, rename
from geom_r import Z_TO_X, xform

pen = xform(lathe("Pen", [(0, 0), (0.5 * MM, 0), (5 * MM, 15 * MM), (5 * MM, 125 * MM),
                          (5.5 * MM, 125 * MM), (5.5 * MM, 140 * MM), (0, 140 * MM)], seg=96), Z_TO_X)
boolean(pen, box("Clip", (127 * MM, -1.5 * MM, 4.5 * MM), (139 * MM, 1.5 * MM, 7 * MM)), "UNION")
rename(pen, "Pen")
