"""Reference helpers for the held-out tasks w03-w04 (heldout4/). Runs inside Blender (bpy, bmesh).

Same conventions as geom.py: world coordinates in metres, transforms left at identity. Outlines here
are radial functions sampled at shared polar angles, so a loft between two different sections
(a rounded square and a circle) joins points at the same angle about Z.
"""
import math

from mathutils import Matrix, Vector

from geom import MM, boolean, box, cylinder, loft, rounded_rect


def rsq_radius(t, h, r):
    """Distance from the centre to a rounded square (half-size h, corner radius r) at polar angle t."""
    t = t % (math.pi / 2)
    if t > math.pi / 4:
        t = math.pi / 2 - t
    c, s = math.cos(t), math.sin(t)
    if h * math.tan(t) <= h - r:
        return h / c
    cc = h - r
    d = cc * c + cc * s
    return d + math.sqrt(max(0.0, d * d - 2 * cc * cc + r * r))


def polar_angles(seg, tangents=()):
    """seg uniform angles from 0, plus the given tangent-point angles mirrored into all octants."""
    angles = {round(2 * math.pi * k / seg, 12) for k in range(seg)}
    for a in tangents:
        for q in range(4):
            for b in (a, math.pi / 2 - a):
                angles.add(round((q * math.pi / 2 + b) % (2 * math.pi), 12))
    return sorted(angles)


def outline(angles, radius_fn):
    return [(radius_fn(t) * math.cos(t), radius_fn(t) * math.sin(t)) for t in angles]


def candlestick(seg=96, h=30.0, r=12.0, chamfer=3.0, foot_top=25.0, top_z=120.0, top_r=15.0,
                top_square=None, well_floor=100.0, well_r=11.0, recess=True, twist_deg=0.0):
    """w03 candlestick: rounded-square foot with a 45-degree chamfered bottom edge, a straight-blend
    loft from the foot outline to a circle at the top, a blind candle socket from the top, and a shallow
    round recess in the underside. top_square=(h, r) lofts to a rounded square instead; twist_deg
    joins each foot point to the top point that many degrees further round."""
    cc = h - r  # corner-centre offset; the chamfer insets keep it fixed
    tang = [math.atan2(cc, h - i) for i in (0.0, chamfer)] if r > 0 else []
    if top_square:
        tang.append(math.atan2(top_square[0] - top_square[1], top_square[0]))
    ang = polar_angles(seg, tang)

    def foot(inset):
        return outline(ang, lambda t: rsq_radius(t, h - inset, max(0.0, r - inset)))

    top = outline(ang, (lambda t: rsq_radius(t, *top_square)) if top_square else (lambda t: top_r))
    if twist_deg:
        rot = Matrix.Rotation(math.radians(twist_deg), 2)
        top = [tuple(rot @ Vector(p)) for p in top]
    layers = []
    if chamfer > 0:
        layers.append(([(x * MM, y * MM) for x, y in foot(chamfer)], 0.0))
        layers.append(([(x * MM, y * MM) for x, y in foot(0.0)], chamfer * MM))
    else:
        layers.append(([(x * MM, y * MM) for x, y in foot(0.0)], 0.0))
    if foot_top > (chamfer if chamfer > 0 else 0):
        layers.append(([(x * MM, y * MM) for x, y in foot(0.0)], foot_top * MM))
    layers.append(([(x * MM, y * MM) for x, y in top], top_z * MM))
    obj = loft("Candlestick", layers)
    boolean(obj, cylinder("Socket", well_r * MM, well_floor * MM, (top_z + 5) * MM, seg=seg), "DIFFERENCE")
    if recess:
        boolean(obj, cylinder("Recess", 18 * MM, -1 * MM, 2 * MM, seg=seg), "DIFFERENCE")
    return obj


def rr_slab(name, h, r, z0, z1, cx=0.0, cy=0.0, angle_deg=0.0, n=16):
    """Rounded-square prism (half-size h, corner radius r, mm) from z0 to z1 (mm), turned by
    angle_deg about its own vertical axis and centred at (cx, cy) mm."""
    pts = [(x * MM, y * MM) for x, y in rounded_rect(h, h, r, n)]
    obj = loft(name, [(pts, z0 * MM), (pts, z1 * MM)])
    obj.data.transform(Matrix.Translation((cx * MM, cy * MM, 0.0)) @ Matrix.Rotation(math.radians(angle_deg), 4, "Z"))
    return obj


def coaster_holder(n=16, notch=True):
    """w04 holder: open-top rounded-square tray, outside 104 mm square r12 to z 25, inside 98 mm
    square r9 above a floor at z 3, with a 30 mm wide notch in the -Y wall down to z 12."""
    obj = rr_slab("Holder", 52, 12, 0, 25, n=n)
    boolean(obj, rr_slab("Cavity", 49, 9, 3, 26, n=n), "DIFFERENCE")
    if notch:
        boolean(obj, box("Notch", (-15 * MM, -55 * MM, 12 * MM), (15 * MM, -45 * MM, 26 * MM)), "DIFFERENCE")
    return obj
