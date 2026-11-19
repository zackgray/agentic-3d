"""Repeated features for the harness's opening read (h7): ribs, slots, ports, feet. Generic: every
connected cluster of sharp edges is a feature; features identical up to a shift, or up to a turn
about the X, Y or Z axis through the part's centre, form a pattern. Reported with count, spacing,
start and one instance's extent. Nothing here knows any task.

From the revision-transcript mining: about 67 of the 210 inspection calls rebuilt a pattern.
"""
import math

import numpy as np

from harness_circles import _circle
from harness_shape import AXES, components, fmt, sharp_graph

TOL = 5e-5        # 0.05 mm: two features match if every vertex has a partner this close
MIN_VERTS = 4
MAX_SHARE = 0.5   # a cluster holding half the part's vertices is the part's own outline, not a feature
MAX_GROUPS = 4
MAX_FEATURES = 200


def _corners(comp, sharp, V):
    """The cluster's vertices without those sitting mid-way along a straight sharp edge: a boolean
    leaves extra vertices on some copies of a feature and not others."""
    keep = []
    for v in comp:
        nb = sharp[v]
        if len(nb) == 2:
            a, b = V[nb[0]] - V[v], V[nb[1]] - V[v]
            la, lb = np.linalg.norm(a), np.linalg.norm(b)
            if la and lb and np.dot(a, b) < -0.9999 * la * lb:
                continue
        keep.append(v)
    return keep


def _plane(P):
    """(unit normal, offset) if the points are flat, else None."""
    c = P.mean(axis=0)
    _u, sv, vt = np.linalg.svd(P - c)
    if sv[2] > 1e-6 * max(sv[0], 1e-30) * 1e3 and np.abs((P - c) @ vt[2]).max() > TOL:
        return None
    n = vt[2] if vt[2][int(np.argmax(np.abs(vt[2])))] > 0 else -vt[2]
    return n, float(c @ n)


def _stacked(A, B):
    """True if flat loops A and B lie in parallel planes, close, one over the other: the opening
    and the floor of one recess, or the base and top of one boss."""
    pa, pb = _plane(A), _plane(B)
    if pa is None or pb is None or abs(pa[0] @ pb[0]) < 0.999:
        return False
    n = pa[0]
    flat = lambda P: P - np.outer(P @ n, n)
    fa, fb = flat(A), flat(B)
    lo, hi = np.maximum(fa.min(axis=0), fb.min(axis=0)), np.minimum(fa.max(axis=0), fb.max(axis=0))
    size = max(np.ptp(fa, axis=0).max(), np.ptp(fb, axis=0).max())
    return bool((hi - lo >= -TOL).all()) and abs(pa[1] - pb[1]) < 2 * size


def _features(bm, V, lo, hi):
    """Features: sharp clusters that aren't round loops; flat loops stacked over one footprint are
    joined (a recess's opening and floor are one feature)."""
    sharp = sharp_graph(bm)
    comps = [c for c in components(sharp) if len(c) >= MIN_VERTS
             and not (all(len(sharp[v]) == 2 for v in c) and _circle(V[c]) is not None)]
    size = np.array(hi) - np.array(lo)
    comps = [c for c in comps if len(c) <= MAX_SHARE * len(V) and (np.ptp(V[c], axis=0) >= 0.9 * size).sum() < 2]
    loops = [n for n, c in enumerate(comps) if all(len(sharp[v]) == 2 for v in c)]
    parent = list(range(len(comps)))
    for x in loops:
        for y in loops:
            if x < y and parent[y] == y and _stacked(V[comps[x]], V[comps[y]]):
                parent[y] = parent[x]
    merged = {}
    for n, c in enumerate(comps):
        merged.setdefault(parent[n], []).extend(c)
    out = []
    for comp in merged.values():
        inside = set(comp)
        segs = np.array([(V[v], V[w]) for v in comp for w in sharp[v] if w in inside and v < w])
        if len(segs):
            out.append(Feature(V[_corners(comp, sharp, V)], segs))
    return out


