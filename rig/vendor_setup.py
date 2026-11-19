"""Fetches each MCP server at its pinned commit and installs its Blender side into an isolated
Blender profile, so runs never touch the owner's own Blender settings. Idempotent.

    python -m rig.vendor_setup
"""
import os
import shutil
import subprocess
import sys

from .blender import blender_path
from .setups.pins import PINS, PROFILES, profile, src


def git(*args, cwd=None):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def fetch(name: str) -> None:
    pin, dest = PINS[name], src(name)
    if not dest.is_dir():
        git("clone", "-q", pin["repo"], str(dest))
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=dest, capture_output=True, text=True).stdout.strip()
    if head != pin["commit"]:
        git("fetch", "-q", "origin", cwd=dest)
        git("checkout", "-q", pin["commit"], cwd=dest)
    print(f"{name}: {pin['commit'][:8]}")


def blender(exe, name, *args):
    env = dict(os.environ, BLENDER_USER_RESOURCES=str(profile(name)))
    out = subprocess.run([str(exe), *args], env=env, capture_output=True, text=True, timeout=300)
    if out.returncode != 0:
        raise SystemExit(f"{name}: blender {' '.join(args[:3])} failed:\n{out.stdout[-1500:]}{out.stderr[-1500:]}")


def install_lab(exe) -> None:
    """The official server is a Blender extension; its GUI auto-start reads the port from prefs."""
    build = PROFILES / "_build"
    build.mkdir(parents=True, exist_ok=True)
    blender(exe, "blender-lab", "--command", "extension", "build",
            f"--source-dir={src('blender-lab') / 'addon' / 'blender_mcp_addon'}", f"--output-dir={build}")
    zips = sorted(build.glob("mcp-*.zip"))
    blender(exe, "blender-lab", "--online-mode", "--background", "--factory-startup", "--command",
            "extension", "install-file", str(zips[-1]), "--repo", "user_default", "--enable")
    port = PINS["blender-lab"]["port"]
    blender(exe, "blender-lab", "--background", "--python-expr",
            "import bpy; p = bpy.context.preferences.addons['bl_ext.user_default.mcp'].preferences; "
            f"p.port = {port}; p.autostart_delay = 0.0; bpy.ops.wm.save_userpref()")


def install_ahujasid(exe) -> None:
    """The community server is a single-file legacy add-on, enabled by the boot script."""
    addons = profile("ahujasid") / "scripts" / "addons"
    addons.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src("ahujasid") / "addon.py", addons / "mcp_for_blender.py")


def main() -> int:
    exe = blender_path()
    for name in PINS:
        fetch(name)
        profile(name).mkdir(parents=True, exist_ok=True)
    install_lab(exe)
    install_ahujasid(exe)
    # Meshwire's add-on is imported straight from its checkout by the boot script, as its own
    # test harness does, so it needs no install step.
    for name in PINS:  # build each server's Python environment now, not inside a timed run
        sub = src(name) / "mcp" if name == "blender-lab" else src(name)
        subprocess.run(["uv", "sync", "--quiet", "--directory", str(sub)], check=True)
    print("vendor ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
