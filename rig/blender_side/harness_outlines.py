"""Flat-level outlines for the harness's opening read (h7): each flat loop of sharp edges that spans
most of the part, with its extent and corner radii, grouped across levels when identical. Generic:
nothing here knows any task.

From the revision-transcript mining: about 13 of the 210 inspection calls rebuilt a level's outline
or its corner radius.
"""
import math

import numpy as np

from harness_circles import _circle, _kind
from harness_shape import AXES, ARC_TOL, components, fmt, sharp_graph

SPAN = 0.5        # an outline covers at least half the part's extent on both of its axes
TURN = math.radians(30)
MAX_ENTRIES = 6


def _walk(loop, sharp):
    order, prev = [loop[0]], None
    while len(order) < len(loop):
        nxt = [w for w in sharp[order[-1]] if w != prev]
        if not nxt or nxt[0] == order[0]:
            break
        prev = order[-1]
        order.append(nxt[0])
    return order if len(order) == len(loop) else None


def _arc_radius(P):
    """Radius of the circle through the run's first, middle and last points if every point lies
    on it and the steps are short, else None."""
    a, b, c = P[0], P[len(P) // 2], P[-1]
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    if abs(d) < 1e-18:
        return None
    sa, sb, sc = a @ a, b @ b, c @ c
    ux = (sa * (b[1] - c[1]) + sb * (c[1] - a[1]) + sc * (a[1] - b[1])) / d
    uy = (sa * (c[0] - b[0]) + sb * (a[0] - c[0]) + sc * (b[0] - a[0])) / d
    r = math.hypot(a[0] - ux, a[1] - uy)
    if np.abs(np.hypot(P[:, 0] - ux, P[:, 1] - uy) - r).max() > ARC_TOL:
        return None
    if np.linalg.norm(np.diff(P, axis=0), axis=1).max() > 0.6 * r:
        return None
    return r


def _corners(P):
    """Text for a closed 2D outline's corners: radii of its arcs, or square corners."""
    keep = []
    for k in range(len(P)):  # drop points a boolean left part-way along a straight edge
        u, v = P[k] - P[k - 1], P[(k + 1) % len(P)] - P[k]
        if abs(u[0] * v[1] - u[1] * v[0]) > 1e-4 * np.linalg.norm(u) * np.linalg.norm(v) or u @ v < 0:
            keep.append(k)
    P = P[keep]
    n = len(P)
    cap = 0.5 * np.ptp(P, axis=0).min()  # no corner is rounder than half the outline's width
    turn = []
    for k in range(n):
        u, v = P[k] - P[k - 1], P[(k + 1) % n] - P[k]
        cos = u @ v / max(np.linalg.norm(u) * np.linalg.norm(v), 1e-30)
        turn.append(math.acos(max(-1.0, min(1.0, cos))))
    start = int(np.argmax(turn)) if max(turn) > TURN else 0  # start on a sharp corner if any
    P = np.roll(P, -start, axis=0)
    radii, k = [], 0
    while k < n:
        m = n
        while m > k + 3 and not (_arc_radius(P[k:m]) or cap + 1) <= cap:
            m -= 1
        if m > k + 3:  # 4+ points: any 3 points lie on some circle
            radii.append(_arc_radius(P[k:m]))
            k = m - 1 if m < n else n
        else:
            k += 1
    sharp = sum(1 for t in turn if t > TURN)
    if not radii:
        return f"{sharp} square corners" if sharp else ""
    rs = []
    for r in sorted(radii):  # one radius per corner size: a boolean's split arcs fit a hair apart
        if not rs or r > rs[-1] * 1.05:
            rs.append(r)
    text = "corners r " + ", ".join(fmt(r) for r in rs)
    return text + (f", {sharp} square" if sharp else "")


def describe(bm, lo, hi):
    """One line of outlines, or none."""
    bm.verts.ensure_lookup_table()
    V = np.array([v.co[:] for v in bm.verts], dtype=float)
    size = np.array(hi) - np.array(lo)
    sharp = sharp_graph(bm)
    found = {}
    for comp in components(sharp):
        if len(comp) < 4 or any(len(sharp[v]) != 2 for v in comp) or _circle(V[comp]) is not None:
            continue
        P = V[comp]
        flat = [k for k in range(3) if np.ptp(P[:, k]) < ARC_TOL]
        if len(flat) != 1:
            continue
        k = flat[0]
        i, j = [a for a in range(3) if a != k]
        if np.ptp(P[:, i]) < SPAN * size[i] or np.ptp(P[:, j]) < SPAN * size[j]:
            continue
        order = _walk(comp, sharp)
        if order is None:
            continue
        Q = V[order][:, [i, j]]
        centre = V[order].mean(axis=0)
        n = np.zeros(3)
        n[k] = 1.0
        inner = _kind(bm, order, centre, n) == "hole"
        ext = f"{AXES[i]} {fmt(Q[:, 0].min())}..{fmt(Q[:, 0].max())} {AXES[j]} {fmt(Q[:, 1].min())}..{fmt(Q[:, 1].max())}"
        key = (k, ext, _corners(Q), inner)
        found.setdefault(key, []).append(P[0, k])
    if not found:
        return []
    parts = []
    for (k, ext, corners, inner), levels in sorted(found.items(), key=lambda f: (f[0][0], min(f[1]))):
        at = ", ".join(dict.fromkeys(fmt(v) for v in sorted(levels)))
        parts.append(f"{AXES[k]} {at}{' inner' if inner else ''}: {ext}" + (f", {corners}" if corners else ""))
    more = f"; and {len(parts) - MAX_ENTRIES} more" if len(parts) > MAX_ENTRIES else ""
    return ["  flat outlines: " + "; ".join(parts[:MAX_ENTRIES]) + more]
