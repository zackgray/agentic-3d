"""The harness's scene report: compact, generic facts about every mesh object, plus problems.

Generic only (owner's rule, 2026-11-17): manifold, pieces, self-intersection, normals, hygiene,
transforms, and contact between parts. Nothing here knows a task's checks or expected values.
Lengths are metres in world space, the scene's own unit, measured on the evaluated mesh. h2 reported
millimetres and agents read them as metres: 10 of 18 failures were built 1,000x too large.
"""
import array
import zlib

import bmesh
import bpy

from check_scene import Scene
from harness_circles import describe as round_features
from harness_outlines import describe as flat_outlines
from harness_patterns import describe as repeated
from harness_shape import revolved
from checks_core import inside, min_vertex_gap, self_overlaps, shell_count
from mathutils.bvhtree import BVHTree

TOUCH = 0.00002  # 0.02 mm: closer than this counts as touching
NEAR = 0.001     # pairs whose bounding boxes are further apart than 1 mm are not measured


def fmt(v):
    """Metres to 0.01 mm, trailing zeros dropped."""
    s = f"{v:.5f}".rstrip("0").rstrip(".") if abs(v) < 1e4 else f"{v:.4g}"
    return "0" if s in ("-0", "") else s


def bounds(bm):
    co = [v.co for v in bm.verts]
    return [min(p[i] for p in co) for i in range(3)], [max(p[i] for p in co) for i in range(3)]


def levels(values, cap=16):
    """Distinct values to 0.01 mm, or None if there are more than cap."""
    seen = sorted({round(v * 1e5) for v in values})
    return None if len(seen) > cap else [fmt(s / 1e5) for s in seen]


def where(points):
    """ ' at x a..b y a..b z a..b' around the given points, so the agent can find what's flagged."""
    pts = list(points)
    if not pts:
        return ""
    return " at " + " ".join(f"{a} {fmt(min(p[i] for p in pts))}..{fmt(max(p[i] for p in pts))}"
                             for i, a in enumerate("xyz"))


def mid(e):
    return (e.verts[0].co + e.verts[1].co) / 2


def object_problems(o, bm):
    """(text, kind, count) per problem. kind is a fixed label, so the harness tells problems apart
    without parsing the text (h5 parsed it, and merged digit-suffixed object names)."""
    out = []
    m = o.matrix_world
    if max(abs(m[i][j] - (1.0 if i == j else 0.0)) for i in range(4) for j in range(4)) > 1e-6:
        out.append(("transforms not applied", "transforms", 1))
    open_e = [e for e in bm.edges if not e.is_manifold]
    if open_e:
        out.append((f"{len(open_e)} non-manifold edges" + where(mid(e) for e in open_e), "open", len(open_e)))
    shells = shell_count(bm)
    if shells != 1:
        out.append((f"{shells} separate pieces", "pieces", shells))
    flipped = sum(1 for e in bm.edges if len(e.link_loops) == 2 and e.link_loops[0].vert == e.link_loops[1].vert)
    if flipped:
        out.append((f"inconsistent normals on {flipped} edges", "flipped", flipped))
    elif not open_e and bm.calc_volume(signed=True) <= 0:
        out.append(("normals point inward", "inward", 1))
    dup = list(bmesh.ops.find_doubles(bm, verts=bm.verts, dist=1e-7)["targetmap"])
    if dup:
        out.append((f"{len(dup)} coincident vertices" + where(v.co for v in dup), "coincident", len(dup)))
    short = [e for e in bm.edges if e.calc_length() < 1e-7]
    if short:
        out.append((f"{len(short)} zero-length edges" + where(mid(e) for e in short), "short", len(short)))
    flat = [f for f in bm.faces if f.calc_area() < 1e-10]
    if flat:
        out.append((f"{len(flat)} zero-area faces (area under 1e-10 m^2)"
                    + where(f.calc_center_median() for f in flat), "flat", len(flat)))
    loose = sum(1 for v in bm.verts if not v.link_edges) + sum(1 for e in bm.edges if not e.link_faces)
    if loose:
        out.append((f"{loose} loose vertices/edges", "loose", loose))
    hits = self_overlaps(bm)
    if hits:
        out.append((f"{hits} self-intersecting face pairs", "selfhit", hits))
    return out


