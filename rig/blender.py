"""Launching headless Blender. Any failure to launch is a SetupError, which the runner records as void."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

DEFAULT_BLENDER = r"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"
SIDE = Path(__file__).parent / "blender_side"
LIB = Path(__file__).resolve().parent.parent / "tasks" / "_lib"


class SetupError(Exception):
    """A fault in the rig or environment, not in the agent's work. Recorded as void."""


def blender_path(override: str | None = None) -> Path:
    p = Path(override or os.environ.get("BLENDER_PATH") or DEFAULT_BLENDER)
    if not p.is_file():
        raise SetupError(f"Blender not found at {p}")
    return p


def run_script(exe: Path, script: str, args: list[str], blend: Path | None = None,
               timeout: float = 180) -> subprocess.CompletedProcess:
    cmd = [str(exe), "-b"]
    if blend is not None:
        cmd.append(str(blend))
    cmd += ["--factory-startup", "--disable-autoexec", "--python-exit-code", "1", "--python", str(SIDE / script), "--", *args]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except FileNotFoundError as e:
        raise SetupError(f"Blender failed to launch: {e}") from e


def blender_version(exe: Path) -> str:
    try:
        out = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise SetupError(f"Blender --version failed: {e}") from e
    first = out.stdout.strip().splitlines()[:1]
    if out.returncode != 0 or not first:
        raise SetupError(f"Blender --version returned {out.returncode}")
    return first[0]


def make_starting_scene(exe: Path, kind: str, out: Path, folder: Path | None = None) -> None:
    """'empty', or a task-local script (e.g. 'start.py') run on the empty scene to build the model a
    revision task starts from. The script gets tasks/_lib on sys.path, as reference models do."""
    proc = run_script(exe, "empty_scene.py", [str(out)])
    if proc.returncode != 0 or not out.is_file():
        raise SetupError(f"Starting scene build failed: {proc.stderr[-2000:]}")
    if kind == "empty":
        return
    src = (folder / kind) if folder is not None else None
    if src is None or not kind.endswith(".py") or not src.is_file():
        raise SetupError(f"Unknown starting scene {kind!r}")
    with tempfile.TemporaryDirectory() as tmp:
        code, result = Path(tmp) / "start.py", Path(tmp) / "result.json"
        code.write_text(f"import sys\nsys.path.insert(0, {str(LIB)!r})\n" + src.read_text(encoding="utf-8"),
                        encoding="utf-8")
        proc = run_script(exe, "exec_code.py", [str(code), str(result)], blend=out)
        ok = proc.returncode == 0 and result.is_file() and json.loads(result.read_text(encoding="utf-8"))["ok"]
        if not ok:
            detail = result.read_text(encoding="utf-8") if result.is_file() else proc.stderr[-2000:]
            raise SetupError(f"Starting scene {kind} failed: {detail[-2000:]}")


def run_checks(exe: Path, blend: Path, checks: list[dict]) -> dict:
    """Runs the task's checks on a scene. A crash of the check script itself is a SetupError."""
    with tempfile.TemporaryDirectory() as tmp:
        spec, result = Path(tmp) / "spec.json", Path(tmp) / "result.json"
        spec.write_text(json.dumps(checks), encoding="utf-8")
        proc = run_script(exe, "checks.py", [str(spec), str(result)], blend=blend, timeout=600)
        if proc.returncode != 0 or not result.is_file():
            raise SetupError(f"Check script failed (exit {proc.returncode}): {proc.stdout[-1500:]}{proc.stderr[-1500:]}")
        return json.loads(result.read_text(encoding="utf-8"))
