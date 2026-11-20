"""The no-MCP baseline with each call's Blender in the sandbox container (setup "no-mcp-sandbox").

Same walls as harness-sandbox (rig/setups/sandbox.py): no network, read-only system, no host
environment, only the run folder writable, an audit log of attempts past them. As on the host, every
call is a fresh Blender on the saved scene; here every call is also a fresh container, so a call
costs the container start (about 1-2 s) on top. The model sees exactly what no-mcp shows it.
"""
import json
import subprocess
import uuid
from pathlib import Path

from ..blender import SetupError
from .no_mcp import NoMcpSetup
from .sandbox import IMAGE, docker_cmd, image_id


class NoMcpSandboxSetup(NoMcpSetup):
    name = "no-mcp-sandbox"

    def start(self, workdir: Path, scene: Path) -> None:
        if scene.resolve().parent != workdir.resolve():
            raise SetupError("the sandbox mounts only the run folder; the scene must be in it")
        self.versions = {"sandbox": f"{IMAGE} {image_id()[7:19]}"}
        self.audit = []
        self.root = workdir
        super().start(workdir, scene)

    def _exec(self, code: Path, result: Path) -> subprocess.CompletedProcess:
        rel = lambda p: "/work/" + p.resolve().relative_to(self.root.resolve()).as_posix()  # noqa: E731
        name = f"a3d-{uuid.uuid4().hex[:12]}"
        cmd = docker_cmd(name, self.root, self.scene.name, script="exec_code.py",
                         args=(rel(code), rel(result), "--sandbox"), interactive=False)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=self.timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True, timeout=60)
            raise
        except OSError as e:
            raise SetupError(f"docker failed to start: {e}") from e
        if result.is_file():
            self.audit.extend(json.loads(result.read_text(encoding="utf-8")).get("audit", []))
        elif "Unable to find image" in proc.stderr or "docker: " in proc.stderr[:200]:
            raise SetupError(f"sandbox container failed: {proc.stderr.strip()[-500:]}")
        return proc

    def stop(self) -> None:
        lines = "\n".join(self.audit)
        (self.root / "sandbox_audit.log").write_text(lines + ("\n" if lines else ""), encoding="utf-8")
