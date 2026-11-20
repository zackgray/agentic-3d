"""Free checks of the h6, h7 and h9 behaviours against a live harness Blender (no model calls). Run from the repo root:

    python tests/harness_selftest.py [--sandbox]   # --sandbox: the same checks in the container
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, ".")
from rig.blender import blender_path, make_starting_scene  # noqa: E402
from rig.setups.harness import HarnessSetup  # noqa: E402
from rig.setups.sandbox import SandboxHarnessSetup  # noqa: E402

exe = blender_path()
work = Path("runs/_smoke/h6check")
shutil.rmtree(work, ignore_errors=True)
work.mkdir(parents=True)
scene = work / "scene.blend"
make_starting_scene(exe, "empty", scene)
h = (SandboxHarnessSetup if "--sandbox" in sys.argv else HarnessSetup)(exe, timeout=8)
h.start(work, scene)
h.initial_context()
fails = []


def call(code, done=False):
    o = h.call("blender", {"code": code, "done": done})
    return o


def expect(name, cond, o=None):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)
        if o is not None:
            print(o.text[-800:])


VOL = """
import bmesh
def vol(n):
    o = bpy.data.objects[n]; bm = bmesh.new(); bm.from_mesh(o.data); v = bm.calc_volume(signed=True); bm.free(); return v
"""

# 1. Cavity built as an inner shell survives boolean() and finish().
o = call(VOL + """
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.1)
inner = bmesh.ops.create_cube(bm, size=0.05)
bmesh.ops.reverse_faces(bm, faces=list({f for v in inner['verts'] for f in v.link_faces}))
o = new_object('Shell', bm)
box('Cut', (0.04, -0.01, -0.01), (0.06, 0.01, 0.01))
boolean('Shell', 'Cut')
finish('Shell')
print('VOL', vol('Shell'))
""")
v = float(o.text.split("VOL ")[1].split()[0])
want = 0.1 ** 3 - 0.05 ** 3 - 0.01 * 0.02 * 0.02
expect(f"cavity kept (volume {v:.3e}, want {want:.3e})", abs(v - want) < 1e-8, o)

# 2. A mirrored (inside-out) cutter still cuts.
o = call(VOL + """
remove('Shell')
cylinder('Post', 0.01, 0, 0.2)
c = cylinder('Hole', 0.003, -0.05, 0.05)
for v in c.data.vertices:
    v.co.x, v.co.z = v.co.z, v.co.x + 0.1   # swap x and z: a mirror, inside out
