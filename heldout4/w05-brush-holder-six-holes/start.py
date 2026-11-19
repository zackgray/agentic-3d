"""Starting scene for w05 (held out): the approved makeup-brush holder, before the revision.

Runs inside Blender on the empty scene. Holder: a solid turned puck 90 mm across (r 45), z 0..50,
its top outer edge rounded 4 mm. A 20 mm centre well and four 16 mm brush holes on a 28 mm pitch
radius at 0, 90, 180 and 270 degrees from +X, all 38 mm deep (flat floors at z = 12). Built as one
lathe (the well is part of the profile) turned half a segment off the axes, then four hole booleans.
Unturned, the top face's radial edges pass exactly through the cutters' outermost vertices and the
exact boolean leaves coincident vertices there; turned, the start has none (checked 2026-11-18).
"""
from geom_wc import brush_holder

brush_holder([0, 90, 180, 270])