class Feature:
    """A feature's corner points and its sharp edges (segments), with a length-weighted centre
    that doesn't drift with how densely a boolean happened to split its edges."""
    def __init__(self, pts, segs):
        self.pts, self.segs = pts, segs
        lengths = np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1)
        mids = segs.mean(axis=1)
        self.centre = (mids * lengths[:, None]).sum(axis=0) / max(lengths.sum(), 1e-30)

    def moved(self, f):
        g = Feature.__new__(Feature)
        g.pts, g.segs, g.centre = f(self.pts), f(self.segs.reshape(-1, 3)).reshape(self.segs.shape), f(self.centre[None])[0]
        return g


def _near_segments(P, S):
    """Each point's distance to the nearest segment."""
    a, b = S[:, 0], S[:, 1]
    ab = b - a
    t = np.clip(((P[:, None, :] - a[None]) * ab[None]).sum(axis=2) / np.maximum((ab * ab).sum(axis=1), 1e-30), 0, 1)
    return np.linalg.norm(P[:, None, :] - (a[None] + t[..., None] * ab[None]), axis=2).min(axis=1)


def _match(A, B):
    """True if every corner of each feature lies on the other's edges, within TOL."""
    if abs(len(A.segs) - len(B.segs)) > max(len(A.segs), len(B.segs)) // 2 + 2:
        return False
    if np.abs(np.ptp(A.pts, axis=0) - np.ptp(B.pts, axis=0)).max() > 4 * TOL and len(A.pts) == len(B.pts):
        return False
    return _near_segments(A.pts, B.segs).max() < TOL and _near_segments(B.pts, A.segs).max() < TOL


def _rotate(P, k, centre, theta):
    i, j = [a for a in range(3) if a != k]
    R = P.copy()
    di, dj = P[:, i] - centre[0], P[:, j] - centre[1]
    c, s = math.cos(theta), math.sin(theta)
    R[:, i] = centre[0] + c * di - s * dj
    R[:, j] = centre[1] + s * di + c * dj
    return R


def _mean_angle(F, k, centre):
    i, j = [a for a in range(3) if a != k]
    return math.atan2(F.centre[j] - centre[1], F.centre[i] - centre[0])


def _group(feats, same):
    """Lists of mutually matching features (two or more each), and every index used."""
    groups, used = [], set()
    for a in range(len(feats)):
        if a in used:
            continue
        g = [a] + [b for b in range(a + 1, len(feats)) if b not in used and same(feats[a], feats[b])]
        if len(g) > 1:
            used.update(g)
            groups.append([feats[n] for n in g])
    return groups, used


def _linear(g):
    """Text for features related by shifts."""
    c = np.array([m.centre for m in g])
    first = g[int(np.lexsort(np.round(c / TOL).T[::-1])[0])].pts  # lowest x, then y, then z
    ext = " ".join(f"{a} {fmt(first[:, k].min())}..{fmt(first[:, k].max())}" for k, a in enumerate(AXES))
    k = int(np.argmax(np.ptp(c, axis=0)))
    steps = np.diff(np.sort(c[:, k]))
    other = [a for a in range(3) if a != k]
    if np.ptp(c[:, other], axis=0).max() < TOL and np.ptp(steps) < TOL:
        where = f"along {AXES[k]}, pitch {fmt(steps.mean())}, centres {AXES[k]} {fmt(c[:, k].min())}..{fmt(c[:, k].max())}"
    elif _grid(c):
        where = _grid(c)
    else:
        shown = sorted(map(tuple, np.round(c, 5)))[:8]
        where = "centred at " + ", ".join("(" + ", ".join(fmt(v) for v in p) + ")" for p in shown)
    return f"x{len(c)} {where}; first at {ext}"


