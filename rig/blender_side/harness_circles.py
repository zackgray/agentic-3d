"""Round holes and posts for the harness's opening read (h7). Generic: any closed loop of sharp
edges that is a flat circle, paired into a wall when two loops share an axis and radius, then
grouped when walls repeat. Nothing here knows any task.
"""
import math

import numpy as np

from harness_shape import AXES, Q, components, fmt, sharp_graph

MIN_LOOP = 8
FLAT = 0.005     # out-of-plane and out-of-round tolerance, as a share of the radius
MAX_GAP = math.radians(45)  # widest angular gap between loop vertices: corner arcs alone aren't a circle
MAX_LISTED = 8
MAX_GROUPS = 6


def _loops(bm):
    """Closed loops of sharp edges, as vertex index lists. Only loops where every vertex has
    exactly two sharp edges: a loop that branches into another feature is skipped."""
    sharp = sharp_graph(bm)
    return [c for c in components(sharp) if len(c) >= MIN_LOOP and all(len(sharp[v]) == 2 for v in c)]


def _circle(P):
    """(centre, axis unit vector, radius) if the points are a flat circle, else None."""
    c = P.mean(axis=0)
    _u, _s, vt = np.linalg.svd(P - c)
    n, e1, e2 = vt[2], vt[0], vt[1]
    x, y = (P - c) @ e1, (P - c) @ e2
    A = np.column_stack([x, y, np.ones_like(x)])  # least-squares circle: x^2 + y^2 = 2ax + 2by + k
    (a2, b2, k), *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    a, b = a2 / 2, b2 / 2
    r = math.sqrt(max(k + a * a + b * b, 0.0))
    if r <= 0:
        return None
    if np.abs((P - c) @ n).max() > FLAT * r or np.abs(np.hypot(x - a, y - b) - r).max() > FLAT * r:
        return None
    ang = np.sort(np.arctan2(y - b, x - a))
    if np.diff(np.concatenate([ang, [ang[0] + 2 * math.pi]])).max() > MAX_GAP:
        return None
    big = int(np.argmax(np.abs(n)))
    if n[big] < 0:
        n = -n
    return c + a * e1 + b * e2, n, r


def _kind(bm, loop, centre, n):
    """'hole' when the wall next to the loop faces the axis, 'post' when it faces away."""
    ring, score = set(loop), 0.0
    for v in loop:
        for e in bm.verts[v].link_edges:
            if e.other_vert(bm.verts[v]).index not in ring:
                continue
            f = min(e.link_faces, key=lambda f: abs(np.dot(f.normal[:], n)))  # the wall side
            out = np.array(((e.verts[0].co + e.verts[1].co) / 2)[:]) - centre
            out -= np.dot(out, n) * n
            score += float(np.dot(f.normal[:], out))
    return "hole" if score < 0 else "post"


def _axis_name(n):
    big = int(np.argmax(np.abs(n)))
    if abs(n[big]) > 0.999:
        return AXES[big]
    return "tilted"


def walls(bm, skip_axis=None):
    """Round features as dicts: kind, axis name, radius, centre across the axis, span along it.
    skip_axis=(k, (ci, cj)) drops loops on a revolved part's own axis (its outline covers them)."""
    bm.verts.ensure_lookup_table()
    V = np.array([v.co[:] for v in bm.verts], dtype=float)
    found = []
    for loop in _loops(bm):
        got = _circle(V[loop])
        if got is None:
            continue
        centre, n, r = got
        name = _axis_name(n)
        if name in AXES:
            k = AXES.index(name)
            across = tuple(round(centre[a] * Q) for a in range(3) if a != k)
            along = centre[k]
        else:  # the foot of the axis line nearest the origin, so both ends of one wall agree
            n = np.round(n, 2)
            n /= np.linalg.norm(n)
            along = float(np.dot(centre, n))
            k, across = None, tuple(round(c * Q / 10) * 10 for c in centre - along * n)
        if skip_axis and k == skip_axis[0] and all(abs(a / Q - b) < 2 / Q for a, b in zip(across, skip_axis[1])):
            continue
        found.append({"kind": _kind(bm, loop, centre, n), "axis": name, "k": k, "r": round(r * Q), "n": n,
                      "across": across, "along": along})
    merged = {}
    for f in found:  # two loops on one axis line with one radius are the two ends of one wall
        key = (f["kind"], f["axis"], f["r"], f["across"], None if f["k"] is not None else tuple(np.round(f["n"], 2)))
        m = merged.setdefault(key, {**f, "lo": f["along"], "hi": f["along"]})
        m["lo"], m["hi"] = min(m["lo"], f["along"]), max(m["hi"], f["along"])
    return list(merged.values())


def _centres(pts, axis):
    """Compact text for a set of centres across the axis: (±a, ±b) when mirror-symmetric."""
    if len(pts) > 1:
        xs = sorted({abs(p[0]) for p in pts})
        ys = sorted({abs(p[1]) for p in pts})
        if len(xs) == 1 and len(ys) == 1:
            want = {(sx * xs[0], sy * ys[0]) for sx in (1, -1) for sy in (1, -1)}
            if set(pts) == want:
                fa = lambda v: ("±" if v else "") + fmt(v / Q)
                return f"({fa(xs[0])}, {fa(ys[0])})"
    shown = ", ".join("(" + ", ".join(fmt(c / Q) for c in p) + ")" for p in sorted(pts)[:MAX_LISTED])
    more = f" and {len(pts) - MAX_LISTED} more" if len(pts) > MAX_LISTED else ""
    return f"{shown}{more}"


def describe(bm, skip_axis=None):
    """One line listing the round holes and posts, or no line."""
    feats = walls(bm, skip_axis)
    if not feats:
        return []
    groups, tilted = {}, {}
    for f in feats:
        if f["k"] is None:  # off the X, Y and Z axes: summarised per kind and radius
            mid = np.array(f["across"], dtype=float) / Q + (f["lo"] + f["hi"]) / 2 * f["n"]
            tilted.setdefault((f["kind"], f["r"]), []).append(mid)
            continue
        key = (f["kind"], f["axis"], f["r"], round(f["lo"] * Q), round(f["hi"] * Q))
        groups.setdefault(key, []).append(f["across"])
    parts = []
    for (kind, axis, r, lo, hi), pts in sorted(groups.items(), key=lambda g: (g[0][1], -g[0][2])):
        count = f" x{len(pts)}" if len(pts) > 1 else ""
        dims = ",".join(a for a in AXES if a != axis)
        span = f"{axis} {fmt(lo / Q)}..{fmt(hi / Q)}" if lo != hi else f"{axis} {fmt(lo / Q)}"
        parts.append(f"{kind}{count} r {fmt(r / Q)} at {dims} {_centres(pts, axis)}, {span}")
    for (kind, r), mids in tilted.items():
        P = np.array(mids)
        if len(mids) == 1:
            parts.append(f"{kind} r {fmt(r / Q)} on a tilted axis, centred at ({', '.join(fmt(c) for c in P[0])})")
            continue
        span = " ".join(f"{a} {fmt(P[:, n].min())}..{fmt(P[:, n].max())}" for n, a in enumerate(AXES))
        parts.append(f"{kind} x{len(mids)} r {fmt(r / Q)} on tilted axes, centred within {span}")
    more = f"; and {len(parts) - MAX_GROUPS} more groups" if len(parts) > MAX_GROUPS else ""
    return ["  round: " + "; ".join(parts[:MAX_GROUPS]) + more]
