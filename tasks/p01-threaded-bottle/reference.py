"""Reference model for p01, written by hand to prove the checks. Runs inside Blender via exec_code.py.

Both objects are lathes: rings of vertices stacked along Z, with the thread made by pushing neck
vertices outward along a helical profile. One closed grid per object means watertight by construction.
VARIANT selects deliberately broken versions for the check self-test (set by verify_checks).
"""
import math

import bmesh
import bpy

VARIANT = globals().get("VARIANT", "good")
SEG = 128
MM = 0.001


def thread_offset(theta, z, z0=178 * MM, z1=192 * MM, pitch=3 * MM, depth=1.2 * MM):
    if not z0 <= z <= z1:
        return 0.0
    frac = ((z - pitch * theta / (2 * math.pi)) / pitch) % 1.0
    tri = max(0.0, 1.0 - abs(frac - 0.5) * 2.0 / 0.8)  # triangular profile over 80% of the pitch
    if VARIANT == "flat_crest":  # a wide flat crest (trapezoid), still a valid helix
        tri = min(1.0, 2 * max(0.0, 1.0 - abs(frac - 0.5) * 2.0))
    if VARIANT == "rings":
        tri = max(0.0, 1.0 - abs(((z / pitch) % 1.0) - 0.5) * 2.0 / 0.8)
    run_in = min(1.0, (z - z0) / pitch, (z1 - z) / pitch)  # fade the thread in and out over one turn
    return depth * tri * max(0.0, run_in)


def lathe(name, profile, radial=lambda theta, z, r: r):
    """profile: list of (r, z) from one pole to the other; r == 0 marks a pole (single vertex)."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r == 0:
            rings.append([bm.verts.new((0.0, 0.0, z))])
            continue
        ring = []
        for i in range(SEG):
            t = 2 * math.pi * i / SEG
            rr = radial(t, z, r)
            ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(SEG):
            j = (i + 1) % SEG
            if len(a) == 1:
                bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def bottle():
    prof = [(0, 0.0), (35 * MM, 0.0), (35 * MM, 160 * MM)]
    for k in range(1, 16):  # cosine shoulder 160 -> 175 mm
        u = k / 15
        prof.append((14 * MM + 21 * MM * (1 + math.cos(math.pi * u)) / 2, (160 + 15 * u) * MM))
    for k in range(1, 101):  # 0.2 mm rows through the neck so the thread resolves
        prof.append((14 * MM, (175 + 0.2 * k) * MM))
    if VARIANT != "open":  # open: no top cap, so the mesh has a hole
        prof.append((0, 195 * MM))
    radial = (lambda t, z, r: r) if VARIANT == "no_thread" else (
        lambda t, z, r: r + thread_offset(t, z) if abs(r - 14 * MM) < 1e-9 else r)
    return lathe("Bottle", prof, radial)


def cap():
    inner_r = 15.5 * MM if VARIANT != "tight_cap" else 14.5 * MM  # tight: hits the thread crest
    prof = [(0, 197.5 * MM), (17 * MM, 197.5 * MM), (17 * MM, 175.5 * MM),
            (inner_r, 175.5 * MM), (inner_r, 195.5 * MM), (0, 195.5 * MM)]
    return lathe("Cap", prof)


b = bottle()
c = cap()
if VARIANT == "poke":  # a block crossing the shoulder surface, joined into the same mesh
    bm = bmesh.new()
    bm.from_mesh(b.data)
    block = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.scale(bm, vec=(12 * MM, 6 * MM, 6 * MM), verts=block)
    bmesh.ops.translate(bm, vec=(26 * MM, 0, 165 * MM), verts=block)
    bm.to_mesh(b.data)
    bm.free()
if VARIANT == "unapplied":  # same world geometry, but held in an object transform
    from mathutils import Matrix
    c.data.transform(Matrix.Translation((0, 0, -0.01)))
    c.location.z = 0.01
