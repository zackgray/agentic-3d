"""Re-runs the current checks on a recorded run's final scene, e.g. after a check bug is fixed.
The original verdict is kept in the record's recheck history, never overwritten silently.

    python -m rig.recheck runs/<run id> [--reason "why"]
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .blender import blender_path, run_checks
from .run import rig_version
from .task import load_task

ROOT = Path(__file__).resolve().parent.parent


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir")
    p.add_argument("--reason", default="")
    args = p.parse_args(argv)
    run_dir = Path(args.run_dir)
    rec = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    if rec["verdict"] == "void":
        print("void run: nothing to recheck")
        return 1
    checks = run_checks(blender_path(), run_dir / "scene.blend", load_task(ROOT / "tasks" / rec["task"]).checks)
    verdict = "pass" if checks["passed"] else "fail"
    rec.setdefault("rechecks", []).append({
        "at": datetime.now(timezone.utc).isoformat(), "rig": rig_version(), "reason": args.reason,
        "previous_verdict": rec["verdict"], "previous_checks": rec["checks"]})
    rec["checks"], rec["verdict"] = checks, verdict
    (run_dir / "result.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print(f"{verdict.upper()}  {rec['run_id']}  (was {rec['rechecks'][-1]['previous_verdict']})")
    for c in checks["checks"]:
        if not c["passed"]:
            print(f"  FAIL {c['check']}: {json.dumps(c['detail'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
