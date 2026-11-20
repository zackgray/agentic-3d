"""Runs one block of agent-written Python inside headless Blender, then saves the scene.

    blender -b scene.blend --factory-startup --python exec_code.py -- code.py result.json

On an exception the scene is NOT saved, so every call is one atomic step.
With a third argument --sandbox (no-mcp-sandbox, in the container): the agent's attempts past the
sandbox are logged (harness_audit) and scripts registered to run when a scene opens are stripped.
Writes {"ok": bool, "output": "<stdout + stderr, including any traceback>"}.
"""
import contextlib
import io
import json
import sys
import os
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness_audit  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
code_path, result_path = args[:2]
SANDBOX = "--sandbox" in args[2:]
if SANDBOX:
    harness_audit.install()
with open(code_path, encoding="utf-8") as f:
    source = f.read()

buf = io.StringIO()
ok = True
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    harness_audit.active = SANDBOX
    try:
        exec(compile(source, "<agent>", "exec"), {"__name__": "__main__", "bpy": bpy})
    except BaseException:  # SystemExit included: the agent's code must not kill the step silently
        ok = False
        traceback.print_exc()
    finally:
        harness_audit.active = False

if ok:
    if SANDBOX:
        for t in [t for t in bpy.data.texts if t.use_module]:
            bpy.data.texts.remove(t)
    bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)

with open(result_path, "w", encoding="utf-8") as f:
    json.dump({"ok": ok, "output": buf.getvalue(), "audit": harness_audit.take()}, f)
