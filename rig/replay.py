"""Replays recorded harness runs through the current harness code, call by call, then re-checks the
final scene. Free: no model calls. It reuses each run's recorded code, so it shows what the current
harness does with the same agent actions; it is diagnostic, not a measurement of a live agent.

    python -m rig.replay runs/_matrix-h4 [--version "harness h4"] [--setup harness] [--out runs/_replay-h5/replay.json]

--setup replays through another setup: e.g. --version "no-mcp rig-1" --setup no-mcp-sandbox checks that
the sandboxed baseline gives the host's verdicts on the same agent code.

Used 2026-11-18 to check h5 against all 114 recorded h4 runs before spending (docs/journal.md).
"""
import argparse
import json
import shutil
from pathlib import Path

from .blender import blender_path, make_starting_scene, run_checks
from .run import SETUPS
from .task import load_task

ROOT = Path(__file__).resolve().parent.parent


def task_dir(name: str) -> Path:
    for suite in ("tasks", "heldout", "heldout2", "heldout3", "heldout4"):
        if (ROOT / suite / name).is_dir():
            return ROOT / suite / name
    raise SystemExit(f"task {name} not found")


def replay(exe, run: Path, work: Path, setup: str = "harness") -> tuple:
    r = json.loads((run / "result.json").read_text(encoding="utf-8"))
    calls = [(b["name"], b["input"]) for m in json.loads((run / "transcript.json").read_text(encoding="utf-8"))
             if isinstance(m["content"], list) for b in m["content"] if b.get("type") == "tool_use"]
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    task = load_task(task_dir(r["task"]))
    scene = work / "scene.blend"
    make_starting_scene(exe, task.starting_scene, scene, task.folder)
    h, n = SETUPS[setup](exe), 0
    h.start(work, scene)
    if hasattr(h, "initial_context"):
        h.initial_context()
    try:
        for name, inp in calls:
            n += 1
            if getattr(h.call(name, inp), "final", False):
                break
    finally:
        h.stop()
    verdict = "pass" if run_checks(exe, scene, task.checks)["passed"] else "fail"
    return r["task"], r["verdict"], len(calls), verdict, n


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("runs", nargs="+", help="folders holding run folders")
    p.add_argument("--version", default="harness h4", help="replay only runs recorded on this setup version")
    p.add_argument("--setup", default="harness", choices=sorted(SETUPS), help="replay through this setup")
    p.add_argument("--out", default="runs/_replay/replay.json")
    args = p.parse_args(argv)
    exe, rows = blender_path(), []
    for folder in args.runs:
        for run in sorted(Path(folder).glob("*_*")):
            if not (run / "result.json").is_file():
                continue
            rec = json.loads((run / "result.json").read_text(encoding="utf-8"))
            if rec["versions"].get("setup") != args.version:
                continue
            for attempt in range(3):  # a setup fault (e.g. the port-file race on Windows) is retried, never scored
                try:
                    row = replay(exe, run, ROOT / "runs" / "_smoke" / "replay", args.setup)
                    break
                except OSError as e:
                    print(f"setup fault on {run.name}, retrying: {e}", flush=True)
            else:
                raise SystemExit(f"{run.name}: setup fault three times")
            rows.append(row)
            print("{} recorded {} in {} calls; replayed {} in {} calls".format(*row), flush=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{len(rows)} runs; recorded passes {sum(r[1] == 'pass' for r in rows)}, "
          f"replayed passes {sum(r[3] == 'pass' for r in rows)}; written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
