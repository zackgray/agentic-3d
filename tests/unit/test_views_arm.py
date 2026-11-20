"""The views arm: every build task has its rendered views, revisions have none, and the views are part
of the prompt fingerprint, so re-rendering them can never mix with older runs."""
import shutil

import pytest

from suite import ROOT
from rig.blender import SetupError
from rig.prompt_arms import IMAGES
from rig.run import task_sha
from rig.task import BRIEF_VIEWS, load_task

TASKS = sorted(d for d in (ROOT / "tasks").iterdir() if d.is_dir() and not d.name.startswith("_"))


@pytest.mark.parametrize("folder", TASKS, ids=[d.name for d in TASKS])
def test_build_tasks_have_views_and_revisions_do_not(folder):
    has = all((folder / IMAGES["views"] / f"{v}.png").is_file() for v in BRIEF_VIEWS)
    assert has == (not folder.name.startswith("r"))


def test_views_change_the_fingerprint(tmp_path):
    src = ROOT / "tasks" / "p01-threaded-bottle"
    copy = tmp_path / src.name
    shutil.copytree(src, copy)
    task = load_task(copy)
    base, views = task_sha(task, "base"), task_sha(task, "views")
    assert base != views
    (copy / "brief" / "top.png").write_bytes(b"different")
    assert task_sha(load_task(copy), "views") != views
    assert task_sha(load_task(copy), "base") == base  # the text arm never depends on the images


def test_missing_view_is_a_setup_fault(tmp_path):
    copy = tmp_path / "p01"
    shutil.copytree(ROOT / "tasks" / "p01-threaded-bottle", copy)
    (copy / "brief" / "side.png").unlink()
    with pytest.raises(SetupError):
        load_task(copy).brief_images("brief")
