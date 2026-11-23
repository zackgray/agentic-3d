"""Serve the judging page on 127.0.0.1 only. POST <page>/__grades__ writes a grades file beside the page
and never overwrites an earlier one."""
import json
import re
import socket
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import FORMAT

HOST = "127.0.0.1"
DEFAULT_PORT = 8741
MAX_GRADES_BYTES = 5_000_000


def save_grades(folder: Path, body: bytes, stamp: str | None = None) -> str:
    """Write one grades export into ``folder``; returns the file name. Opened with mode 'x': never overwrites."""
    if len(body) > MAX_GRADES_BYTES:
        raise ValueError("grades file too large")
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict) or data.get("format") != FORMAT or not isinstance(data.get("grades"), dict):
        raise ValueError("not a grades file from this judging page")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", str(data.get("buildId", "page")))[:40] or "page"
    stem = "grades-%s-%s" % (safe, stamp or time.strftime("%Y%m%d-%H%M%S"))
    for n in range(1000):
        name = stem + ("" if n == 0 else "-%d" % n) + ".json"
        try:
            with open(Path(folder) / name, "x", encoding="utf-8", newline="\n") as out:
                out.write(json.dumps(data, indent=1) + "\n")
            return name
        except FileExistsError:
            continue
    raise ValueError("could not find a free file name")


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        path = self.path.split("?")[0]
        folder = Path(self.translate_path(path.rsplit("/", 1)[0] + "/"))
        try:
            if not path.endswith("/__grades__") or not folder.is_dir():
                raise ValueError("no such endpoint")
            length = min(int(self.headers.get("Content-Length", 0)), MAX_GRADES_BYTES + 1)
            reply, code = {"saved": save_grades(folder, self.rfile.read(length))}, 200
        except (ValueError, UnicodeDecodeError) as err:
            reply, code = {"error": str(err)}, 400
        body = json.dumps(reply).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # a rebuilt page must never show stale images
        super().end_headers()


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, port))
            return True
        except OSError:
            return False


def pick_port(start: int = DEFAULT_PORT, tries: int = 50) -> int:
    for port in range(start, start + tries):
        if port_free(port):
            return port
    raise SystemExit("no free port in %d-%d" % (start, start + tries - 1))


def serve(folder: Path, port: int | None = None) -> None:
    folder = Path(folder)
    if not (folder / "index.html").is_file():
        raise SystemExit("no page at %s: run build first" % folder)
    if port is None:
        port = pick_port()
    elif not port_free(port):
        raise SystemExit("port %d is taken (an old judging server?); pick another or omit --port" % port)
    server = ThreadingHTTPServer((HOST, port), partial(Handler, directory=str(folder)))
    print("Judging page: http://%s:%d/  (Ctrl+C to stop)" % (HOST, port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
