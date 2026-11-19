"""Runs a matrix of tasks x setups x repeats, one run at a time, interleaved so that drift over the
session (API latency, machine load) lands on every setup equally. Skips cells that already hold
enough non-void runs, so an interrupted batch resumes where it stopped.

    python -m rig.batch --tasks p01 p02 p03 p04 p05 --setups no-mcp blender-lab ahujasid meshwire --repeats 3
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from .run import ROOT, SETUPS, prompt_sha
from .task import load_task
from .run import main as run_one


def done_counts(model: str, effort: str, arm: str, shas: dict) -> Counter:
    """Scored runs per (task, setup) that saw exactly the current prompt (task text + arm)."""
    c = Counter()
    for f in (ROOT / "runs").glob("*/result.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("model") == model and r.get("effort") == effort and r.get("arm", "base") == arm \
                and r.get("verdict") in ("pass", "fail") and r.get("prompt_sha") is not None and r.get("prompt_sha") == shas.get(r["task"]):
            c[(r["task"], r["setup"])] += 1
    return c


def resolve_tasks(folders: list[Path], prefixes: list[str]) -> list[Path]:
    """Each prefix must match exactly one task folder name; anything else stops the batch."""
    tasks = []
    for t in prefixes:
        match = [d for d in folders if d.name.startswith(t)]
        if len(match) != 1:
            raise SystemExit(f"task {t!r} matches {[m.name for m in match]}")
        tasks.append(match[0])
    return tasks


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", nargs="+", required=True, help="task folder names or unique prefixes")
    p.add_argument("--setups", nargs="+", required=True, choices=sorted(SETUPS))
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--suite", default="tasks", choices=["tasks", "heldout", "heldout2", "heldout3", "heldout4"],
                   help="heldout (spent at h4), heldout2 (spent at h5), heldout3 (spent at h6) and heldout4 (for h7) are each run once, for a final claim (docs/eval-method.md)")
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--effort", default="low")
    p.add_argument("--arm", default="base")
    p.add_argument("--max-runs", type=int, default=100, help="hard stop, a spend guard")
    args = p.parse_args(argv)

    folders = sorted(d for d in (ROOT / args.suite).iterdir() if d.is_dir() and not d.name.startswith("_"))
    tasks = resolve_tasks(folders, args.tasks)

    shas = {t.name: prompt_sha((lt := load_task(t)).prompt, args.arm, lt.scene_text) for t in tasks}
    done, started = done_counts(args.model, args.effort, args.arm, shas), 0
    for rep in range(args.repeats):
        for task in tasks:
            for setup in args.setups:
                if done[(task.name, setup)] > rep:
                    continue
                if started >= args.max_runs:
                    print("max-runs reached; stopping")
                    return 0
                started += 1
                print(f"--- [{started}] {task.name} / {setup} / repeat {rep + 1}", flush=True)
                run_one([str(task), "--setup", setup, "--model", args.model, "--effort", args.effort, "--arm", args.arm])
                sys.stdout.flush()
    print(f"batch complete: {started} runs started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