boolean('Post', 'Hole')
print('VOL', vol('Post'))
""")
v = float(o.text.split("VOL ")[1].split()[0])
solid = 3.14159 * 0.01 ** 2 * 0.2
expect(f"mirrored cutter cuts ({v:.4e} < {solid:.4e})", v < solid * 0.995 and "warning" not in o.text, o)

# 3. Small hole in a big part: no warning.
o = call("""
remove('Post')
box('Slab', (-1, -1, 0), (1, 1, 0.1))
cylinder('Pin', 0.0005, -0.01, 0.11, segments=16, center=(0.3, 0.3))
boolean('Slab', 'Pin')
finish('Slab')
""", done=True)
expect("small hole in big part: no warning, finishes", "warning" not in o.text and o.final, o)
h.final = False

# 4. A boolean that misses warns, and blocks done=true once.
h.calls = 0
o = call("""
box('Far', (5, 5, 5), (5.1, 5.1, 5.1))
boolean('Slab', 'Far')
""", done=True)
expect("missed boolean warns and holds the run", "warning" in o.text and not o.final and "helper warned" in o.text, o)
o = call("pass", done=True)
expect("done=true again finishes", o.final, o)

# h9. A part tens of metres across holds a done=true call once per run; never a call without done.
h.calls = 0
o = call("remove('Slab')\nbox('Huge', (0, 0, 0), (30, 20, 10))")
expect("scale: no warning without done", "very large" not in o.text and not o.final, o)
o = call("pass", done=True)
expect("scale: done=true held once with a warning", "very large parts: Huge (30 m)" in o.text and not o.final, o)
o = call("pass", done=True)
expect("scale: done=true again finishes", o.final, o)
o = call("box('Huge2', (40, 0, 0), (90, 5, 5))", done=True)
expect("scale: holds only once per run", "very large" not in o.text and o.final, o)
call("remove('Huge', 'Huge2')\nbox('Slab', (-1, -1, 0), (1, 1, 0.1))")

# 5. Streak: raised and inspection-only calls don't count; progress resets it.
h.calls, h.streak, h.prev = 0, 0, None
BAD = """
remove('Slab')
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=0.1)
bmesh.ops.delete(bm, geom=bm.faces[:{n}], context='FACES')
new_object('Open', bm)
"""
call(BAD.format(n=1))
s1 = h.streak
call("print(len(bpy.data.objects))")                 # inspection only
call("raise ValueError('x')")                         # raised
expect(f"inspection and raised calls don't advance (streak {s1} -> {h.streak})", h.streak == s1 == 1)
call(BAD.format(n=3))                                 # more open edges: no improvement
call(BAD.format(n=2))                                 # fewer: progress
expect(f"progress resets the streak (streak {h.streak})", h.streak == 1)
call(BAD.format(n=2) + "\nbpy.data.objects['Open'].data.vertices[0].co.z += 0.001")
call(BAD.format(n=2) + "\nbpy.data.objects['Open'].data.vertices[0].co.z += 0.002")
expect(f"three unchanged calls make a streak of 3 (streak {h.streak})", h.streak == 3)

# 6. Digit-suffixed names are separate problem keys.
o = call("""
remove('Open')
box('Leg1', (0, 0, 0), (0.1, 0.1, 0.1)).location.x = 0.5
box('Leg2', (0, 0, 0), (0.1, 0.1, 0.1)).location.x = 1.0
""")
expect(f"digit-suffixed names kept apart ({sorted(h.prev)})", len(h.prev) == 2, o)

# h7 1. Names carry over between clean calls; math, bmesh and Mesh.faces need no setup.
call("remove('Leg1', 'Leg2')\nkeep = 41\nob = box('Kept', (0, 0, 0), (0.1, 0.1, 0.1))")
o = call("print('H7', keep + 1, ob.name, len(ob.data.faces), round(math.pi, 2), bmesh.new().__class__.__name__)")
expect("names, math, bmesh and faces available", "H7 42 Kept 6 3.14 BMesh" in o.text, o)

# h7 2. A failed call drops its own names and every Blender reference; plain values survive.
o = call("lost = 1\nraise ValueError('x')")
o = call("print('H7B', keep, 'lost' in globals(), 'ob' in globals(), bpy.data.objects['Kept'].name)")
expect("failed call: plain names kept, its names and stale refs dropped",
       "H7B 41 False False Kept" in o.text, o)

# h7 3. Helpers come back even if the agent overwrote one.
call("box = 5")
o = call("print('H7C', box('B2', (0, 0, 0), (1, 1, 1)).name)")
expect("helpers restored every call", "H7C B2" in o.text, o)

# h7 4. The opening read gives a revolved part's outline and round holes.
o = call("""
remove(*[n.name for n in bpy.data.objects])
lathe('Cup', [(0, 0), (0.03, 0), (0.03, 0.05), (0.028, 0.05), (0.028, 0.002), (0, 0.002)])
p = box('Plate', (0.1, -0.02, 0), (0.18, 0.02, 0.005))
for x in (0.12, 0.16):
    boolean(p, cylinder('H', 0.004, -0.01, 0.01, center=(x, 0)))
""")
read = h._request({"op": "report"})["report"]
expect("read: cup outline", "revolved about Z through x 0 y 0; outline (r, z): (0, 0), (0.03, 0), (0.03, 0.05), "
       "(0.028, 0.05), (0.028, 0.002), (0, 0.002)" in read, o if "revolved" in read else None)
expect("read: two holes", "hole x2 r 0.004 at x,y (0.12, 0), (0.16, 0), z 0..0.005" in read)
if fails[-2:] and fails[-1].startswith("read"):
    print(read)

# 7. A timeout counts toward the cap and can end the run.
h.calls = 7
o = call("import time\ntime.sleep(20)")
expect("timeout on call 8 ends the run", o.final and "Timed out" in o.text and "Call limit" in o.text, o)

h.stop()
print("\n%d failed" % len(fails) if fails else "\nall passed")
