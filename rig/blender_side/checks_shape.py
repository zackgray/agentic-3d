"""Shape checks that measure the model itself: enclosed volume, and ray probes.

A ray probe fires a ray at the scene and compares where it first hits with where the reference
surface is. One probe set measures holes, pockets, wall thickness, fillet radii and orientation
without the check knowing how the model was built.
"""
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from check_scene import mm


def check_volume(s, c):
    """Enclosed volume against the expected value +- a relative tolerance. Unsigned: inverted
    normals are the topology check's finding, so one defect fails one check."""
    got = abs(s.bm(c["object"]).calc_volume(signed=True)) * 1e9
    want, rel = c["mm3"], c.get("rel_tol", 0.02)
    return abs(got - want) <= rel * want, {"volume_mm3": round(got, 1), "expected_mm3": want,
                                            "rel_tol": rel}


def check_ray_probe(s, c):
    """Each probe: origin [m], dir, and either hit = expected distance [m] or hit = false (must miss).

    Rays test the named objects (per probe, else per check, else every mesh object) and report the
    first hit.
    """
    trees = {}

    def tree_list(names):
        for n in names:
            if n not in trees and s.obj(n) is not None:
                trees[n] = BVHTree.FromBMesh(s.bm(n), epsilon=0.0)
        return [trees[n] for n in names if n in trees]

    tol = c.get("tol", 0.0003)
    out, ok = [], True
    for p in c["probes"]:
        origin, direction = Vector(p["origin"]), Vector(p["dir"]).normalized()
        best = None
        for t in tree_list(p.get("objects") or c.get("objects") or s.mesh_names()):
            loc, _n, _i, dist = t.ray_cast(origin, direction)
            if loc is not None and (best is None or dist < best):
                best = dist
        want = p["hit"]
        good = best is None if want is False else (best is not None and abs(best - want) <= tol)
        ok = ok and good
        out.append({"name": p.get("name", ""), "passed": good,
                    "hit_mm": None if best is None else mm(best),
                    "expected_mm": "miss" if want is False else mm(want)})
    return ok, {"tol_mm": mm(tol), "probes": out}
