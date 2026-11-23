"""The live spec-first session on a product-page brief (products/<id>/): the agent writes a dimensioned
spec from the page text and the one shot, the owner approves or corrects it, then the agent builds.

    python -m rig.spec_session spec volta                       # step 1: writes the spec
    python -m rig.spec_session revise volta --notes "..."       # the owner's corrections, back into the spec
    python -m rig.spec_session build volta                      # step 2: builds the newest spec
    python -m rig.spec_session compare volta                    # the build against the hidden key

Step 1 is one API call with no tools. Step 2 is an ordinary rig run on a task generated from the
spec (sandboxed by default, so the agent's code can't read the key). Everything for a session lives
in runs/_spec/<product>/<stamp>/ (git-ignored); the comparison and renders are for the owner only.
"""
import argparse
import base64
import glob
import json
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from .accounting import PRICES
from .blender import blender_path, run_checks, run_script
from .env import load_env
from .models import make_client
from .product_briefs import build as build_reference
from .spec_prompts import BUILD, DIRECT, NOTES, REVISE, SPEC
from . import run as rig_run

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS, SESSIONS = ROOT / "products", ROOT / "runs" / "_spec"


def product(prefix: str) -> Path:
    hits = [d for d in PRODUCTS.iterdir() if d.is_dir() and d.name.startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"{prefix!r} matches {[d.name for d in hits]}")
    return hits[0]


def newest(folder: Path) -> Path:
    sessions = sorted(d for d in (SESSIONS / folder.name).glob("*") if (d / "spec.md").is_file())
    if not sessions:
        raise SystemExit(f"no spec yet for {folder.name}: run the spec step first")
    return sessions[-1]


def write_spec(folder: Path, model: str, effort: str, parent: Path | None = None, notes: str = "",
               out: Path | None = None, quiet: bool = False) -> Path:
    """A spec from the brief, or (with parent and notes) the parent spec revised by the owner's notes,
    as a follow-up turn in the same conversation. Either way a new session folder holds the result."""
    meta = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))
    shot = base64.b64encode((folder / "shot.png").read_bytes()).decode("ascii")
    prompt = SPEC.format(page=meta["page"])
    messages = [{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": shot}},
        {"type": "text", "text": prompt}]}]
    if parent is not None:
        messages += [{"role": "assistant", "content": (parent / "spec.md").read_text(encoding="utf-8").strip()},
                     {"role": "user", "content": REVISE.format(notes=notes.strip())}]
    resp = make_client(model).messages.create(
        model=model, max_tokens=16000, output_config={"effort": effort}, messages=messages)
    spec = "\n".join(b.text for b in resp.content if b.type == "text").strip()
    out = out or SESSIONS / folder.name / f"{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    u = resp.usage
    p_in, p_out, _ = PRICES.get(model, (0, 0, 0))
    cost = (u.input_tokens * p_in + u.output_tokens * p_out) / 1e6
    (out / "spec.md").write_text(spec + "\n", encoding="utf-8")
    (out / "spec.json").write_text(json.dumps({
        "product": folder.name, "model": model, "effort": effort, "stop_reason": resp.stop_reason,
        "prompt": prompt, "parent": parent.name if parent else None, "notes": notes, "usage": u.model_dump(mode="json"), "cost_usd": round(cost, 5)}, indent=2), encoding="utf-8")
    if not quiet:
        print(spec)
    print(f"\n[{model} {effort}: in {u.input_tokens}, out {u.output_tokens}, ${cost:.4f}] -> {out}")
    return out


