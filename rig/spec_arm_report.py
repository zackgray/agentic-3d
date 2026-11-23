"""The scored spec-first arm's table (rig/spec_arm.py): per product and arm, then per arm overall.
Tokens per pass is every token the arm spent (spec, revision and build, failures included) divided by
its passes, the project's headline metric."""
import json
from pathlib import Path
from statistics import median

ARMS = ("direct", "spec", "spec1")


def rows(results: Path) -> list[dict]:
    """The latest non-void row per (product, arm, rep)."""
    best = {}
    for line in results.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["verdict"] != "void":
                best[(r["product"], r["arm"], r["rep"])] = r
    return list(best.values())


def pct(v: float) -> str:
    return f"{v * 100:+.0f}%"


def errs(group: list[dict], key: str) -> str:
    vals = [r["score"]["err"][key] for r in group if "err" in r.get("score", {})]
    if not vals:
        return "n/a"
    return f"{pct(median(vals))} ({pct(min(vals))}..{pct(max(vals))})"


def summary(group: list[dict]) -> dict:
    passes = sum(1 for r in group if r.get("passed"))
    tokens = sum(r["tokens"] for r in group)
    return {"n": len(group), "passes": passes, "median_tokens": int(median(r["tokens"] for r in group)),
            "tokens_per_pass": round(tokens / passes) if passes else None,
            "checks_passed": sum(1 for r in group if r["verdict"] == "pass"),
            "cost": round(sum(r["cost_usd"] for r in group), 4)}


def report(results: Path) -> dict:
    data = rows(results)
    products = sorted({r["product"] for r in data})
    print("| Product | Arm | Passed | Checks | Median tokens | Height err | Width err | Volume err |")
    print("|---|---|---|---|---|---|---|---|")
    for p in products:
        for a in ARMS:
            g = [r for r in data if r["product"] == p and r["arm"] == a]
            if g:
                s = summary(g)
                print(f"| {p} | {a} | {s['passes']}/{s['n']} | {s['checks_passed']}/{s['n']} | {s['median_tokens']:,} "
                      f"| {errs(g, 'height')} | {errs(g, 'width')} | {errs(g, 'volume')} |")
    print("\n| Arm | Passed | Median tokens | Tokens per pass | Cost |")
    print("|---|---|---|---|---|")
    out = {}
    for a in ARMS:
        g = [r for r in data if r["arm"] == a]
        if g:
            s = out[a] = summary(g)
            tpp = f"{s['tokens_per_pass']:,}" if s["tokens_per_pass"] else "n/a"
            print(f"| {a} | {s['passes']}/{s['n']} | {s['median_tokens']:,} | {tpp} | ${s['cost']} |")
    return out
