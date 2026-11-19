"""Proves a task's checks before any agent is trusted with them. Free: no model calls.

Builds the task's reference model (must pass every check), then each deliberately broken variant
(must fail exactly the checks it is meant to break). Variants are listed in task.toml.

    python -m rig.verify_checks tasks/p01-threaded-bottle
"""
import json
import sys
import tempfile
from pathlib import Path

from .blender import LIB, blender_path, make_starting_scene, run_checks, run_script
from .task import load_task


def build(exe, task, variant: str, tmp: Path) -> Path:
    blend = tmp / f"{variant}.blend"
    make_starting_scene(exe, task.starting_scene, blend, task.folder)
    code = tmp / f"{variant}.py"
    prelude = f"VARIANT = {variant!r}\nimport sys\nsys.path.insert(0, {str(LIB)!r})\n"
    code.write_text(prelude + task.reference.read_text(encoding="utf-8"), encoding="utf-8")
    result = tmp / f"{variant}.json"
    run_script(exe, "exec_code.py", [str(code), str(result)], blend=blend)
    out = json.loads(result.read_text(encoding="utf-8"))
    if not out["ok"]:
        raise RuntimeError(f"reference variant {variant} failed to build:\n{out['output']}")
    return blend


def main(task_dir: str) -> int:
    exe = blender_path()
    task = load_task(task_dir)
    bad = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for variant, must_fail in task.variants.items():
            must_fail = set(must_fail)
            res = run_checks(exe, build(exe, task, variant, tmp), task.checks)
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            ok = failed == must_fail
            bad += not ok
            print(f"{'OK ' if ok else 'BAD'} {variant:10} failed={sorted(failed)} expected={sorted(must_fail)}")
            if variant == "good" or not ok:
                for c in res["checks"]:
                    print(f"      {'pass' if c['passed'] else 'FAIL'} {c['check']}: {json.dumps(c['detail'])}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
