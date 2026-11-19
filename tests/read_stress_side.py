"""Blender side of tests/read_stress.py: opens each scene in turn and runs the opening read on it."""
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rig", "blender_side"))
import bpy  # noqa: E402
import harness_facts  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
scenes, out = json.loads(open(args[0], encoding="utf-8").read()), args[1]
rows = []
for path in scenes:
    try:
        bpy.ops.wm.open_mainfile(filepath=path)
        t0 = time.monotonic()
        text, _keys, _fp = harness_facts.report(True)
        rows.append({"scene": path, "seconds": time.monotonic() - t0, "text": text})
    except Exception:
        rows.append({"scene": path, "error": traceback.format_exc()})
with open(out, "w", encoding="utf-8") as f:
    json.dump(rows, f)
