"""The harness's Blender: one headless session that stays open for the whole run.

    blender -b scene.blend --factory-startup --python harness_server.py -- port_file

Listens on 127.0.0.1 (an ephemeral port, written to port_file) for one JSON request per line:
    {"op": "exec", "code": "..."}  -> {"ok", "output", "warnings", "report", "problems", "keys",
                                       "fingerprint"}
    {"op": "report"}               -> the same without ok, output and warnings (detailed: adds Z
                                      and radial levels)
problems is the count; keys is [[key, count], ...], one per problem; warnings counts the helper
warnings (e.g. a boolean that changed nothing) printed during the call.
    {"op": "quit"}
A call that raises changes nothing: the scene is saved after every clean call and reloaded after a
failed one, the same atomic-step rule as the no-MCP baseline.

Names the agent defines carry over between calls (h7: 29 NameErrors in 21 recorded revision runs
came from a fresh namespace per call). A failed call's own names are dropped with its scene
changes, and the reload invalidates every Blender reference, so those are dropped too: no stale
object survives a reload. bpy, math, bmesh and the helpers are put back before every call, and
Mesh.faces reads Mesh.polygons (27 more recorded errors).
"""
import contextlib
import io
import json
import math
import os
import socket
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh  # noqa: E402
import bpy  # noqa: E402

import harness_facts  # noqa: E402
import harness_lib  # noqa: E402


bpy.types.Mesh.faces = property(lambda self: self.polygons)
NS = {}


def run_code(source):
    global NS
    buf = io.StringIO()
    ok = True
    harness_lib.WARNINGS.clear()
    before = dict(NS)
    ns = NS
    ns.update({"__name__": "__main__", "bpy": bpy, "math": math, "bmesh": bmesh, **harness_lib.EXPORTS})
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            exec(compile(source, "<agent>", "exec"), ns)
        except BaseException:  # SystemExit included: the agent's code must not end the session
            ok = False
            traceback.print_exc()
    if ok:
        bpy.ops.wm.save_mainfile(filepath=bpy.data.filepath)
    else:
        bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
        NS = {k: v for k, v in before.items() if not isinstance(v, bpy.types.bpy_struct)}
    return ok, buf.getvalue()


def safe_report(detail):
    try:
        text, keys, fp = harness_facts.report(detail)
        return {"report": text, "problems": len(keys), "keys": keys, "fingerprint": fp}
    except Exception:  # a broken report is a rig fault; say so rather than hide it
        return {"report": "Scene report failed:\n" + traceback.format_exc(), "problems": -1,
                "keys": [], "fingerprint": None}


def handle(req):
    if req["op"] == "exec":
        ok, output = run_code(req["code"])
        warnings = len(harness_lib.WARNINGS) if ok else 0
        return {"ok": ok, "output": output, "warnings": warnings, **safe_report(False)}
    if req["op"] == "report":
        return safe_report(True)
    raise ValueError(f"unknown op {req['op']!r}")


def main():
    port_file = sys.argv[sys.argv.index("--") + 1]
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    with open(port_file + ".tmp", "w", encoding="utf-8") as f:
        f.write(str(srv.getsockname()[1]))
    os.replace(port_file + ".tmp", port_file)
    conn, _ = srv.accept()
    stream = conn.makefile("rw", encoding="utf-8", newline="\n")
    for line in stream:
        req = json.loads(line)
        if req["op"] == "quit":
            break
        try:
            resp = handle(req)
        except Exception:
            resp = {"rig_error": traceback.format_exc()}
        stream.write(json.dumps(resp) + "\n")
        stream.flush()
    conn.close()
    srv.close()


main()
