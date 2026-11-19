"""rig.env's .env loader, and the prompt arms and fingerprint that decide which runs are comparable."""
import os

import pytest

from rig.env import load_env
from rig.prompt_arms import ARMS, REQUEST, apply
from rig.run import prompt_sha

KEYS = ["A3D_TEST_NEW", "A3D_TEST_SET", "A3D_TEST_EMPTY", "A3D_TEST_QUOTED", "A3D_TEST_SINGLE", "A3D_TEST_EQ"]


@pytest.fixture
def env(monkeypatch):
    for k in KEYS:
        monkeypatch.delenv(k, raising=False)
    yield monkeypatch
    for k in KEYS:  # load_env writes os.environ directly; undo it
        os.environ.pop(k, None)


def test_load_env(tmp_path, env):
    env.setenv("A3D_TEST_SET", "from-shell")
    env.setenv("A3D_TEST_EMPTY", "")
    f = tmp_path / ".env"
    f.write_text("# comment\n\nnot a pair\n A3D_TEST_NEW = new \nA3D_TEST_SET=from-file\n"
                 "A3D_TEST_EMPTY=filled\nA3D_TEST_QUOTED=\"q v\"\nA3D_TEST_SINGLE='s'\nA3D_TEST_EQ=a=b\n",
                 encoding="utf-8")
    load_env(f)
    assert os.environ["A3D_TEST_NEW"] == "new"
    assert os.environ["A3D_TEST_SET"] == "from-shell"  # already set wins
    assert os.environ["A3D_TEST_EMPTY"] == "filled"    # set but empty counts as unset
    assert os.environ["A3D_TEST_QUOTED"] == "q v"
    assert os.environ["A3D_TEST_SINGLE"] == "s"
    assert os.environ["A3D_TEST_EQ"] == "a=b"


def test_load_env_empty_value_is_skipped(tmp_path, env):
    (tmp_path / ".env").write_text("A3D_TEST_NEW=\n", encoding="utf-8")
    load_env(tmp_path / ".env")
    assert "A3D_TEST_NEW" not in os.environ


def test_load_env_missing_file(tmp_path):
    load_env(tmp_path / "nope.env")  # no error


def test_apply_base_is_unchanged():
    assert apply("Build it.\n", "base") == "Build it.\n"


def test_apply_appends_once():
    out = apply("Build it.\n", "clean-mesh")
    assert out == "Build it.\n\n" + ARMS["clean-mesh"]
    with pytest.raises(ValueError):
        apply(out, "clean-mesh")


def test_request_arms_are_arms():
    assert set(REQUEST) <= set(ARMS)


def test_prompt_sha():
    a = prompt_sha("Build it.", "base")
    assert len(a) == 12
    assert a == prompt_sha("Build it.", "base", "")
    assert a != prompt_sha("Build it!", "base")
    assert a != prompt_sha("Build it.", "clean-mesh")
    assert a != prompt_sha("Build it.", "base", "scene = 1")
    # arms that only change the request hash like base; runs keep them apart by their arm field
    assert a == prompt_sha("Build it.", "think-off")
