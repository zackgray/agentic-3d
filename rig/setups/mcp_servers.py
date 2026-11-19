"""The three MCP baselines, each run the way its authors' own tooling runs it (see docs/research.md).

Bump a VERSION when anything about how the rig runs that server changes; the server's own version
is its pin in pins.py.
"""
import shutil
from pathlib import Path

from mcp import StdioServerParameters

from .mcp_base import McpSetup, base_env
from .pins import PINS, profile, src

UV = shutil.which("uv") or "uv"


class BlenderLabSetup(McpSetup):
    """Blender's official Lab MCP server: extension auto-starts in GUI Blender."""
    name, version, server_port = "blender-lab", "rig-1", PINS["blender-lab"]["port"]
    blender_args = ["--online-mode"]  # the extension refuses to start without network access allowed

    def blender_env(self, workdir: Path) -> dict:
        return base_env(BLENDER_USER_RESOURCES=profile(self.name))

    def server_params(self, workdir: Path) -> StdioServerParameters:
        return StdioServerParameters(
            command=UV, args=["run", "--frozen", "--directory", str(src(self.name) / "mcp"), "blender-mcp"],
            env=base_env(BLENDER_MCP_PORT=self.server_port, BLENDER_PATH=self.exe))


class AhujasidSetup(McpSetup):
    """ahujasid/mcp-for-blender: add-on auto-starts in GUI Blender. Telemetry and the update check
    are off (owner's decision 2026-11-16; neither changes what the model sees)."""
    name, version, server_port = "ahujasid", "rig-1", PINS["ahujasid"]["port"]
    quiet = {"DISABLE_TELEMETRY": "true", "BLENDERMCP_NO_UPDATE_CHECK": "1"}

    def blender_env(self, workdir: Path) -> dict:
        return base_env(BLENDER_USER_RESOURCES=profile(self.name), **self.quiet)

    def server_params(self, workdir: Path) -> StdioServerParameters:
        return StdioServerParameters(
            command=UV, args=["run", "--frozen", "--directory", str(src(self.name)), "mcp-for-blender"],
            env=base_env(BLENDER_HOST="localhost", BLENDER_PORT=self.server_port,
                         BLENDERMCP_ADDONS_DIR=profile(self.name) / "scripts" / "addons", **self.quiet))


class MeshwireSetup(McpSetup):
    """Meshwire (RFingAdam, ~225 typed tools). "Allow Python" stays at its default, off (owner's
    decision 2026-11-16), so the agent works through the typed tools."""
    name, version, server_port = "meshwire", "rig-1", PINS["meshwire"]["port"]
    allow_python = False

    def config_dir(self, workdir: Path) -> Path:
        d = workdir / "meshwire-config"  # the server writes its auth token here, per run
        d.mkdir(exist_ok=True)
        return d

    def blender_env(self, workdir: Path) -> dict:
        return base_env(BLENDER_USER_RESOURCES=profile("meshwire"), MESHWIRE_CONFIG_DIR=self.config_dir(workdir),
                        MESHWIRE_ADDON_DIR=src("meshwire") / "addon",
                        MESHWIRE_ALLOW_PYTHON="1" if self.allow_python else "0")

    def server_params(self, workdir: Path) -> StdioServerParameters:
        return StdioServerParameters(
            command=UV, args=["run", "--frozen", "--directory", str(src("meshwire")), "meshwire",
                              "--port", str(self.server_port)],
            env=base_env(MESHWIRE_CONFIG_DIR=self.config_dir(workdir), MESHWIRE_PORT=self.server_port))


class MeshwirePythonSetup(MeshwireSetup):
    """Meshwire with "Allow Python" switched on, as a user would run it (owner's decision
    2026-11-17, after the pilot showed the gate-off agent stopping to ask for it). The Meshwire
    baseline from Phase 2 on; the gate-off runs stay on record as "meshwire"."""
    name = "meshwire-py"
    allow_python = True


MCP_SETUPS = {s.name: s for s in (BlenderLabSetup, AhujasidSetup, MeshwireSetup, MeshwirePythonSetup)}
