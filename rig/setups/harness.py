"""Phase 3 harness v1. One tool on a Blender session that stays open for the whole run.

Designed from the Phase 2 no-MCP breakdown (docs/journal.md, 2026-11-17):
- the scene report after every call replaces the inspection code agents write and print;
- the scene is read once up front, so a revision doesn't spend a turn reading the model;
- done=true ends the run on a clean call, saving the closing turn that resends the whole context
  (about 36% of no-MCP tokens; owner's go 2026-11-17);
- generic helpers cut the code written per task;
- a persistent Blender saves the ~1.7 s launch per call.
"""
import json
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ..blender import SIDE, SetupError
from .harness_prompt import INTRO, SYSTEM, TOOLS

NAME = "harness"
VERSION = "h9"  # h8 (expected extents, lathe warning) not adopted; h9 adds a one-time scale warning on done; h6 read no circles or paired profiles and reset names every call; h5's loop handling miscounted (review fixes); h4 looped on problems it could not locate or fix; h3 had no mm constant (1,000x builds); h2 reported millimetres (agents built 1,000x); h1 stale matrix_world; bump when the system prompt, tools, helpers, report or executor change
OUTPUT_CAP = 10_000
PERSIST = 3    # same problems this many calls in a row: done=true may finish anyway (owner, 2026-11-17)
CALL_CAP = 8   # backstop: the run ends after this many calls and the scene is checked as it stands
BOOT_TIMEOUT = 60


@dataclass
class Outcome:
    text: str
    is_error: bool
    seconds: float
    final: bool = False


class HarnessSetup:
    name, version, system, tools = NAME, VERSION, SYSTEM, TOOLS

    def __init__(self, exe: Path, timeout: float = 180):
        self.exe, self.timeout = exe, timeout
        self.proc = self.stream = self.sock = None

    def start(self, workdir: Path, scene: Path) -> None:
        self.dir, self.scene = workdir, scene
        self.calls, self.streak, self.prev, self.fp = 0, 0, None, None
        self._boot()

    def _boot(self) -> None:
        port_file = self.dir / "harness_port.txt"
        port_file.unlink(missing_ok=True)
        if getattr(self, "log", None):
            self.log.close()
        self.log = open(self.dir / "harness_blender.log", "a", encoding="utf-8")
        self.proc = subprocess.Popen(
            [str(self.exe), "-b", str(self.scene), "--factory-startup", "--python-exit-code", "1",
             "--python", str(SIDE / "harness_server.py"), "--", str(port_file)],
            stdout=self.log, stderr=subprocess.STDOUT)
        t0 = time.monotonic()
        try:
            while True:
                try:  # Blender may be replacing the file right now (PermissionError on Windows)
                    port = int(port_file.read_text(encoding="utf-8"))
                    break
                except (OSError, ValueError):
                    pass
                if self.proc.poll() is not None or time.monotonic() - t0 > BOOT_TIMEOUT:
                    raise SetupError(f"harness Blender failed to start (see {self.dir / 'harness_blender.log'})")
                time.sleep(0.05)
            self.sock = socket.create_connection(("127.0.0.1", port))
            self.sock.settimeout(self.timeout)
            self.stream = self.sock.makefile("rw", encoding="utf-8", newline="\n")
        except BaseException:
            self._kill()  # never leave a Blender running behind a failed boot
            raise

    def _request(self, req: dict) -> dict:
        self.stream.write(json.dumps(req) + "\n")
        self.stream.flush()
        line = self.stream.readline()
        if not line:
            raise ConnectionError("harness Blender closed the connection")
        resp = json.loads(line)
        if "rig_error" in resp:
            raise SetupError(f"harness server error: {resp['rig_error'][-1500:]}")
        return resp

    def initial_context(self) -> str:
        resp = self._request({"op": "report"})
        self.fp = resp["fingerprint"]
        return INTRO + resp["report"]

    def call(self, name: str, tool_input: dict) -> Outcome:
        t0 = time.monotonic()
        if name != "blender" or not isinstance(tool_input.get("code"), str):
            return Outcome(f"Unknown tool or bad input: {name}", True, 0.0)
        self.calls += 1  # crashes and timeouts count toward the cap too (h5 didn't count them)
        capped = self.calls >= CALL_CAP
        limit = f"\nCall limit ({CALL_CAP}) reached; the task ends here."
        try:
            resp = self._request({"op": "exec", "code": tool_input["code"],
                                  "done": bool(tool_input.get("done"))})
        except (socket.timeout, TimeoutError, ConnectionError, OSError) as e:
            # The agent's code hung or took Blender down. The scene on disk is the last clean step.
            self._kill()
            self._boot()
            what = "Timed out" if isinstance(e, (socket.timeout, TimeoutError)) else "Blender crashed"
            return Outcome(f"{what}; scene unchanged." + (limit if capped else ""), True,
                           time.monotonic() - t0, capped)
        out = resp["output"]
        if len(out) > OUTPUT_CAP:
            out = out[:OUTPUT_CAP] + f"\n[output truncated: {len(out)} characters total]"
        self._track(resp)
        ok, problems, warned = resp["ok"], resp["problems"], resp.get("warnings", 0) > 0
        done, stuck = bool(tool_input.get("done")), self.streak >= PERSIST
        final = done and ok and not warned and (problems == 0 or stuck)
        if final and problems == 0:
            tail = "Done: no problems found."
        elif final:
            tail = resp["report"] + "\nFinished with these problems unchanged over the last calls."
        elif capped:
            final, tail = True, resp["report"] + limit
        else:
            tail = resp["report"]
            if done:
                tail += "\nNot finished: " + (
                    "the call raised." if not ok else
                    "fix the problems above." if problems and not stuck else
                    "a helper warned (see above). Fix it, or if the result is what you intended, "
                    "call again with done=true.")
            if stuck:
                tail += (f"\nThese problems haven't improved over the last {self.streak} calls that "
                         "changed the scene. If you can't fix them, call again with done=true to "
                         "finish as is.")
        text = (out.rstrip() + "\n\n" if out.strip() else "") + tail
        return Outcome(text, not ok, time.monotonic() - t0, final)

    def _track(self, resp: dict) -> None:
        """Count consecutive calls whose problems didn't improve. Only calls that ran clean and
        changed the scene count: h5 also counted calls that raised (the scene reverts, so the
        problems repeat) and inspection-only calls. Improving means some count fell, so 270 -> 40 ->
        6 open edges is progress, while 160 -> 264 intersecting face pairs is not."""
        if not resp["ok"] or (resp["fingerprint"] is not None and resp["fingerprint"] == self.fp):
            return
        self.fp = resp["fingerprint"]
        keys = dict((k, n) for k, n in resp["keys"])
        same = bool(keys) and self.prev is not None and keys.keys() == self.prev.keys()
        if same and all(keys[k] >= self.prev[k] for k in keys):
            self.streak += 1
        else:
            self.streak = 1 if keys else 0
        self.prev = keys

    def _kill(self) -> None:
        for h in (self.stream, self.sock):
            try:
                h and h.close()
            except OSError:
                pass
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=30)
        self.stream = self.sock = None

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None and self.stream:
            try:
                self._request_quit()
                self.proc.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired):
                pass
        self._kill()
        if getattr(self, "log", None):
            self.log.close()

    def _request_quit(self) -> None:
        self.stream.write(json.dumps({"op": "quit"}) + "\n")
        self.stream.flush()
