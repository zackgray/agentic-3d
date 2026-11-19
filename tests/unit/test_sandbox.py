"""rig.setups.sandbox: the container's walls are in the command line, and responses are framed apart
from Blender's own output. The live walls are checked by tests/sandbox_walls.py."""
import io
import queue
from pathlib import Path

from rig.setups.sandbox import MARK, SandboxHarnessSetup, docker_cmd


def test_walls_in_command(tmp_path):
    cmd = docker_cmd("a3d-x", tmp_path, "scene.blend")
    joined = " ".join(cmd)
    for wall in ("--network none", "--read-only", "--cap-drop ALL", "--security-opt no-new-privileges",
                 "--user 1000:1000", "--rm", "--disable-autoexec", "--stdio"):
        assert wall in joined
    mounts = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-v"]
    assert mounts == [f"{tmp_path.resolve()}:/work", f"{Path('rig/blender_side').resolve()}:/side:ro"]
    envs = [cmd[i + 1] for i, a in enumerate(cmd) if a == "-e"]
    assert envs == ["HOME=/tmp"]  # nothing from the host environment
    assert "-p" not in cmd and "--publish" not in cmd and "--privileged" not in cmd


def test_framing_separates_responses_from_blender_output():
    out = io.BytesIO(b"Blender 5.2.3\n" + (MARK + '{"a": 1}\n').encode()
                     + b"partial line " + (MARK + '{"b": 2}\n').encode() + b"Read prefs\n")
    lines, log = queue.Queue(), io.StringIO()
    SandboxHarnessSetup._read(out, lines, log)
    got = []
    while (x := lines.get_nowait()) is not None:
        got.append(x.strip())
    assert got == ['{"a": 1}', '{"b": 2}']
    assert "Blender 5.2.3" in log.getvalue() and "Read prefs" in log.getvalue()
