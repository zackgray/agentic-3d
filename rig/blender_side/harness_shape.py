"""Shape facts for the harness's opening read (h7): a revolved part's paired profile, and round
holes and posts. Generic: computed the same way for any mesh, with no knowledge of any task.

From the revision-transcript mining (runs/_mining/findings.md): 125 of the 210 calls agents spent
inspecting before their first edit rebuilt one of these two facts.
"""
import math

import numpy as np

AXES = "xyz"
Q = 1e5            # levels and radii are compared at 0.01 mm
MIN_RING = 8       # vertices for a ring to count as round
MAX_GAP = math.radians(60)
EVEN = 1.5         # a ring's widest angular gap over its narrowest: lathed rings are even
REVOLVED = 0.7     # share of vertices on rings for a part to count as revolved
SHARP = math.radians(25)
MAX_POINTS = 24
MAX_RINGS = 120   # beyond this (threads, knurls) the outline isn't walked: it would be too long to list anyway
ARC_TOL = 2e-5     # points within 0.02 mm of one circle (levels are read to 0.01 mm): a gentle polyline isn't an arc


def fmt(v):
    s = f"{v:.5f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def verts_array(bm):
    return np.array([v.co[:] for v in bm.verts], dtype=float)


def sharp_graph(bm):
    """Vertex index -> neighbours along sharp edges (faces meeting at more than SHARP)."""
    sharp = {}
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > SHARP:
            a, b = e.verts[0].index, e.verts[1].index
            sharp.setdefault(a, []).append(b)
            sharp.setdefault(b, []).append(a)
    return sharp


