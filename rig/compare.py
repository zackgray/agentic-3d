"""Compares setups on the development suite, the way docs/eval-method.md says to.

    python -m rig.compare --setups no-mcp harness [--version harness=h2]

Counts only scored runs (pass/fail) that saw the current prompt of each task, at the given model,
effort and arm. Reports per setup: pass rate, tokens per passed task (the headline), the geometric
mean over tasks of each task's geometric-mean tokens, its ratio to the first setup, wall time, cost.
"""
import argparse
import json
import math
import sys
from collections import defaultdict
from statistics import mean

from .run import ROOT, prompt_sha
from .task import load_task


def gmean(xs):
    return math.exp(mean(math.log(x) for x in xs))


def load_runs(args, shas):
    want = dict(v.split("=", 1) for v in args.version)
    runs = defaultdict(list)
    for f in (ROOT / "runs").glob("*/result.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        s = r.get("setup")
        if s not in args.setups or r.get("verdict") not in ("pass", "fail"):
            continue
        if r.get("model") != args.model or r.get("effort") != args.effort or r.get("arm", "base") != args.arm:
            continue
        if r.get("prompt_sha") is None or r.get("prompt_sha") != shas.get(r["task"]):
            continue
        if s in want and r["versions"].get("setup") != f"{s} {want[s]}":
            continue
        runs[s].append(r)
    return runs


def summarise(rs):
    by_task = defaultdict(list)
    for r in rs:
        by_task[r["task"]].append(r["metrics"]["total_tokens"])
    passes = sum(r["verdict"] == "pass" for r in rs)
    tokens = sum(r["metrics"]["total_tokens"] for r in rs)
    return {
        "runs": len(rs), "passes": passes, "pass_rate": passes / len(rs),
        "tokens_per_pass": tokens / passes if passes else float("inf"),
        "gmean_tokens": gmean([gmean(v) for v in by_task.values()]),
        "task_gmeans": {t: gmean(v) for t, v in by_task.items()},
        "wall": mean(r["metrics"]["wall_seconds"] for r in rs),
        "turns": mean(r["metrics"]["turns"] for r in rs),
        "cost": sum(r["metrics"]["cost_usd"] or 0 for r in rs),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--setups", nargs="+", required=True, help="the first is the reference")
    p.add_argument("--version", nargs="*", default=[], help="setup=version, e.g. harness=h2")
    p.add_argument("--suite", default="tasks", choices=["tasks", "heldout", "heldout2", "heldout3", "heldout4"],
                   help="heldout (spent at h4), heldout2 (spent at h5), heldout3 (spent at h6) and heldout4 (for h7) are each run once, for a final claim (docs/eval-method.md)")
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--effort", default="low")
    p.add_argument("--arm", default="base")
    p.add_argument("--groups", action="store_true", help="also break down by task group")
    args = p.parse_args(argv)

    folders = sorted(d for d in (ROOT / args.suite).iterdir() if d.is_dir() and not d.name.startswith("_"))
    tasks = {d.name: load_task(d) for d in folders}
    shas = {n: prompt_sha(t.prompt, args.arm, t.scene_text) for n, t in tasks.items()}
    runs = load_runs(args, shas)
    stats = {s: summarise(runs[s]) for s in args.setups if runs[s]}
    ref = stats.get(args.setups[0])
    print(f"{'setup':<12}{'runs':>6}{'pass':>12}{'tok/pass':>10}{'gmean':>9}{'ratio':>7}{'turns':>7}{'wall s':>8}{'cost $':>8}")
    for s, st in stats.items():
        ratio = st["gmean_tokens"] / ref["gmean_tokens"] if ref else float("nan")
        print(f"{s:<12}{st['runs']:>6}{st['passes']:>5}/{st['runs']:<3}{st['pass_rate']:>4.0%}"
              f"{st['tokens_per_pass']:>10,.0f}{st['gmean_tokens']:>9,.0f}{ratio:>7.2f}{st['turns']:>7.1f}"
              f"{st['wall']:>8.1f}{st['cost']:>8.3f}")
    if args.groups:
        for s in stats:
            print(f"\n{s} by group (pass, tokens per pass):")
            grouped = defaultdict(list)
            for r in runs[s]:
                grouped[r["task"][0]].append(r)
            for g, rs in sorted(grouped.items()):
                st = summarise(rs)
                print(f"  {g}: {st['passes']}/{st['runs']}  {st['tokens_per_pass']:,.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