def pair_problem(a, b, bma, bmb, ba, bb):
    """(text, kind, count) for a pair of objects, or None."""
    if any(ba[0][i] > bb[1][i] + NEAR or bb[0][i] > ba[1][i] + NEAR for i in range(3)):
        return None
    ta, tb = BVHTree.FromBMesh(bma, epsilon=0.0), BVHTree.FromBMesh(bmb, epsilon=0.0)
    pairs = ta.overlap(tb)
    if pairs:
        bma.faces.ensure_lookup_table()
        at = where(bma.faces[i].calc_center_median() for i, _j in pairs)
        return f"{a} and {b} intersect ({len(pairs)} face pairs){at}", "intersect", len(pairs)
    if bma.verts and inside(tb, bma.verts[0].co):
        return f"{a} is inside {b}", "a_in_b", 1
    if bmb.verts and inside(ta, bmb.verts[0].co):
        return f"{b} is inside {a}", "b_in_a", 1
    gaps = [g for g in (min_vertex_gap(bma, tb), min_vertex_gap(bmb, ta)) if g is not None]
    if gaps and min(gaps) < TOUCH:
        return f"{a} and {b} touch (gap {fmt(min(gaps))} m)", "touch", 1
    return None


def shape_lines(bm, lo, hi):
    """The opening read's shape facts for one object: a revolved part's outline, or its Z levels and
    flat outlines; then round holes and posts off that axis, then repeated features."""
    bm.verts.index_update()
    rev = revolved(bm)
    if rev:
        k, out, centre = rev
        return out + round_features(bm, (k, centre)) + repeated(bm, lo, hi)
    z = levels([v.co.z for v in bm.verts])
    return ([f"  z levels: {', '.join(z) if z else 'many'}"] + flat_outlines(bm, lo, hi)
            + round_features(bm) + repeated(bm, lo, hi))


def fingerprint(s, names):
    """A checksum of every mesh's world-space vertices, so the harness can tell a call that changed
    the scene from one that only inspected it."""
    crc = 0
    for n in names:
        bm = s.bm(n)
        crc = zlib.crc32(f"{n}:{len(bm.verts)}:{len(bm.faces)};".encode(), crc)
        crc = zlib.crc32(array.array("f", [c for v in bm.verts for c in v.co]).tobytes(), crc)
    return crc


def report(detail=False):
    """One line per mesh object, then the problems. detail adds distinct Z and radial levels, for
    reading an existing model without writing inspection code.

    Returns (text, problems, fingerprint); problems is [[key, count], ...], each key naming the
    objects and the kind of problem exactly."""
    bpy.context.view_layer.update()
    s = Scene()
    names = s.mesh_names()
    if not names:
        return "Scene: no mesh objects.", [], 0
    lines, problems, box = [f"Scene (metres): {len(names)} mesh objects"], [], {}
    for n in names:
        o, bm = s.obj(n), s.bm(n)
        if not bm.verts:
            lines.append(f"{n}: empty mesh")
            problems.append((f"{n}: empty mesh", f"{n}|empty", 1))
            continue
        lo, hi = bounds(bm)
        box[n] = (lo, hi)
        ext = " ".join(f"{a} {fmt(lo[i])}..{fmt(hi[i])}" for i, a in enumerate("xyz"))
        lines.append(f"{n}: {len(bm.faces)} faces; {ext}")
        if detail:
            lines += shape_lines(bm, lo, hi)
        problems += [(f"{n}: {t}", f"{n}|{k}", c) for t, k, c in object_problems(o, bm)]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a in box and b in box:
                p = pair_problem(a, b, s.bm(a), s.bm(b), box[a], box[b])
                if p:
                    problems.append((p[0], f"{a}|{b}|{p[1]}", p[2]))
    lines.append("Problems: " + ("none" if not problems else ""))
    lines += [f"- {t}" for t, _k, _c in problems]
    return "\n".join(lines), [[k, c] for _t, k, c in problems], fingerprint(s, names)