def components(graph):
    """Connected vertex sets of an adjacency dict."""
    seen, out = set(), []
    for start in graph:
        if start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in graph[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(comp)
    return out


# --- revolved profile -------------------------------------------------------------------------

def _rings_about(V, k):
    """Ring id per vertex (-1 if off every ring) for the axis along coordinate k, plus the axis
    line's position and each ring's (axial level, radius)."""
    i, j = [a for a in range(3) if a != k]
    lev = np.round(V[:, k] * Q).astype(np.int64)
    centres = []
    for L in np.unique(lev):
        P = V[lev == L]
        if len(P) >= MIN_RING:
            centres.append(((P[:, i].min() + P[:, i].max()) / 2, (P[:, j].min() + P[:, j].max()) / 2))
    if not centres:
        return None
    ci, cj = np.median(np.array(centres), axis=0)
    di, dj = V[:, i] - ci, V[:, j] - cj
    rad = np.round(np.hypot(di, dj) * Q).astype(np.int64)
    ang = np.arctan2(dj, di)
    ids, rings = np.full(len(V), -1), []
    keys = {}
    for n, key in enumerate(zip(lev.tolist(), rad.tolist())):
        keys.setdefault(key, []).append(n)
    keys = _merge_close(keys)
    for (L, R), members in keys.items():
        if R == 0:
            ok = True
        elif len(members) >= MIN_RING:
            a = np.sort(ang[members])
            gaps = np.diff(np.concatenate([a, [a[0] + 2 * math.pi]]))
            ok = gaps.max() < MAX_GAP and gaps.max() < EVEN * gaps.min()  # rib corners pair up unevenly
        else:
            ok = False
        if ok:
            ids[members] = len(rings)
            rings.append((L / Q, R / Q))
    return ids, rings, (ci, cj)


def _merge_close(keys):
    """Join groups at one level whose radii are within 0.02 mm: a boolean can leave a ring's
    vertices a hair off its radius, which would split one ring in two."""
    out = {}
    for L, R in sorted(keys, key=lambda k: (k[0], -len(keys[k]))):
        home = next((k for k in out if k[0] == L and abs(k[1] - R) <= 2), None)
        out.setdefault(home or (L, R), []).extend(keys[(L, R)])
    return out


def _between(p, a, b):
    """True if outline point p lies on the segment a-b, strictly inside it."""
    (r0, z0), (r1, z1), (r, z) = a, b, p
    seg = math.hypot(r1 - r0, z1 - z0)
    cross = (r1 - r0) * (z - z0) - (z1 - z0) * (r - r0)
    dot = (r - r0) * (r1 - r0) + (z - z0) * (z1 - z0)
    return seg > 0 and abs(cross) < ARC_TOL * seg and 0 < dot < seg * seg


def _order(ids, rings, edges):
    """The rings in outline order, walking ring-to-ring mesh edges; None unless that walk is a
    single path or loop."""
    adj = {n: set() for n in range(len(rings))}
    for a, b in edges:
        ra, rb = ids[a], ids[b]
        if ra >= 0 and rb >= 0 and ra != rb:
            adj[ra].add(rb)
            adj[rb].add(ra)
    pt = lambda n: (rings[n][1], rings[n][0])
    for a in adj:  # an edge that skips a ring lying on its line is a shortcut, not a profile step
        for b in list(adj[a]):
            if any(_between(pt(c), pt(a), pt(b)) for c in adj if c not in (a, b)):
                adj[a].discard(b)
                adj[b].discard(a)
    if any(len(s) > 2 for s in adj.values()) or any(not s for s in adj.values()):
        return None
    ends = [n for n, s in adj.items() if len(s) == 1]
    if len(ends) not in (0, 2):
        return None
    lowest = lambda n: (rings[n][1] != 0, rings[n][0], rings[n][1])  # an axis point, then lowest level
    start = min(ends or adj, key=lowest)
    order, prev = [start], None
    while True:
        nxt = [n for n in adj[order[-1]] if n != prev and n != order[0]]
        if not nxt:
            break
        prev = order[-1]
        order.append(min(nxt, key=lambda n: (rings[n][1], rings[n][0])))
    return (order, not ends) if len(order) == len(rings) else None


def _capped(bm, ids, ring):
    """True if some face lies wholly on this ring: a flat cap with no centre vertex."""
    return any(all(ids[v.index] == ring for v in f.verts) for f in bm.faces)


def _simplify(pts):
    """Drop points lying on the straight line between their neighbours."""
    out = list(pts)
    changed = True
    while changed and len(out) > 2:
        changed = False
        for n in range(1, len(out) - 1):
            (r0, z0), (r1, z1), (r2, z2) = out[n - 1], out[n], out[n + 1]
            cross = (r1 - r0) * (z2 - z0) - (z1 - z0) * (r2 - r0)
            if abs(cross) < ARC_TOL * math.hypot(r2 - r0, z2 - z0):  # within 0.02 mm of the line
                del out[n]
                changed = True
                break
    return out


def _arc(a, b, c):
    """(centre, radius) of the circle through three outline points, or None if they're in line."""
    (x1, y1), (x2, y2), (x3, y3) = a, b, c
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-15:
        return None
    s1, s2, s3 = x1 * x1 + y1 * y1, x2 * x2 + y2 * y2, x3 * x3 + y3 * y3
    ux = (s1 * (y2 - y3) + s2 * (y3 - y1) + s3 * (y1 - y2)) / d
    uy = (s1 * (x3 - x2) + s2 * (x1 - x3) + s3 * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    return ((ux, uy), r) if r < 4 * math.hypot(x3 - x1, y3 - y1) else None  # nearly straight: no arc


def _with_arcs(pts):
    """Outline text, writing each run of 4+ points on one circle as 'arc r R to (end)'."""
    out, n = [], 0
    while n < len(pts):
        best = None
        for m in range(len(pts) - 1, n + 2, -1):
            fit = _arc(pts[n], pts[(n + m) // 2], pts[m])
            run = pts[n:m + 1]
            if fit and all(abs(math.hypot(p[0] - fit[0][0], p[1] - fit[0][1]) - fit[1]) < ARC_TOL
                           for p in run) and all(  # short steps: a box's four corners are on a circle too
                    math.hypot(p[0] - q[0], p[1] - q[1]) < 0.6 * fit[1] for p, q in zip(run, run[1:])):
                best = (m, fit[1])
                break
        out.append(f"({fmt(pts[n][0])}, {fmt(pts[n][1])})")
        if best:
            m, r = best
            out.append(f"arc r {fmt(r)} to ({fmt(pts[m][0])}, {fmt(pts[m][1])})")
            n = m + 1
        else:
            n += 1
    return ", ".join(out)


def revolved(bm):
    """(axis index, text lines, ring vertex mask) for a part revolved about X, Y or Z, or None."""
    if len(bm.verts) < 2 * MIN_RING:
        return None
    V = verts_array(bm)
    best = None
    for k in range(3):
        got = _rings_about(V, k)
        if got is None:
            continue
        ids, rings, centre = got
        share = (ids >= 0).mean()
        if sum(1 for _L, R in rings if R) >= 2 and share >= REVOLVED and (best is None or share > best[0]):
            best = (share, k, ids, rings, centre)
    if best is None:
        return None
    _share, k, ids, rings, centre = best
    i, j = [AXES[a] for a in range(3) if a != k]
    edges = [(e.verts[0].index, e.verts[1].index) for e in bm.edges]
    walk = _order(ids, rings, edges) if len(rings) <= MAX_RINGS else None
    where = f"revolved about {AXES[k].upper()} through {i} {fmt(centre[0])} {j} {fmt(centre[1])}"
    if walk is not None:
        order, closed = walk
        pts = [(rings[n][1], rings[n][0]) for n in order]
        if not closed:  # an open outline ending off the axis may end on a flat cap face
            if pts[0][0] > 0 and _capped(bm, ids, order[0]):
                pts.insert(0, (0.0, pts[0][1]))
            if pts[-1][0] > 0 and _capped(bm, ids, order[-1]):
                pts.append((0.0, pts[-1][1]))
        pts = _simplify(pts)
        body = _with_arcs(pts)
        if body.count("(") <= MAX_POINTS:
            lines = [f"  {where}; outline (r, {AXES[k]}): {body}"]
        else:
            lines = [f"  {where}; outline has {len(pts)} points (curved)"]
    elif len(rings) > MAX_POINTS:
        lines = [f"  {where}; {len(rings)} rings (not listed)"]
    else:
        by_level = {}
        for L, R in rings:
            by_level.setdefault(L, []).append(R)
        body = "; ".join(f"{fmt(L)}: {', '.join(fmt(r) for r in sorted(rs))}" for L, rs in sorted(by_level.items()))
        lines = [f"  {where}; radii at each {AXES[k]} level: {body}"]
    off = ids < 0
    if off.any():
        P = V[off]
        span = " ".join(f"{a} {fmt(P[:, n].min())}..{fmt(P[:, n].max())}" for n, a in enumerate(AXES))
        lines.append(f"  {int(off.sum())} vertices off the revolved shape, at {span}")
    return k, lines, centre
