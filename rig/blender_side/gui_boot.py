"""Boot script for GUI Blender in the MCP baselines. Runs as:

    blender scene.blend --python gui_boot.py -- <server> <harness_port> [server_port]

Two jobs. First, start the server's Blender side the way its authors' own tooling does (the Lab
extension and the community add-on auto-start themselves; Meshwire is started as its test harness
starts it, with the "Allow Python" switch left at its default, off). Second, open the rig's private
control channel: a localhost socket taking one JSON line per request ({"cmd": "save", "path": ...}
or {"cmd": "quit"}), executed on Blender's main thread. The agent never sees this channel.
"""
import json
import os
import queue
import socket
import sys
import threading
import traceback

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
SERVER, HARNESS_PORT = args[0], int(args[1])
SERVER_PORT = int(args[2]) if len(args) > 2 else None
jobs: "queue.Queue[tuple[dict, queue.Queue]]" = queue.Queue()


def start_server():
    if SERVER == "ahujasid":
        import addon_utils
        addon_utils.enable("mcp_for_blender", default_set=True, persistent=True)
    elif SERVER.startswith("meshwire"):  # meshwire, meshwire-py
        sys.path.insert(0, os.environ["MESHWIRE_ADDON_DIR"])
        import blender_mcp_addon
        from blender_mcp_addon.socket_server import MCPSocketServer
        blender_mcp_addon.register()
        if os.environ.get("MESHWIRE_ALLOW_PYTHON") == "1":  # the user has switched on "Allow Python"
            blender_mcp_addon.security.set_python_allowed(True)
        server = MCPSocketServer(host="127.0.0.1", port=SERVER_PORT)
        server.start()
        blender_mcp_addon._server = server
    # blender-lab: the extension is enabled in its profile and auto-starts from its preferences.


def handle(req):
    if req["cmd"] == "save":
        bpy.ops.wm.save_as_mainfile(filepath=req["path"], copy=True)
        return {"ok": True}
    if req["cmd"] == "quit":
        bpy.app.timers.register(lambda: bpy.ops.wm.quit_blender() and None, first_interval=0.2)
        return {"ok": True}
    if req["cmd"] == "ping":
        return {"ok": True}
    return {"ok": False, "error": f"unknown cmd {req['cmd']!r}"}


def pump():
    while not jobs.empty():
        req, reply = jobs.get()
        try:
            reply.put(handle(req))
        except Exception:
            reply.put({"ok": False, "error": traceback.format_exc()})
    return 0.1


def serve(conn):
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(65536)
        if not chunk:
            break
        data += chunk
    if not data.strip():  # a bare connect, e.g. the rig probing that the port is open
        return
    reply: queue.Queue = queue.Queue()
    jobs.put((json.loads(data), reply))
    conn.sendall((json.dumps(reply.get()) + "\n").encode())


def listen():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", HARNESS_PORT))
    srv.listen(4)
    while True:
        conn, _ = srv.accept()
        with conn:
            try:
                serve(conn)
            except (OSError, ValueError):  # a probe that resets, or a malformed request: keep listening
                traceback.print_exc()

try:
    start_server()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    os._exit(3)
bpy.app.timers.register(pump, first_interval=0.1, persistent=True)
threading.Thread(target=listen, daemon=True).start()
print(f"gui_boot: {SERVER} started; harness on {HARNESS_PORT}", flush=True)
