"""The scored spec-first arm: three ways from a product-page brief to a model, repeated and scored
against each product's hidden key (products/<id>/facts.json).

    python -m rig.spec_arm run --reps 5          # resumable; skips reps already scored
    python -m rig.spec_arm report                # the table (rig/spec_arm_report.py)

Arms, per product and rep:
- direct: the brief (page text and shot) goes straight to the builder, no spec step.
- spec:   the first spec, built as-is, as if a non-modeller approved it unread.
- spec1:  the first spec, one fixed correction (CORRECTIONS, frozen before any run), the revised spec built.

Scoring is on the main container's outside (the product's first object), probed by rays
(blender_side/outer_profile.py) on the build and on the key's reference model: height, widest width
and outside volume within 5%, plus the generic build checks. A shape error (profile mismatch with
scale taken out) is reported but not scored. Solid or hollow doesn't count, and caps are left out:
both are modelling conventions. Everything lives in runs/_arm/ (git-ignored); results.jsonl is one line per rep.
"""
import argparse
import json
import sys
import tempfile
import tomllib
from pathlib import Path

from .blender import SetupError, blender_path, run_script
from .env import load_env
from .product_briefs import build as build_reference
from .spec_session import PRODUCTS, ROOT, make_task, write_spec
from . import run as rig_run

ARM_DIR = ROOT / "runs" / "_arm"
RESULTS = ARM_DIR / "results.jsonl"
ARMS = ("direct", "spec", "spec1")
TOL = 0.05  # a rep passes when height, width and volume are all within 5% of the key

# One correction per product, in the client's words: what kind of product it is, never a number.
# Frozen 2026-11-23 before the first scored run; changing one starts a new arm.
CORRECTIONS = {
    "volta-soda-20oz": "It's a standard 20 oz soda bottle. Make the bottle solid; a plain cap and a flat base are fine.",
    "halden-can-12oz": "It's a normal 12 oz drinks can with a closed lid.",
    "northpeak-water-500ml": "It's an ordinary half-litre water bottle; please check the bottle's own volume works out to about that. A plain small cap and a flat base are fine.",
    "orchard-carton-52oz": "It's a standard gable-top carton: the top slopes like a roof up to a thin sealed fin.",
}


def spec_usage(session: Path) -> dict:
    j = json.loads((session / "spec.json").read_text(encoding="utf-8"))
    u = j["usage"]
    return {"tokens": u["input_tokens"] + u["output_tokens"], "cost": j["cost_usd"], "stop": j["stop_reason"]}


def find_run(product: str, label: str) -> Path | None:
    for r in sorted((ROOT / "runs").glob(f"*_spec-{product}_*"), reverse=True):
        res = r / "result.json"
        if res.is_file() and json.loads(res.read_text(encoding="utf-8")).get("label") == label:
            return r
    return None


def profile(exe: Path, blend: Path, name: str) -> dict:
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "profile.json"
        proc = run_script(exe, "outer_profile.py", [str(out), name], blend=blend, timeout=300)
        if proc.returncode != 0 or not out.is_file():
            raise SetupError(f"outer_profile failed: {proc.stderr[-1500:]}")
        return json.loads(out.read_text(encoding="utf-8"))


def key_profile(exe: Path, folder: Path, name: str) -> dict:
    cache = ARM_DIR / folder.name / "key_profile.json"
    if not cache.is_file():
        with tempfile.TemporaryDirectory() as t:
            prof = profile(exe, build_reference(exe, folder, Path(t)), name)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(prof), encoding="utf-8")
    return json.loads(cache.read_text(encoding="utf-8"))


def shape_error(a: dict, b: dict) -> float:
    """Profile mismatch with scale taken out: each profile's radius over its own widest, compared at
    the same fraction of height. Mean absolute difference, as a fraction of the widest radius."""
    ra, rb = [l["r_eq_mm"] for l in a["levels"]], [l["r_eq_mm"] for l in b["levels"]]
    ma, mb = max(ra) or 1, max(rb) or 1
    return sum(abs(x / ma - y / mb) for x, y in zip(ra, rb)) / len(ra)


def measure(exe: Path, folder: Path, run: Path) -> dict:
    """Main container's outside against the key's. A missing object scores as a miss, not a crash."""
    main = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))["objects"][0]
    got, key = profile(exe, run / "scene.blend", main), key_profile(exe, folder, main)
    if "missing" in got:
        return {"main": main, "missing": True, "within": False}
    facts = json.loads((folder / "facts.json").read_text(encoding="utf-8"))["objects"][main]

    def dims(p):  # width is the widest equivalent-circle diameter, the same measure on both sides
        width = 2 * max(l["r_eq_mm"] for l in p["levels"])
        return {"height_mm": round(p["z1_mm"] - p["z0_mm"], 1), "width_mm": round(width, 1), "outer_ml": p["outer_ml"]}

    g, k = dims(got), dims(key)
    err = {"height": g["height_mm"] / k["height_mm"] - 1, "width": g["width_mm"] / k["width_mm"] - 1,
           "volume": g["outer_ml"] / k["outer_ml"] - 1}
    return {"main": main, **g, "enclosed_ml": got["enclosed_ml"], "key": {**k, "facts_volume_ml": facts["volume_ml"]},
            "err": {k2: round(v, 4) for k2, v in err.items()}, "shape_err": round(shape_error(got, key), 4),
            "hollow": got["enclosed_ml"] < 0.5 * got["outer_ml"],
            "within": all(abs(v) <= TOL for v in err.values())}


