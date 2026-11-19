"""Every task in every suite is well-formed, following docs/task-authoring.md."""
import ast
import tomllib

import pytest

from suite import ROOT, SUITES, task_folders
from rig.task import load_task

FOLDERS = task_folders()
IDS = [f"{d.parent.name}/{d.name}" for d in FOLDERS]
GROUPS = {"hard-surface", "revision", "layout", "multi-step"}
SHAPE_TYPES = {"volume", "ray_probe", "helical_thread"}

# Known departures from the authoring rules, found when these tests were written (2026-11-18).
# Each is a strict xfail: fixing the task turns it into an unexpected pass, so remove it from here.
ID_MISMATCH: set[str] = set()
UNPROVEN = {("tasks/m01-flashlight", "probe_tail"), ("tasks/p04-gable-carton", "probe_body"),
            ("heldout3/z08-desk-fan", "volume_motor")}


def check_types():
    """Check types the Blender side defines (def check_<type>), read without importing bpy."""
    names = set()
    for f in (ROOT / "rig" / "blender_side").glob("checks_*.py"):
        for node in ast.parse(f.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("check_"):
                names.add(node.name[len("check_"):])
    return names


def raw(folder):
    return tomllib.loads((folder / "task.toml").read_text(encoding="utf-8"))


def names(task):
    """The name each check reports under, which variants list: its label, else its type."""
    return [c.get("label", c["type"]) for c in task.checks]


def test_suites_are_not_empty():
    for s in SUITES:
        assert any(d.parent.name == s for d in FOLDERS), s


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_loads(folder):
    task = load_task(folder)
    assert task.prompt and task.title and task.checks
    assert task.reference.is_file()


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_id_matches_folder(folder, request):
    if f"{folder.parent.name}/{folder.name}" in ID_MISMATCH:
        request.applymarker(pytest.mark.xfail(strict=True, reason="known id/folder mismatch"))
    assert load_task(folder).id == folder.name


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_group(folder):
    assert raw(folder).get("group") in GROUPS


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_starting_scene(folder):
    task, group = load_task(folder), raw(folder)["group"]
    if task.starting_scene != "empty":
        assert task.starting_scene.endswith(".py") and (folder / task.starting_scene).is_file()
    if group == "revision":
        assert task.starting_scene != "empty", "a revision starts from an approved model"
        assert "unchanged" in task.variants, "revision tasks need an 'unchanged' variant"


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_check_types_exist(folder):
    known = check_types()
    assert {c["type"] for c in load_task(folder).checks} <= known


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_check_names_unique(folder):
    n = names(load_task(folder))
    assert len(n) == len(set(n)), "label every check whose type appears more than once"


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_good_variant_fails_nothing(folder):
    task = load_task(folder)
    assert "good" in task.variants and task.variants["good"] == []


@pytest.mark.parametrize("folder", FOLDERS, ids=IDS)
def test_variants_name_real_checks(folder):
    task = load_task(folder)
    valid = set(names(task))
    for variant, must_fail in task.variants.items():
        assert len(must_fail) == len(set(must_fail)), variant
        assert set(must_fail) <= valid, f"{variant}: {sorted(set(must_fail) - valid)}"


SHAPE_CASES = [(d, n) for d in FOLDERS for c in load_task(d).checks if c["type"] in SHAPE_TYPES
               for n in [c.get("label", c["type"])]]


@pytest.mark.parametrize("folder,check", SHAPE_CASES, ids=[f"{d.parent.name}/{d.name}:{n}" for d, n in SHAPE_CASES])
def test_shape_check_proven_by_a_variant(folder, check, request):
    if (f"{folder.parent.name}/{folder.name}", check) in UNPROVEN:
        request.applymarker(pytest.mark.xfail(strict=True, reason="known unproven shape check"))
    failed = {f for v in load_task(folder).variants.values() for f in v}
    assert check in failed, "every shape check must be failed by at least one variant"