def _grid(c):
    """'in a 6 x 2 grid ...' when the centres fill an evenly spaced grid on two axes, else ''."""
    axes = [k for k in range(3) if np.ptp(c[:, k]) > TOL]
    if len(axes) != 2:
        return ""
    vals = []
    for k in axes:
        u = np.unique(np.round(c[:, k] / TOL).astype(np.int64)) * TOL
        steps = np.diff(u)
        if len(u) < 2 or np.ptp(steps) > 2 * TOL:
            return ""
        vals.append((k, u, steps.mean()))
    if len(vals[0][1]) * len(vals[1][1]) != len(c):
        return ""
    (a, ua, pa), (b, ub, pb) = vals
    return (f"in a {len(ua)} x {len(ub)} grid, pitch {AXES[a]} {fmt(pa)} {AXES[b]} {fmt(pb)}, centres "
            f"{AXES[a]} {fmt(c[:, a].min())}..{fmt(c[:, a].max())} {AXES[b]} {fmt(c[:, b].min())}..{fmt(c[:, b].max())}")


def _rotational(g, k, centre):
    """Text for features related by turns about the axis along coordinate k."""
    i, j = [AXES[a] for a in range(3) if a != k]
    a, b = [x for x in range(3) if x != k]
    deg = [(math.degrees(_mean_angle(m, k, centre)) + 360) % 360 for m in g]
    angles = sorted(deg)
    steps = np.diff(angles + [angles[0] + 360])
    first = g[int(np.argmin(deg))]
    theta = _mean_angle(first, k, centre)
    first = first.pts
    out = (first[:, a] - centre[0]) * math.cos(theta) + (first[:, b] - centre[1]) * math.sin(theta)
    across = np.abs(-(first[:, a] - centre[0]) * math.sin(theta) + (first[:, b] - centre[1]) * math.cos(theta))
    if np.ptp(steps) < 0.05:
        where = f"every {fmt(round(steps.mean(), 3))} deg from {fmt(round(angles[0], 3))} deg"
    else:
        where = "at " + ", ".join(fmt(round(x, 2)) for x in angles) + " deg"
    return (f"x{len(g)} about {AXES[k]} through {i} {fmt(centre[0])} {j} {fmt(centre[1])}, {where} "
            f"(angles from +{i} toward +{j}); each reaches {fmt(out.min())}..{fmt(out.max())} out along its centre line, "
            f"{AXES[k]} {fmt(first[:, k].min())}..{fmt(first[:, k].max())}, {fmt(2 * across.max())} wide")


def describe(bm, lo, hi):
    """One line describing repeated features, or none."""
    bm.verts.ensure_lookup_table()
    V = np.array([v.co[:] for v in bm.verts], dtype=float)
    feats = _features(bm, V, lo, hi)
    if not 2 <= len(feats) <= MAX_FEATURES:
        return []
    feats.sort(key=lambda F: tuple(np.round(F.centre, 5)))
    shift = lambda A, B: _match(A.moved(lambda P: P - A.centre), B.moved(lambda P: P - B.centre))
    centre3 = [(lo[a] + hi[a]) / 2 for a in range(3)]
    rules = [(None, None, shift)]
    for k in (2, 0, 1):
        c = [centre3[a] for a in range(3) if a != k]
        rules.append((k, c, lambda A, B, k=k, c=c: _match(
            B.moved(lambda P: _rotate(P, k, c, _mean_angle(A, k, c) - _mean_angle(B, k, c))), A)))
    parts, rest = [], feats
    while len(rest) >= 2:  # take the reading (a shift, or a turn about one axis) that gathers the most
        best = None
        for k, c, same in rules:
            g, used = _group(rest, same)
            if g and (best is None or max(map(len, g)) > max(map(len, best[2]))):
                best = (k, c, g, used)
        if best is None:
            break
        k, c, g, used = best
        parts += [_linear(x) if k is None else _rotational(x, k, c) for x in g]
        rest = [rest[n] for n in range(len(rest)) if n not in used]
    if not parts:
        return []
    more = f"; and {len(parts) - MAX_GROUPS} more patterns" if len(parts) > MAX_GROUPS else ""
    return ["  repeated: " + "; ".join(parts[:MAX_GROUPS]) + more]
