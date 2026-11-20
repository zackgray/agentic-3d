"""The h7 harness with its Blender in a container (setup name "harness-sandbox").

Agent-written code otherwise runs in a Blender that is the owner's Windows user: every file, the
network, other programs. Here it runs in a Linux container (sandbox/Dockerfile) with
- no network at all (--network none): the rig talks to Blender over the container's stdin and
  stdout, and the model is called from the rig, outside;
- a read-only root, no Linux capabilities, no privilege escalation, capped processes and memory;
- one writable folder, the run's own, mounted at /work; the harness code is mounted read-only;
- nothing from the host environment (the API key stays outside).
Each run gets a fresh container, removed when it stops. Inside, an audit hook logs what the agent's
code tries past those walls (harness_audit); the log is kept with the run.

The model sees exactly what h7 shows it; only where Blender runs changes. Checks still run in the
host's Blender on the saved scene, as for every other setup.
"""
import json
import queue
import subprocess
import threading
import uuid

from ..blender import SIDE, SetupError
from .harness import BOOT_TIMEOUT, HarnessSetup

IMAGE = "agentic3d-blender:5.2.3"
MARK = "\x1eA3D\x1e"  # harness_server.MARK
_image_id = None


def image_id() -> str:
    """The image's id, checked once per process. A missing image or Docker is a setup fault."""
    global _image_id
    if _image_id is None:
        try:
            out = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", IMAGE],
                                 capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise SetupError(f"Docker unavailable: {e}") from e
        if out.returncode != 0:
            raise SetupError(f"sandbox image {IMAGE} missing (docker build -t {IMAGE} sandbox): "
                             f"{out.stderr.strip()[-300:]}")
        _image_id = out.stdout.strip()
    return _image_id


def docker_cmd(name: str, workdir, scene_name: str, script: str = "harness_server.py",
               args: tuple = ("--stdio",), interactive: bool = True) -> list[str]:
    return [
        "docker", "run", "--rm", *(["-i"] if interactive else []), "--name", name,
        "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,size=1g",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "512", "--memory", "8g", "--user", "1000:1000", "-e", "HOME=/tmp",
        "-v", f"{workdir.resolve()}:/work", "-v", f"{SIDE.resolve()}:/side:ro",
        IMAGE, "-b", f"/work/{scene_name}", "--factory-startup", "--disable-autoexec",
        "--python-exit-code", "1", "--python", f"/side/{script}", "--", *args,
    ]


class SandboxHarnessSetup(HarnessSetup):
    name = "harness-sandbox"

    def start(self, workdir, scene) -> None:
        if scene.resolve().parent != workdir.resolve():
            raise SetupError("the sandbox mounts only the run folder; the scene must be in it")
        self.versions = {"sandbox": f"{IMAGE} {image_id()[7:19]}"}
        self.audit = []
        super().start(workdir, scene)

    def _boot(self) -> None:
        if getattr(self, "log", None):
            self.log.close()
        self.log = open(self.dir / "harness_blender.log", "a", encoding="utf-8")
        self.cname = f"a3d-{uuid.uuid4().hex[:12]}"
        self.lines = queue.Queue()
        self.first = True
        try:
            self.proc = subprocess.Popen(docker_cmd(self.cname, self.dir, self.scene.name),
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=self.log)
        except OSError as e:
            raise SetupError(f"docker failed to start: {e}") from e
        self.stream = self.proc.stdin
        threading.Thread(target=self._read, args=(self.proc.stdout, self.lines, self.log),
                         daemon=True).start()

    @staticmethod
    def _read(out, lines, log) -> None:
        """Responses to the queue; Blender's own output to the log. None marks the end."""
        for raw in out:
            text = raw.decode("utf-8", "replace")
            i = text.find(MARK)
            if i < 0:
                try:
                    log.write(text)
                except ValueError:  # log closed by stop()
                    pass
                continue
            lines.put(text[i + len(MARK):])
        lines.put(None)

    def _request(self, req: dict) -> dict:
        wait = self.timeout + (BOOT_TIMEOUT if self.first else 0)  # first reply waits for the boot
        self.first = False
        try:
            self.stream.write((json.dumps(req) + "\n").encode("utf-8"))
            self.stream.flush()
        except OSError as e:
            raise ConnectionError(f"sandbox closed: {e}") from e
        try:
            line = self.lines.get(timeout=wait)
        except queue.Empty:
            raise TimeoutError("sandbox call timed out") from None
        if line is None:
            raise ConnectionError("sandbox Blender closed the connection")
        resp = json.loads(line)
        if "rig_error" in resp:
            raise SetupError(f"harness server error: {resp['rig_error'][-1500:]}")
        self.audit.extend(resp.get("audit", []))
        return resp

    def initial_context(self) -> str:
        try:
            return super().initial_context()
        except (TimeoutError, ConnectionError) as e:  # no first report: the sandbox never came up
            self._kill()
            raise SetupError(f"sandbox failed to start ({e}); see {self.dir / 'harness_blender.log'}") from e

    def _request_quit(self) -> None:
        self.stream.write(b'{"op": "quit"}\n')
        self.stream.flush()

    def _kill(self) -> None:
        if getattr(self, "cname", None):
            subprocess.run(["docker", "kill", self.cname], capture_output=True, timeout=60)
        for h in (self.stream, getattr(self.proc, "stdout", None)):
            try:
                h and h.close()
            except OSError:
                pass
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=30)
        self.stream = None

    def stop(self) -> None:
        super().stop()
        lines = "\n".join(self.audit)
        (self.dir / "sandbox_audit.log").write_text(lines + ("\n" if lines else ""), encoding="utf-8")
