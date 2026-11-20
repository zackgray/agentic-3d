"""Builds the product-page briefs in products/: for each invented product, its hidden reference model,
a product-page style front shot (shot.png) and the measured key (facts.json). Free: no model calls.

    python -m rig.product_briefs                  # every product
    python -m rig.product_briefs volta halden     # a subset, by prefix

A brief is what a product page gives: the page text in product.toml and the one front shot. Everything
else (the reference model, facts.json) is the key the agent's spec and build are scored against.
"""
import json
import sys
import tempfile
import tomllib
from pathlib import Path

from .blender import LIB, blender_path, make_starting_scene, run_script

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / "products"


def build(exe, folder: Path, tmp: Path) -> Path:
    blend, code, result = tmp / "ref.blend", tmp / "ref.py", tmp / "ref.json"
    make_starting_scene(exe, "empty", blend)
    code.write_text(f"import sys\nsys.path.insert(0, {str(LIB)!r})\n"
                    + (folder / "reference.py").read_text(encoding="utf-8"), encoding="utf-8")
    run_script(exe, "exec_code.py", [str(code), str(result)], blend=blend)
    out = json.loads(result.read_text(encoding="utf-8"))
    if not out["ok"]:
        raise RuntimeError(f"{folder.name} reference failed:\n{out['output']}")
    return blend


def brief(exe, folder: Path) -> dict:
    meta = tomllib.loads((folder / "product.toml").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        blend = build(exe, folder, tmp)
        spec = tmp / "spec.json"
        spec.write_text(json.dumps({"shot": str(folder / "shot.png"), "facts": str(folder / "facts.json"),
                                    "colours": meta.get("colours", {}), "label_mm": meta.get("label_mm")}),
                        encoding="utf-8")
        proc = run_script(exe, "product_shot.py", [str(spec)], blend=blend, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(f"{folder.name} shot failed: {proc.stderr[-800:]}")
    facts = json.loads((folder / "facts.json").read_text(encoding="utf-8"))
    missing = set(meta["objects"]) - set(facts["objects"])
    leaks = {n: f["open_edges"] for n, f in facts["objects"].items() if f["open_edges"]}
    if missing or leaks:
        raise RuntimeError(f"{folder.name}: missing {missing}, open edges {leaks}")
    return facts


def main(argv: list[str]) -> int:
    exe = blender_path()
    folders = sorted(d for d in PRODUCTS.iterdir() if d.is_dir() and not d.name.startswith("_"))
    if argv:
        folders = [d for d in folders if any(d.name.startswith(p) for p in argv)]
    for d in folders:
        f = brief(exe, d)
        vols = ", ".join(f"{n} {o['volume_ml']} mL" for n, o in f["objects"].items())
        print(f"{d.name}: {f['overall_mm']}  {vols}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
