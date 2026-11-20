"""Structural checks: which objects exist, transforms, bounds, mesh validity, overlaps, budgets."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from check_scene import mm


def check_objects(s, c):
    names = sorted(o.name for o in bpy.context.scene.objects if o.type == "MESH")
    want = sorted(c["expected"])
    return names == want, {"mesh_objects": names, "expected": want}


def check_transforms_applied(s, c):
    bad = {}
    for name in c["objects"]:
        m = s.obj(name).matrix_world
        err = max(abs(m[i][j] - (1.0 if i == j else 0.0)) for i in range(4) for j in range(4))
        if err > 1e-6:
            bad[name] = {"location": [mm(x) for x in m.translation], "max_deviation": round(err, 6)}
    return not bad, {"not_applied": bad}


def check_bbox(s, c):
    co = [v.co for v in s.bm(c["object"]).verts]
    if not co:  # an object with no geometry is the agent's failure, not a crash (void) of the check
        return False, {"no_vertices": c["object"]}
    lo = [min(p[i] for p in co) for i in range(3)]
    hi = [max(p[i] for p in co) for i in range(3)]
    tol = c.get("tol", 0.0005)
    ok = all(abs(lo[i] - c["min"][i]) <= tol and abs(hi[i] - c["max"][i]) <= tol for i in range(3))
    return ok, {"min_mm": [mm(x) for x in lo], "max_mm": [mm(x) for x in hi],
                "expected_min_mm": [mm(x) for x in c["min"]], "expected_max_mm": [mm(x) for x in c["max"]],
                "tol_mm": mm(tol)}


def check_watertight(s, c):
    out = {}
    for name in c["objects"]:
        out[name] = sum(1 for e in s.bm(name).edges if not e.is_manifold)
    return all(v == 0 for v in out.values()), {"non_manifold_edges": out}


def self_overlaps(bm):
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    faces = bm.faces
    hits = 0
    for i, j in tree.overlap(tree):
        if i >= j:
            continue
        if {v.index for v in faces[i].verts} & {v.index for v in faces[j].verts}:
            continue  # neighbours touch by construction
        hits += 1
    return hits


def check_self_intersection(s, c):
    out = {name: self_overlaps(s.bm(name)) for name in c["objects"]}
    return all(v == 0 for v in out.values()), {"intersecting_face_pairs": out}


def inside(tree, point, max_hits=10000):
    """Ray-parity test: is point inside the closed mesh behind tree? Skewed ray avoids edge hits.

    Each hop past a hit is scaled to the coordinates (mathutils is single precision, so a fixed tiny
    step stalls on a model built far too large), and the hop count is capped.
    """
    d = Vector((0.1234, 0.2345, 0.9643)).normalized()
    o, hits = Vector(point), 0
    while hits < max_hits:
        loc, _n, _i, _dist = tree.ray_cast(o, d)
        if loc is None:
            return hits % 2 == 1
        hits += 1
        o = loc + d * max(1e-6, 1e-5 * max(abs(c) for c in loc))
    return False


def min_vertex_gap(bm, tree):
    """Smallest distance from any vertex of bm to the surface behind tree."""
    best = None
    for v in bm.verts:
        hit = tree.find_nearest(v.co)
        if hit[0] is not None and (best is None or hit[3] < best):
            best = hit[3]
    return best


def check_no_overlap(s, c):
    """No crossing surfaces, no surfaces resting on each other, and neither object sealed inside the
    other. Crossing faces are found by BVH overlap, but faces lying exactly on each other aren't
    reliably reported by it (found 2026-11-17 on stacked boxes), so the check also measures the
    smallest vertex-to-surface gap both ways: under min_gap (default 0.02 mm) counts as touching."""
    bma, bmb = s.bm(c["a"]), s.bm(c["b"])
    a = BVHTree.FromBMesh(bma, epsilon=0.0)
    b = BVHTree.FromBMesh(bmb, epsilon=0.0)
    n = len(a.overlap(b))
    a_in_b = bool(bma.verts) and inside(b, bma.verts[0].co)
    b_in_a = bool(bmb.verts) and inside(a, bmb.verts[0].co)
    gaps = [g for g in (min_vertex_gap(bma, b), min_vertex_gap(bmb, a)) if g is not None]
    gap = min(gaps) if gaps else None
    touching = gap is not None and gap < c.get("min_gap", 0.00002)
    return n == 0 and not a_in_b and not b_in_a and not touching, {
        "intersecting_face_pairs": n, "a_inside_b": a_in_b, "b_inside_a": b_in_a,
        "min_gap_mm": None if gap is None else mm(gap), "touching": touching}


def check_face_budget(s, c):
    """max faces for one object, or for each of several (objects = [...])."""
    names = [c["object"]] if "object" in c else c["objects"]
    faces = {n: len(s.bm(n).faces) for n in names}
    ok = all(f <= c["max"] for f in faces.values())
    return ok, ({"faces": faces[names[0]], "max": c["max"]} if "object" in c else {"faces": faces, "max": c["max"]})


def check_topology(s, c):
    out, ok = {}, True
    for name in c["objects"]:
        bm = s.bm(name)
        flipped = 0
        for e in bm.edges:
            loops = list(e.link_loops)
            if len(loops) == 2 and loops[0].vert == loops[1].vert:
                flipped += 1
        r = {
            "degenerate_faces": sum(1 for f in bm.faces if f.calc_area() < 1e-10),
            "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
            "loose_edges": sum(1 for e in bm.edges if not e.link_faces),
            "inconsistent_normal_edges": flipped,
            "signed_volume_mm3": round(bm.calc_volume(signed=True) * 1e9, 1),
        }
        ok = ok and r["signed_volume_mm3"] > 0 and not any(
            r[k] for k in ("degenerate_faces", "loose_verts", "loose_edges", "inconsistent_normal_edges"))
        out[name] = r
    return ok, out


def shell_count(bm):
    seen, shells = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        shells += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                o = e.other_vert(cur)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
    return shells


def check_shells(s, c):
    """Each object must be one connected piece: a part that floats free of the rest is a defect."""
    out = {name: shell_count(s.bm(name)) for name in c["objects"]}
    return all(n == c.get("expected", 1) for n in out.values()), {"shells": out}
