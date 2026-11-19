"""Baselines that reach Blender through an MCP server.

Per run: one GUI Blender opened on the run's starting scene with gui_boot.py, then the server's
own MCP process over stdio. The server's tool definitions and instructions go to the model
unchanged; tool results (text and images) come back unchanged. When the agent is done the rig
saves the scene over its private control channel and closes everything. Any failure to bring the
setup up is a SetupError (void).
"""
import asyncio
import json
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..blender import SIDE, SetupError
from .hidden_desktop import launch
from .pins import HARNESS_PORT

# Shared by every MCP baseline; only the server's own instructions differ.
BASE_SYSTEM = (
    "You are modeling in Blender 5.2 through the connected Blender tools. When the task is "
    "complete, reply with a short final message and no tool call."
)
CALL_TIMEOUT = 300


@dataclass
class Outcome:
    text: str
    is_error: bool
    seconds: float
    images: list = field(default_factory=list)  # [(media_type, base64 data)]


def wait_port(port: int, proc: subprocess.Popen, timeout: float, what: str) -> None:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if proc.poll() is not None:
            raise SetupError(f"{what}: Blender exited ({proc.returncode}) before port {port} opened")
        try:
            socket.create_connection(("127.0.0.1", port), 1).close()
            return
        except OSError:
            time.sleep(0.25)
    raise SetupError(f"{what}: port {port} not open after {timeout:.0f} s")


def harness(cmd: dict, timeout: float = 120) -> dict:
    with socket.create_connection(("127.0.0.1", HARNESS_PORT), timeout) as s:
        s.sendall((json.dumps(cmd) + "\n").encode())
        data = b""
        while not data.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
    return json.loads(data)


class McpSetup:
    """Subclasses set name, version, server_port, and implement blender_env / server_params."""
    name = version = ""
    server_port = 0
    blender_args: list[str] = []  # extra flags the server's own launch uses

    def __init__(self, exe: Path):
        self.exe = exe
        self.system, self.tools = BASE_SYSTEM, []
        self.instructions = ""

    # -- per-server configuration ------------------------------------------------------------
    def blender_env(self, workdir: Path) -> dict:
        raise NotImplementedError

    def server_params(self, workdir: Path) -> StdioServerParameters:
        raise NotImplementedError

    # -- lifecycle -----------------------------------------------------------------------------
    def start(self, workdir: Path, scene: Path) -> None:
        self.workdir, self.scene = workdir, scene
        self.log = log = open(workdir / "blender.log", "w", encoding="utf-8", errors="replace")
        cmd = [str(self.exe), *self.blender_args, str(scene), "--python", str(SIDE / "gui_boot.py"), "--",
               self.name, str(HARNESS_PORT), str(self.server_port)]
        self.blender = launch(cmd, self.blender_env(workdir), log)  # on a hidden desktop: see hidden_desktop.py
        self._closing = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        try:
            wait_port(HARNESS_PORT, self.blender, 120, self.name)
            wait_port(self.server_port, self.blender, 120, self.name)
            self._run(self._open(), 180)
        except BaseException as e:
            self.shutdown()
            raise e if isinstance(e, SetupError) else SetupError(f"{self.name}: MCP start failed: {e!r}")
        self.tools = [{"name": t.name, "description": t.description or "", "input_schema": t.inputSchema}
                      for t in self._tools]
        if self.instructions:
            self.system = BASE_SYSTEM + "\n\n" + self.instructions

    async def _open(self):
        """Hold the stdio client and session open in one task until stop() releases them."""
        opened = asyncio.get_running_loop().create_future()
        self._closing = asyncio.Event()

        async def hold():
            try:
                async with stdio_client(self.server_params(self.workdir)) as (r, w):
                    async with ClientSession(r, w) as session:
                        init = await session.initialize()
                        self.instructions = init.instructions or ""
                        self._tools = (await session.list_tools()).tools
                        self.session = session
                        opened.set_result(True)
                        await self._closing.wait()
            except BaseException as e:
                if not opened.done():
                    opened.set_exception(e)

        self._holder = asyncio.ensure_future(hold())
        await opened

    def _run(self, coro, timeout):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    def call(self, name: str, tool_input: dict) -> Outcome:
        t0 = time.monotonic()
        if self.blender.poll() is not None:
            return Outcome(f"Blender is not running (exited {self.blender.returncode}).", True, 0.0)
        try:
            res = self._run(self.session.call_tool(name, tool_input), CALL_TIMEOUT)
        except TimeoutError:
            return Outcome(f"Tool call timed out after {CALL_TIMEOUT} s.", True, time.monotonic() - t0)
        except Exception as e:  # a protocol-level error is returned to the agent as the client would
            return Outcome(f"Error calling tool {name}: {e}", True, time.monotonic() - t0)
        texts, images = [], []
        for c in res.content:
            if c.type == "text":
                texts.append(c.text)
            elif c.type == "image":
                images.append((c.mimeType, c.data))
            else:
                texts.append(json.dumps(c.model_dump(mode="json")))
        return Outcome("\n".join(texts), bool(res.isError), time.monotonic() - t0, images)

    def stop(self) -> None:
        """Save the final scene for the checks, then close the server and Blender."""
        try:
            if self.blender.poll() is not None:
                raise SetupError(f"{self.name}: Blender exited during the run ({self.blender.returncode})")
            out = harness({"cmd": "save", "path": str(self.scene)})
            if not out.get("ok"):
                raise SetupError(f"{self.name}: saving the final scene failed: {out.get('error')}")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Close the MCP session and Blender; safe to call on a half-started setup."""
        if self._closing is not None:
            self.loop.call_soon_threadsafe(self._closing.set)
            try:
                self._run(asyncio.wait_for(asyncio.shield(self._holder), 30), 40)
            except Exception:
                pass
        if self.blender.poll() is None:
            try:
                harness({"cmd": "quit"}, timeout=10)
                self.blender.wait(30)
            except Exception:
                self.blender.kill()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.log.close()


def base_env(**extra) -> dict:
    env = dict(os.environ)
    env.update({k: str(v) for k, v in extra.items()})
    return env
