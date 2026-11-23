"""Build the blind page and its key.

    runs/_arm/judge/site/   index.html, assets, data.js, img/   the served page (grades files land here too)
    runs/_arm/judge/key.json                                   which build is which: outside the served folder
"""
import hashlib
import json
import random
import re
import secrets
import shutil
from pathlib import Path

from . import ARM_DIR, FORMAT, PRODUCTS, SCORES, judge_dir, site_dir
from .compose import composite, missing_views, write_photo, write_png
from .items import collect

ASSETS = Path(__file__).resolve().parent / "assets"
PAGE_FILES = ("index.html", "style.css", "state.js", "model.js", "view.js", "panel.js", "save.js", "keys.js", "main.js")
EXPERIMENT = "arm-shape"
TITLE = "Shape: does it look like the product in the photo?"
LABELS = {1: "wrong product", 2: "right kind but clearly off", 3: "recognisable with visible errors",
          4: "close, small differences", 5: "indistinguishable in shape"}


class BlindError(ValueError):
    pass


def opaque(seed, item) -> str:
    raw = "%s:%s:%s:%s:%s" % (seed, item["product"], item["arm"], item["rep"], item.get("run"))
    return "b" + hashlib.sha256(raw.encode()).hexdigest()[:10]


def shuffled(items, seed) -> list[dict]:
    order = sorted(items, key=lambda i: (i["product"], i["arm"], int(i["rep"])))
    random.Random(seed).shuffle(order)
    return order


def check_blind(text: str, items) -> None:
    """The page data must name no arm, rep folder or run."""
    for it in items:
        for secret in (it.get("run"), "%s-r%s" % (it["arm"], it["rep"])):
            if secret and secret in text:
                raise BlindError("page data contains the private value %r" % secret)
        if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(it["arm"]), text):
            raise BlindError("page data names the arm %r" % it["arm"])


def _fresh_site(site: Path) -> None:
    """Clear the page but keep every grades file written beside it."""
    site.mkdir(parents=True, exist_ok=True)
    for p in site.iterdir():
        if p.name.startswith("grades-") and p.suffix == ".json":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    (site / "img").mkdir()


def _references(arm_dir: Path, products: Path, names, img: Path) -> tuple[dict, list[str]]:
    refs, notes = {}, []
    for product in sorted(names):
        entry = {"ref": None, "photo": None}
        folder = arm_dir / product / "reference"
        if not missing_views(folder):
            write_png(composite(folder), img / ("ref-%s.png" % product))
            entry["ref"] = "img/ref-%s.png" % product
        else:
            notes.append("%s: no complete reference views" % product)
        shot = products / product / "shot.png"
        if shot.is_file():
            write_photo(shot, img / ("photo-%s.png" % product))
            entry["photo"] = "img/photo-%s.png" % product
        else:
            notes.append("%s: no product photo" % product)
        refs[product] = entry
    return refs, notes


def build(arm_dir: Path = ARM_DIR, products: Path = PRODUCTS, seed=None) -> dict:
    arm_dir, products = Path(arm_dir), Path(products)
    key_path = judge_dir(arm_dir) / "key.json"
    if seed is None and key_path.is_file():  # keep the order and IDs stable across rebuilds
        seed = json.loads(key_path.read_text(encoding="utf-8")).get("seed")
    seed = seed if seed is not None else secrets.randbelow(2**31)
    ready, skipped = collect(arm_dir)
    if not ready:
        raise SystemExit("nothing to judge: no item has all four views (%d skipped)" % len(skipped))
    site = site_dir(arm_dir)
    _fresh_site(site)
    for name in PAGE_FILES:
        shutil.copyfile(ASSETS / name, site / name)
    refs, notes = _references(arm_dir, products, {i["product"] for i in ready}, site / "img")

    entries, key_items = [], {}
    for it in shuffled(ready, seed):
        oid = opaque(seed, it)
        write_png(composite(it["folder"]), site / "img" / (oid + ".png"))
        entries.append({"id": oid, "product": it["product"], "image": "img/%s.png" % oid, **refs[it["product"]]})
        key_items[oid] = {k: it[k] for k in ("product", "arm", "rep", "run")}
    build_id = hashlib.sha256(json.dumps([seed, sorted(key_items)]).encode()).hexdigest()[:12]
    data = {"format": FORMAT, "experiment": EXPERIMENT, "buildId": build_id, "title": TITLE,
            "scores": [{"v": s, "label": LABELS[s]} for s in SCORES], "items": entries}
    text = "window.JUDGE = " + json.dumps(data, indent=1) + ";\n"
    check_blind(text, ready)
    (site / "data.js").write_text(text, encoding="utf-8", newline="\n")

    key = {"format": FORMAT, "experiment": EXPERIMENT, "build_id": build_id, "seed": seed,
           "order": [e["id"] for e in entries], "items": key_items, "skipped": skipped}
    key_path.write_text(json.dumps(key, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return {"page": str(site / "index.html"), "key": str(key_path), "items": len(entries),
            "skipped": [("%s %s-r%s: %s" % (s["product"], s["arm"], s["rep"], s["reason"])) for s in skipped],
            "notes": notes}
