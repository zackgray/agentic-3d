"""Pinned versions of the MCP servers under test, and where each lives on disk.

Every number in the report is tied to these commits. Change a pin only on purpose, and bump the
setup's VERSION with it. vendor/ is git-ignored; `python -m rig.vendor_setup` recreates it.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR = ROOT / "vendor"
PROFILES = VENDOR / "profiles"  # one isolated Blender user profile per server (BLENDER_USER_RESOURCES)

PINS = {
    "blender-lab": {
        "repo": "https://projects.blender.org/lab/blender_mcp.git",
        "commit": "dbbf836ad4b1025f14a2b3b504c43903f39e0b04",  # main 2026-09-29; v1.0.2 lacks fix #31
        "license": "GPL-3.0-or-later",
        "port": 9877,
    },
    "ahujasid": {
        "repo": "https://github.com/ahujasid/mcp-for-blender.git",
        "commit": "b6a2ce30c14636a562b5549684d9db6fc01f29ab",  # HEAD 2026-11-15, pyproject 2.3.0, no tags
        "license": "MIT",
        "port": 9876,
    },
    "meshwire": {
        "repo": "https://github.com/RFingAdam/meshwire.git",
        "commit": "fc53b84ce7ba6d3ce8b5cbf6a469a5f54e8b1d83",  # tag v0.5.0, 2026-11-06
        "license": "AGPL-3.0-or-later",
        "port": 9878,
    },
}

HARNESS_PORT = 9890  # the rig's private control channel into GUI Blender (save, quit); never an agent tool


def src(name: str) -> Path:
    return VENDOR / name


def profile(name: str) -> Path:
    return PROFILES / name
