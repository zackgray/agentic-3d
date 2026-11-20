"""The harness's Blender: one headless session that stays open for the whole run.

    blender -b scene.blend --factory-startup --python harness_server.py -- port_file

Listens on 127.0.0.1 (an ephemeral port, written to port_file) for one JSON request per line:
    {"op": "exec", "code": "...", "done": bool}  -> {"ok", "output", "warnings", "report", "problems", "keys",
                                       "fingerprint"}
    {"op": "report"}               -> the same without ok, output and warnings (detailed: adds Z
                                      and radial levels)
problems is the count; keys is [[key, count], ...], one per problem; warnings counts the helper
warnings (e.g. a boolean that changed nothing) printed during the call; on a done call, also the
one-time scale warning (h9).
    {"op": "quit"}
With --stdio instead of a port file (the harness-sandbox setup: no network in the container), requests
come on stdin and each response is one stdout line after MARK, so Blender's own output on the same
stream can't be mistaken for one. That mode also logs the agent's attempts to reach past the sandbox
(harness_audit) and strips scripts registered to run when a scene is opened before every save.
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

import harness_audit  # noqa: E402
import harness_facts  # noqa: E402
import harness_lib  # noqa: E402

MARK = "\x1eA3D\x1e"
STDIO = "--stdio" in sys.argv


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
        harness_audit.active = STDIO
        try:
            exec(compile(source, "<agent>", "exec"), ns)
        except BaseException:  # SystemExit included: the agent's code must not end the session
            ok = False
            traceback.print_exc()
        finally:
            harness_audit.active = False
    if ok:
        if STDIO:  # the owner opens these scenes in a Blender outside the sandbox
            for t in [t for t in bpy.data.texts if t.use_module]:
                bpy.data.texts.remove(t)
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
        if ok and req.get("done"):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                harness_lib.scale_check()
            output += buf.getvalue()
        warnings = len(harness_lib.WARNINGS) if ok else 0
        return {"ok": ok, "output": output, "warnings": warnings, "audit": harness_audit.take(),
                **safe_report(False)}
    if req["op"] == "report":
        return safe_report(True)
    raise ValueError(f"unknown op {req['op']!r}")


def serve(lines, send):
    for line in lines:
        req = json.loads(line)
        if req["op"] == "quit":
            break
        try:
            resp = handle(req)
        except Exception:
            resp = {"rig_error": traceback.format_exc()}
        send(json.dumps(resp))


def send_stdio(text):
    sys.stdout.flush()  # any partial line of Blender's goes first; the rig finds MARK mid-line too
    os.write(sys.stdout.fileno(), (MARK + text + "\n").encode("utf-8"))


def main():
    if STDIO:
        harness_audit.install()
        serve(sys.stdin, send_stdio)
        return
    port_file = sys.argv[sys.argv.index("--") + 1]
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    with open(port_file + ".tmp", "w", encoding="utf-8") as f:
        f.write(str(srv.getsockname()[1]))
    os.replace(port_file + ".tmp", port_file)
    conn, _ = srv.accept()
    stream = conn.makefile("rw", encoding="utf-8", newline="\n")

    def send(text):
        stream.write(text + "\n")
        stream.flush()

    serve(stream, send)
    conn.close()
    srv.close()


main()
