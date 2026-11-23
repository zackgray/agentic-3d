"""rig.judge: shuffled opaque IDs with the key kept out of the page, metadata stripped from every image,
grades files that never overwrite, and the reveal join. Uses small fake renders in a temp folder."""
import csv
import json
from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402
from PIL.PngImagePlugin import PngInfo  # noqa: E402

from rig.judge import FORMAT, VIEWS  # noqa: E402
from rig.judge.build import BlindError, build, check_blind, opaque, shuffled  # noqa: E402
from rig.judge.reveal import RevealError, join, reveal, summarise  # noqa: E402
from rig.judge.serve import save_grades  # noqa: E402
from rig.judge.strip import text_chunks  # noqa: E402

PRODUCTS = ("halden-can-12oz", "northpeak-water-500ml")
ARMS = ("direct", "spec", "spec1")


def views(folder: Path, shade: int):
    folder.mkdir(parents=True, exist_ok=True)
    for v in VIEWS:
        info = PngInfo()
        info.add_text("File", "C:/somewhere/private/scene.blend")  # what Blender embeds
        Image.new("RGBA", (40, 40), (shade, 80, 80, 255)).save(folder / (v + ".png"), pnginfo=info)


@pytest.fixture
def arm(tmp_path):
    arm_dir, products, rows = tmp_path / "_arm", tmp_path / "products", []
    for i, p in enumerate(PRODUCTS):
        views(arm_dir / p / "reference", 200)
        (products / p).mkdir(parents=True)
        Image.new("RGB", (30, 40), "white").save(products / p / "shot.png")
        for j, a in enumerate(ARMS):
            rows.append({"product": p, "arm": a, "rep": 1, "run": "run-%s-%s" % (p, a), "verdict": "pass"})
            if (i, j) != (1, 2):  # one build has no renders: skipped, not fatal
                views(arm_dir / p / ("%s-r1" % a) / "build", 20 * (j + 1))
    rows.append({"product": PRODUCTS[0], "arm": "direct", "rep": 2, "run": "void-run", "verdict": "void"})
    (arm_dir / "results.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return arm_dir, products


def test_shuffle_is_seeded_and_ids_are_opaque():
    items = [{"product": p, "arm": a, "rep": 1, "run": "r-%s-%s" % (p, a)} for p in PRODUCTS for a in ARMS]
    assert [i["run"] for i in shuffled(items, 7)] == [i["run"] for i in shuffled(list(reversed(items)), 7)]
    ids = {opaque(7, i) for i in items}
    assert len(ids) == len(items)
    assert all(a not in oid and p not in oid for oid in ids for a in ARMS for p in PRODUCTS)
    assert opaque(7, items[0]) != opaque(8, items[0])


def test_check_blind_refuses_arm_names():
    item = {"product": "x", "arm": "spec1", "rep": 1, "run": "run-1"}
    check_blind('{"product": "x"}', [item])
    for leak in ('"spec1"', "spec1-r1", "run-1"):
        with pytest.raises(BlindError):
            check_blind(leak, [item])


def test_build_keeps_key_outside_page_and_strips_images(arm):
    arm_dir, products = arm
    info = build(arm_dir, products, seed=3)
    site, key_path = arm_dir / "judge" / "site", arm_dir / "judge" / "key.json"
    assert info["items"] == 5 and len(info["skipped"]) == 1
    assert key_path.is_file() and not list(site.rglob("key*.json"))
    key = json.loads(key_path.read_text(encoding="utf-8"))
    assert {v["run"] for v in key["items"].values()} == {"run-%s-%s" % (p, a) for p in PRODUCTS for a in ARMS} - {
        "run-%s-spec1" % PRODUCTS[1]}
    page = "".join(f.read_text(encoding="utf-8") for f in site.iterdir() if f.is_file())
    assert not any(a in page for a in ('"direct"', '"spec1"', "-r1", "run-"))
    for png in (site / "img").glob("*.png"):
        data = png.read_bytes()
        assert text_chunks(data) == [] and b"private" not in data
    data = json.loads((site / "data.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    assert [e["id"] for e in data["items"]] == key["order"]
    assert all(e["ref"] == "img/ref-%s.png" % e["product"] for e in data["items"])


def test_rebuild_keeps_ids_and_grades_files(arm):
    arm_dir, products = arm
    build(arm_dir, products)
    site = arm_dir / "judge" / "site"
    first = json.loads((arm_dir / "judge" / "key.json").read_text(encoding="utf-8"))
    (site / "grades-x-1.json").write_text("{}", encoding="utf-8")
    build(arm_dir, products)
    again = json.loads((arm_dir / "judge" / "key.json").read_text(encoding="utf-8"))
    assert again["order"] == first["order"] and again["build_id"] == first["build_id"]
    assert (site / "grades-x-1.json").is_file()


def test_save_never_overwrites(tmp_path):
    body = json.dumps({"format": FORMAT, "buildId": "abc", "grades": {}}).encode()
    names = [save_grades(tmp_path, body, stamp="T") for _ in range(3)]
    assert len(set(names)) == 3 and len(list(tmp_path.glob("grades-*.json"))) == 3
    with pytest.raises(ValueError):
        save_grades(tmp_path, b'{"format": "other", "grades": {}}')


def test_join_and_summary():
    key = {"build_id": "B", "order": ["a", "b", "c"], "items": {
        "a": {"product": "p", "arm": "direct", "rep": 1, "run": "r1"},
        "b": {"product": "p", "arm": "direct", "rep": 2, "run": "r2"},
        "c": {"product": "q", "arm": "spec", "rep": 1, "run": "r3"}}}
    export = {"format": FORMAT, "buildId": "B", "grades": {"a": {"v": 4, "note": " short neck "}, "b": {"v": 2},
                                                          "c": {"v": None, "note": "unsure"}}}
    rows = join(key, export)
    assert [r["score"] for r in rows] == [4, 2, None] and rows[0]["note"] == "short neck"
    s = summarise(rows)
    assert s["arm"] == {"direct": (3.0, 2)} and s["product_arm"] == {("p", "direct"): (3.0, 2)}
    with pytest.raises(RevealError):
        join(key, dict(export, buildId="other"))


def test_reveal_reads_newest_grades_file(arm):
    arm_dir, products = arm
    build(arm_dir, products, seed=1)
    key = json.loads((arm_dir / "judge" / "key.json").read_text(encoding="utf-8"))
    site = arm_dir / "judge" / "site"
    body = {"format": FORMAT, "buildId": key["build_id"], "grades": {oid: {"v": 3} for oid in key["order"]}}
    save_grades(site, json.dumps(body).encode(), stamp="20260101-000000")
    out = reveal(arm_dir)
    with open(out["scores"], encoding="utf-8") as handle:
        assert [r["score"] for r in csv.DictReader(handle)] == ["3"] * 5
    assert "| direct | 3.00 | 2 |" in (arm_dir / "judge" / "summary.md").read_text(encoding="utf-8")
