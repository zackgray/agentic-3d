"""Reference helpers for the held-out revision tasks y05-y06 (heldout2/). Runs inside Blender.

Same conventions as geom.py: world coordinates in metres, transforms left at identity.
"""
import math

from mathutils import Matrix

from geom import MM, boolean, cylinder, loft, rename, rounded_rect
from geom_x2 import remove

__all__ = ["MM", "board", "speaker", "remove"]


def board(corner_r=20.0, hole=None):
    """y05's cutting board: 360 x 240 mm, 18 mm thick (z 0..18), plan corners corner_r mm.
    hole = (x_mm, y_mm, diameter_mm, depth_mm) cuts a round hole down from the top face."""
    plan = rounded_rect(180 * MM, 120 * MM, corner_r * MM)
    obj = loft("Board", [(plan, 0.0), (plan, 18 * MM)])
    if hole:
        x, y, d, depth = hole
        z0 = -1.0 if depth >= 18 else 18 - depth
        boolean(obj, cylinder("Hole", d / 2 * MM, z0 * MM, 19 * MM, x * MM, y * MM, seg=64), "DIFFERENCE")
    return rename(obj, "Board")


def _recess_cutter(r, y0, y1, z):
    """A cylinder along +Y from y0 to y1 [m], axis at (x = 0, z)."""
    c = cylinder("Recess", r, y0, y1, seg=96)
    c.data.transform(Matrix.Rotation(-math.pi / 2, 4, "X"))  # +Z -> +Y
    c.data.transform(Matrix.Translation((0.0, 0.0, z)))
    return c


def speaker(lift=0.0, corner_r=6.0, recess=True, feet=None, foot_d=24.0, foot_h=10.0):
    """y06's speaker: box 140 x 120 x 200 mm (z lift..lift+200), plan corners corner_r mm, a round
    recess 100 mm across and 4 mm deep in the front (-Y) face centred at z = lift + 110.
    feet = [(x_mm, y_mm), ...] fuses cylinders foot_d across under the base, foot_h tall."""
    plan = rounded_rect(70 * MM, 60 * MM, corner_r * MM)
    obj = loft("Speaker", [(plan, lift * MM), (plan, (lift + 200) * MM)])
    if recess:
        boolean(obj, _recess_cutter(50 * MM, -61 * MM, -56 * MM, (lift + 110) * MM), "DIFFERENCE")
    for x, y in feet or []:
        foot = cylinder("Foot", foot_d / 2 * MM, (lift - foot_h) * MM, (lift + 1) * MM, x * MM, y * MM, seg=48)
        boolean(obj, foot, "UNION")
    return rename(obj, "Speaker")
