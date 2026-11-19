"""Screw-thread check by phase variance (see the brain page screw-thread-check-by-phase-variance)."""
import math

from check_scene import mm


def check_helical_thread(s, c):
    """The neck surface in the thread band must be a screw surface of the given pitch, any profile.

    On a helix, a vertex's radius depends only on its phase along the screw, (z/pitch - angle/2pi)
    mod 1. Binning vertices by phase, the share of radius variance the bins explain is near 1 for a
    helix and near 0 for stacked rings. One pitch at each end of the band is skipped (run-outs).
    """
    root, depth, pitch = c["root_radius"], c["depth"], c["pitch"]
    lo, hi = c["z_min"] + pitch, c["z_max"] - pitch
    pts, max_r = [], 0.0
    for v in s.bm(c["object"]).verts:
        x, y, z = v.co
        r = math.hypot(x, y)
        if lo <= z <= hi and r < root + 3 * depth:
            pts.append((math.atan2(y, x), z, r))
            max_r = max(max_r, r)
    detail = {"band_vertices": len(pts), "max_crest_radius_mm": mm(max_r),
              "expected_crest_radius_mm": mm(root + depth)}
    if len(pts) < 100:
        return False, detail
    mean = sum(p[2] for p in pts) / len(pts)
    total = sum((p[2] - mean) ** 2 for p in pts)
    if total == 0:
        detail["helix_explained_variance"] = 0.0
        return False, detail
    bins_n, best = c.get("bins", 36), 0.0
    for hand in (1, -1):
        bins = [[] for _ in range(bins_n)]
        for a, z, r in pts:
            phase = (z / pitch - hand * a / (2 * math.pi)) % 1.0
            bins[min(bins_n - 1, int(phase * bins_n))].append(r)
        within = sum(sum((r - sum(b) / len(b)) ** 2 for r in b) for b in bins if b)
        best = max(best, 1 - within / total)
    detail["helix_explained_variance"] = round(best, 3)
    ok = best >= c.get("min_explained", 0.8) and max_r >= root + 0.8 * depth
    return ok, detail