def build(folder: Path, session: Path, label: str, direct: bool, model: str, effort: str, setup: str) -> Path | None:
    """The build, retried on a void (a setup fault is never the agent's failure)."""
    task = make_task(folder, session, "", direct=direct)
    for _ in range(3):
        rig_run.main([str(task), "--setup", setup, "--model", model, "--effort", effort,
                      "--label", label, "--max-cost", "0.10"])
        run = find_run(folder.name, label)
        if run and json.loads((run / "result.json").read_text(encoding="utf-8"))["verdict"] != "void":
            return run
    return run


def one_rep(exe: Path, folder: Path, arm: str, rep: int, args) -> dict:
    rep_dir = ARM_DIR / folder.name / f"{arm}-r{rep}"
    rep_dir.mkdir(parents=True, exist_ok=True)
    label = f"arm/{arm}/{folder.name}/r{rep}"
    steps = []
    session = rep_dir
    if arm != "direct":
        first = rep_dir / "spec"
        if not (first / "spec.md").is_file():
            write_spec(folder, args.model, args.effort, out=first, quiet=True)
        steps.append(spec_usage(first))
        session = first
        if arm == "spec1":
            revised = rep_dir / "revised"
            if not (revised / "spec.md").is_file():
                write_spec(folder, args.model, args.effort, parent=first, notes=CORRECTIONS[folder.name],
                           out=revised, quiet=True)
            steps.append(spec_usage(revised))
            session = revised
    run = build(folder, session, label, arm == "direct", args.model, args.effort, args.setup)
    res = json.loads((run / "result.json").read_text(encoding="utf-8")) if run else {"verdict": "void"}
    m = res.get("metrics", {})
    row = {"product": folder.name, "arm": arm, "rep": rep, "model": args.model, "run": run.name if run else None,
           "verdict": res["verdict"], "build_tokens": m.get("total_tokens"), "build_turns": m.get("turns"),
           "spec_tokens": sum(s["tokens"] for s in steps), "spec_stops": [s["stop"] for s in steps],
           "cost_usd": round(m.get("cost_usd", 0) + sum(s["cost"] for s in steps), 5)}
    row["tokens"] = (row["build_tokens"] or 0) + row["spec_tokens"]
    if res["verdict"] != "void":
        row["score"] = measure(exe, folder, run)
        row["passed"] = res["verdict"] == "pass" and row["score"].get("within", False)
    return row


def done_reps() -> set:
    if not RESULTS.is_file():
        return set()
    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {(r["product"], r["arm"], r["rep"]) for r in rows if r["verdict"] != "void"}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["run", "report", "rescore"])
    p.add_argument("--reps", type=int, default=5)
    p.add_argument("--products", nargs="*", default=sorted(CORRECTIONS))
    p.add_argument("--arms", nargs="*", default=list(ARMS), choices=ARMS)
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--effort", default="low")
    p.add_argument("--setup", default="harness-sandbox")
    p.add_argument("--max-spend", type=float, default=1.00, help="USD for this invocation; stops there")
    args = p.parse_args(argv)
    if args.step == "report":
        from .spec_arm_report import report
        report(RESULTS)
        return 0
    if args.step == "rescore":  # the scorer changed: re-measure every scored row in place, no model calls
        exe, out = blender_path(), []
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["verdict"] != "void":
                r["score"] = measure(exe, PRODUCTS / r["product"], ROOT / "runs" / r["run"])
                r["passed"] = r["verdict"] == "pass" and r["score"]["within"]
            out.append(json.dumps(r))
        RESULTS.write_text("\n".join(out) + "\n", encoding="utf-8")
        return 0
    load_env(ROOT / ".env")
    exe, done, spent = blender_path(), done_reps(), 0.0
    ARM_DIR.mkdir(parents=True, exist_ok=True)
    for rep in range(1, args.reps + 1):  # reps outermost, so a stopped run leaves every cell with data
        for name in args.products:
            for arm in args.arms:
                if (name, arm, rep) in done:
                    continue
                if spent >= args.max_spend:
                    print(f"spend guard: ${spent:.3f} reached, stopping")
                    return 0
                row = one_rep(exe, PRODUCTS / name, arm, rep, args)
                spent += row["cost_usd"]
                with RESULTS.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row) + "\n")
                s = row.get("score", {})
                print(f"== {name} {arm} r{rep}: {row['verdict']} passed={row.get('passed')} tokens={row['tokens']} "
                      f"err={s.get('err')} ${row['cost_usd']} (total ${spent:.3f})", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
