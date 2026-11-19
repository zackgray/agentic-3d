"""Runs one block of agent-written Python inside headless Blender, then saves the scene.

    blender -b scene.blend --factory-startup --python exec_code.py -- code.py result.json

On an exception the scene is NOT saved, so every call is one atomic step.
Writes {"ok": bool, "output": "<stdout + stderr, including any traceback>"}.
"""
import contextlib
import io
import json
import sys
import traceback

import bpy

code_path, result_path = sys.argv[sys.argv.index("--") + 1:][:2]
with open(code_path, encoding="utf-8") as f:
    source = f.read()

buf = io.StringIO()
ok = True
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    try:
        exec(compile(source, "<agent>", "exec"), {"__name__": "__main__", "bpy": bpy})
    except BaseException:  # SystemExit included: the agent's code must not kill the step silently
        ok = False
        traceback.print_exc()

if ok:
    bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)

with open(result_path, "w", encoding="utf-8") as f:
    json.dump({"ok": ok, "output": buf.getvalue()}, f)
