"""Starting scene for w06 (held out): the approved turned bud vase, before the revision.

Runs inside Blender on the empty scene. Vase: one solid lathe about Z. Foot ring r 30 from z 0 to 8,
a step in to r 24, a straight cone out to the shoulder (r 36 at z 60), a straight cone in to the
neck (r 12 at z 110), a straight neck to the top at z 150 with its outer lip edge rounded 1.5 mm, and
a 12 mm bore from the top down to a flat floor at z 40. No booleans: the shoulder is a single
vertex ring, so selecting it and moving it is a clean edit.
"""
from geom_wc import bud_vase

bud_vase()
