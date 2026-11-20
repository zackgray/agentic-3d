"""Generic modeling helpers the harness puts in the agent's namespace. Metres throughout.

They exist to cut the code an agent writes on every task (making a mesh object, booleans, a lathe,
cleanup), not to solve any task. None of them knows about the checks.
"""
import math

import bmesh
import bpy
from checks_core import inside
from mathutils import Matrix
from mathutils.bvhtree import BVHTree


def remove(*names):
    """Delete objects by name (missing names are ignored)."""
    for n in names:
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)


def new_object(name, bm):
    """A mesh object from a bmesh (freed), linked to the scene. Replaces any object of that name."""
    remove(name)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def cylinder(name, radius, z0, z1, segments=64, radius_top=None, center=(0.0, 0.0)):
    """Closed cylinder (or cone/frustum with radius_top) on the Z axis from z0 to z1."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius,
                          radius2=radius if radius_top is None else radius_top, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(center[0], center[1], (z0 + z1) / 2))
    return new_object(name, bm)


def box(name, lo, hi):
    """Axis-aligned box from corner lo (x, y, z) to corner hi."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = [lo[i] + (v.co[i] + 0.5) * (hi[i] - lo[i]) for i in range(3)]
    return new_object(name, bm)


def lathe(name, profile, segments=64):
    """Revolve a closed outline about the Z axis. profile is [(r, z), ...] in order around the
    outline (r >= 0); points with r == 0 sit on the axis and become single vertices. Gives a closed
    mesh with outward normals."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))] * segments)
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segments),
                                        r * math.sin(2 * math.pi * k / segments), z)) for k in range(segments)])
    n = len(profile)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        if a[0] is a[1] and b[0] is b[1]:
            continue  # both ends on the axis
        for k in range(segments):
            k2 = (k + 1) % segments
            quad = [a[k], a[k2], b[k2], b[k]]
            face = [v for j, v in enumerate(quad) if v is not quad[j - 1]]
            if len(face) >= 3:
                bm.faces.new(face)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_object(name, bm)


def _apply_modifier(obj, mod):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    obj.modifiers.remove(mod)
    old = obj.data
    obj.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def _shells(bm):
    """Faces grouped into edge-connected pieces."""
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        seen.add(f.index)
        shell, stack = [], [f]
        while stack:
            g = stack.pop()
            shell.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(shell)
    return out


def _orient(bm):
    """Point every piece's normals outward, except a piece that sits inside another without
    touching it: that is a cavity, and its normals point into it. h5 turned every piece outward,
    which fills a cavity built as an inner shell; a mirrored (inside-out) piece is still fixed."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.index_update()
    shells = _shells(bm)
    if len(shells) < 2 or len(shells) > 200:
        return
    trees = []
    for shell in shells:
        verts = list({v for f in shell for v in f.verts})
        idx = {v: i for i, v in enumerate(verts)}
        trees.append((verts, BVHTree.FromPolygons([v.co for v in verts],
                                                  [[idx[v] for v in f.verts] for f in shell], epsilon=0.0)))
    for i, shell in enumerate(shells):
        p = trees[i][0][0].co
        depth = sum(1 for j, (_vs, t) in enumerate(trees)
                    if j != i and inside(t, p) and not t.overlap(trees[i][1]))
        if depth % 2:
            bmesh.ops.reverse_faces(bm, faces=shell)


def _outward(obj):
    """Orient a mesh's normals (see _orient). A mesh mirrored by swapping two coordinates is inside
    out, and an inside-out cutter makes the exact boolean silently cut nothing (h4: a lamp's cross
    hole, 14 calls)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    _orient(bm)
    bm.to_mesh(obj.data)
    bm.free()


WARNINGS = []  # helper warnings this call; the harness won't end a run on a call that has any


def warn(msg):
    WARNINGS.append(msg)
    print("warning: " + msg)


HUGE = 10.0  # m: no hand-held product comes near this; a millimetre size written as metres does
_scale_held = []  # one entry once the scale warning has held a run open


def scale_check():
    """On a done=true call, warn once per run if any mesh is over HUGE across. h7 lost 4 of
    DeepSeek's 7 failed runs (and some of Sonnet's) to 1,000x builds that ended on a clean first
    call before the report's bounding boxes were read."""
    if _scale_held:
        return
    big = []
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.vertices:
            pts = [o.matrix_world @ v.co for v in o.data.vertices]
            span = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3))
            if span > HUGE:
                big.append(f"{o.name} ({span:.3g} m)")
    if big:
        _scale_held.append(1)
        warn("very large parts: " + ", ".join(big[:5]) + ". Sizes are in metres; a size given in "
             "millimetres is written 30 * mm. If this scale is intended, call again with done=true.")

def _volume(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    v = bm.calc_volume(signed=True)
    bm.free()
    return v


def boolean(target, other, op="DIFFERENCE"):
    """Apply an exact boolean (DIFFERENCE, UNION or INTERSECT) of other onto target, then delete
    other. Both may be objects or names. Both operands' normals are oriented first, and a boolean
    that leaves the volume unchanged prints a warning."""
    target = bpy.data.objects[target] if isinstance(target, str) else target
    other = bpy.data.objects[other] if isinstance(other, str) else other
    for o in (target, other):
        _outward(o)
    bpy.context.view_layer.update()
    before, cutter = _volume(target), abs(_volume(other))
    m = target.modifiers.new("bool", "BOOLEAN")
    m.operation, m.operand_type, m.object, m.solver = op, "OBJECT", other, "EXACT"
    _apply_modifier(target, m)
    bpy.data.objects.remove(other, do_unlink=True)
    after = _volume(target)
    # Unchanged against both operands: h5 compared with the target alone, so a small hole in a big
    # part read as unchanged.
    change = abs(after - before)
    if change <= 1e-15 + 1e-6 * abs(before) and change <= 1e-15 + 1e-3 * cutter:
        warn(f"boolean {op} on {target.name} left its volume unchanged; check that the operands "
             "overlap where intended")
    return target


def bevel(obj, width, segments=3, angle_deg=30.0):
    """Round every edge sharper than angle_deg with the given width, applied."""
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width, m.segments, m.limit_method, m.angle_limit = width, segments, "ANGLE", math.radians(angle_deg)
    return _apply_modifier(obj, m)


FLAT = 1e-10  # m^2: the scene report's zero-area threshold; cleanup must meet the same bar


def _clean(bm):
    """Merge doubles and dissolve degenerate geometry, widening the tolerance (0.1 um, 1 um, 10 um)
    only while faces under FLAT remain. Boolean slivers often survive the tightest pass; in h4,
    agents spent up to 13 calls hunting faces the report flagged and this cleanup had left."""
    for dist in (1e-7, 1e-6, 1e-5):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
        bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges)
        if not any(f.calc_area() < FLAT for f in bm.faces):
            return


def finish(obj):
    """Apply transforms, merge coincident vertices, remove degenerate geometry, make normals point
    outward. Call on every object before you finish."""
    obj = bpy.data.objects[obj] if isinstance(obj, str) else obj
    bpy.context.view_layer.update()  # matrix_world is stale after setting location/rotation/scale
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    _clean(bm)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    _orient(bm)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


EXPORTS = {f.__name__: f for f in (remove, new_object, cylinder, box, lathe, boolean, bevel, finish)}
EXPORTS["mm"] = 0.001  # unit constant: h3 lost 12 of 90 runs to sizes written in mm as metres