def make_task(folder: Path, session: Path, notes: str, direct: bool = False) -> Path:
    """The build task for a session folder: from its spec.md, or (direct) from the brief itself."""
    meta = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))
    names = meta["objects"]
    quoted = " and ".join(f'"{n}"' for n in names)
    if direct:
        prompt = DIRECT.format(page=meta["page"], names=quoted)
    else:
        spec = (session / "spec.md").read_text(encoding="utf-8").strip()
        prompt = BUILD.format(spec=spec, notes=NOTES.format(notes=notes.strip()) if notes.strip() else "",
                              names=quoted)
    task = session / f"spec-{folder.name}"
    task.mkdir(exist_ok=True)
    (task / "shot.png").write_bytes((folder / "shot.png").read_bytes())
    checks = [{"type": "objects", "expected": names},
              {"type": "transforms_applied", "objects": names},
              {"type": "watertight", "objects": names},
              {"type": "self_intersection", "objects": names}]
    checks += [{"type": "no_overlap", "a": a, "b": b} for i, a in enumerate(names) for b in names[i + 1:]]
    toml = [f'id = "spec-{folder.name}"', f'title = "{meta["name"]} from {"its brief" if direct else "its approved spec"}"',
            'starting_scene = "empty"', 'images = ["shot.png"]', f"prompt = {json.dumps(prompt)}"]
    for c in checks:
        toml.append("\n[[checks]]")
        toml += [f"{k} = {json.dumps(v)}" for k, v in c.items()]
    (task / "task.toml").write_text("\n".join(toml) + "\n", encoding="utf-8")
    (session / "notes.txt").write_text(notes, encoding="utf-8")
    return task


def compare(folder: Path, session: Path) -> dict:
    """The build's sizes and volumes against facts.json, plus renders of the build and the reference."""
    exe = blender_path()
    runs = sorted(glob.glob(str(ROOT / "runs" / f"*_spec-{folder.name}_*")))
    runs = [r for r in runs if Path(r, "result.json").is_file()
            and json.loads(Path(r, "result.json").read_text(encoding="utf-8")).get("label") == session.name]
    if not runs:
        raise SystemExit(f"no build for session {session}")
    run = Path(runs[-1])
    facts = json.loads((folder / "facts.json").read_text(encoding="utf-8"))
    checks = []
    for name, f in facts["objects"].items():
        checks.append({"type": "bbox", "object": name, "label": f"{name} size", "tol": 0.002,
                       "min": [v / 1000 for v in f["min_mm"]], "max": [v / 1000 for v in f["max_mm"]]})
        checks.append({"type": "volume", "object": name, "label": f"{name} volume", "rel_tol": 0.05,
                       "mm3": f["volume_ml"] * 1000})
    got = run_checks(exe, run / "scene.blend", checks)
    run_script(exe, "review_render.py", [str(session / "build")], blend=run / "scene.blend", timeout=300)
    ref = session / "reference"
    if not (ref / "top.png").is_file():
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            run_script(exe, "review_render.py", [str(ref)], blend=build_reference(exe, folder, Path(t)), timeout=300)
    (session / "compare.json").write_text(json.dumps({"run": run.name, "checks": got}, indent=2), encoding="utf-8")
    for c in got["checks"]:
        d = c["detail"]
        if "volume_mm3" in d:
            print(f"{c['check']:>16}: {d['volume_mm3'] / 1000:.1f} mL vs key {d['expected_mm3'] / 1000:.1f} mL")
        elif "min_mm" in d:
            size = [round(h - l, 1) for l, h in zip(d["min_mm"], d["max_mm"])]
            key = [round(h - l, 1) for l, h in zip(d["expected_min_mm"], d["expected_max_mm"])]
            print(f"{c['check']:>16}: {size} mm, top z {d['max_mm'][2]} vs key {key} mm, top z {d['expected_max_mm'][2]}")
        else:
            print(f"{c['check']:>16}: {json.dumps(d)}")
    print(f"renders: {session / 'build'}  reference: {ref}")
    return got


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["spec", "revise", "build", "compare"])
    p.add_argument("product", help="product folder name or prefix")
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--effort", default="low")
    p.add_argument("--setup", default="harness-sandbox")
    p.add_argument("--notes", default="", help="revise: the owner's corrections, in plain words")
    args = p.parse_args(argv)
    load_env(ROOT / ".env")
    folder = product(args.product)
    if args.step == "spec":
        write_spec(folder, args.model, args.effort)
        return 0
    session = newest(folder)
    if args.step == "revise":
        if not args.notes.strip():
            raise SystemExit("revise needs --notes")
        write_spec(folder, args.model, args.effort, parent=session, notes=args.notes)
        return 0
    if args.step == "build":
        task = make_task(folder, session, "")
        return rig_run.main([str(task), "--setup", args.setup, "--model", args.model, "--effort", args.effort,
                             "--label", session.name])
    compare(folder, session)
    return 0


if __name__ == "__main__":
    sys.exit(main())
