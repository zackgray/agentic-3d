"""Baseline: no MCP. One tool that runs agent-written Python in headless Blender against the saved scene.

This is the shape of "the agent writes scripts and runs Blender in the background": no scene
summaries, no screenshots, nothing but what the agent prints.
"""
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ..blender import run_script

NAME = "no-mcp"
VERSION = "rig-1"  # bump when the system prompt, tool definition or executor changes
OUTPUT_CAP = 10_000  # characters of printed output returned per call

SYSTEM = (
    "You are modeling in Blender 5.2. The run_blender_python tool runs Python (bpy) in a headless "
    "Blender session holding the current scene. The scene is saved after every call that finishes "
    "without an exception; a call that raises changes nothing. There is no viewport and no image "
    "output: print() whatever you need to inspect. When the task is complete, reply with a short "
    "final message and no tool call."
)

TOOLS = [{
    "name": "run_blender_python",
    "description": (
        "Run a Python script inside Blender 5.2 (bpy is available) on the current scene. Returns "
        "everything the script printed, plus the traceback if it raised. The scene is saved only "
        "if the script finishes without an exception."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"code": {"type": "string", "description": "Python source to execute."}},
        "required": ["code"],
        "additionalProperties": False,
    },
    "strict": True,
}]


@dataclass
class Outcome:
    text: str
    is_error: bool
    seconds: float


class NoMcpSetup:
    name, version, system, tools = NAME, VERSION, SYSTEM, TOOLS

    def __init__(self, exe: Path, timeout: float = 180):
        self.exe, self.timeout = exe, timeout
        self.calls = 0

    def start(self, workdir: Path, scene: Path) -> None:
        self.dir = workdir / "calls"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.scene = scene

    def call(self, name: str, tool_input: dict) -> Outcome:
        t0 = time.monotonic()
        if name != "run_blender_python" or not isinstance(tool_input.get("code"), str):
            return Outcome(f"Unknown tool or bad input: {name}", True, 0.0)
        self.calls += 1
        code = self.dir / f"{self.calls:03d}.py"
        result = self.dir / f"{self.calls:03d}.json"
        code.write_text(tool_input["code"], encoding="utf-8")
        try:
            proc = self._exec(code, result)
        except subprocess.TimeoutExpired:
            return Outcome(f"Timed out after {self.timeout:.0f} s; scene unchanged.", True,
                           time.monotonic() - t0)
        if not result.is_file():  # the agent's code took Blender down with it
            tail = (proc.stdout + proc.stderr)[-2000:]
            return Outcome(f"Blender exited with code {proc.returncode}; scene unchanged.\n{tail}",
                           True, time.monotonic() - t0)
        out = json.loads(result.read_text(encoding="utf-8"))
        text = out["output"] or ("(no output; scene saved)" if out["ok"] else "(failed, no output)")
        if len(text) > OUTPUT_CAP:
            text = text[:OUTPUT_CAP] + f"\n[output truncated: {len(text)} characters total]"
        return Outcome(text, not out["ok"], time.monotonic() - t0)

    def _exec(self, code: Path, result: Path) -> subprocess.CompletedProcess:
        return run_script(self.exe, "exec_code.py", [str(code), str(result)], blend=self.scene,
                          timeout=self.timeout)

    def stop(self) -> None:
        pass
