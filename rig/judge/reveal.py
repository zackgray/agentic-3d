"""After grading: join a grades file to key.json, write scores.csv and summary.md (mean and n per arm,
and per product x arm). Ungraded items are listed in the CSV with no score and left out of the means."""
import csv
import json
from pathlib import Path

from . import ARM_DIR, FORMAT, SCORES, judge_dir, site_dir

COLUMNS = ("id", "product", "arm", "rep", "run", "score", "note")


class RevealError(ValueError):
    pass


def newest_grades(site: Path) -> Path:
    """The newest grades file beside the page; names carry a timestamp, so the name breaks mtime ties."""
    files = sorted(Path(site).glob("grades-*.json"), key=lambda p: (p.stat().st_mtime, p.name))
    if not files:
        raise RevealError("no grades file in %s: save from the page first (E)" % site)
    return files[-1]


def join(key: dict, export: dict) -> list[dict]:
    if export.get("format") != FORMAT:
        raise RevealError("not a grades file from this page")
    if export.get("buildId") != key["build_id"]:
        raise RevealError("the grades file is from a different build of the page than this key")
    grades = export.get("grades") or {}
    out = []
    for oid in key["order"]:
        info, g = key["items"][oid], grades.get(oid) or {}
        score = g.get("v") if g.get("v") in SCORES else None
        out.append({"id": oid, "product": info["product"], "arm": info["arm"], "rep": info["rep"],
                    "run": info.get("run") or "", "score": score, "note": (g.get("note") or "").strip()})
    return out


def summarise(rows: list[dict]) -> dict:
    """{"arm": {arm: (mean, n)}, "product_arm": {(product, arm): (mean, n)}} over graded rows only."""
    def agg(keyf):
        groups = {}
        for r in rows:
            if r["score"] is not None:
                groups.setdefault(keyf(r), []).append(r["score"])
        return {k: (round(sum(v) / len(v), 2), len(v)) for k, v in sorted(groups.items())}
    return {"arm": agg(lambda r: r["arm"]), "product_arm": agg(lambda r: (r["product"], r["arm"]))}


def markdown(summary: dict, rows: list[dict], source: str) -> str:
    graded = sum(1 for r in rows if r["score"] is not None)
    lines = ["# Shape scores, revealed", "",
             "Grades file: %s. Graded %d of %d items; ungraded items are left out of the means." % (source, graded, len(rows)),
             "", "## Per arm", "", "| Arm | Mean | n |", "|---|---|---|"]
    lines += ["| %s | %.2f | %d |" % (arm, m, n) for arm, (m, n) in summary["arm"].items()]
    lines += ["", "## Per product and arm", "", "| Product | Arm | Mean | n |", "|---|---|---|---|"]
    lines += ["| %s | %s | %.2f | %d |" % (p, a, m, n) for (p, a), (m, n) in summary["product_arm"].items()]
    return "\n".join(lines) + "\n"


def reveal(arm_dir: Path = ARM_DIR, grades: Path | None = None) -> dict:
    jd = judge_dir(arm_dir)
    key = json.loads((jd / "key.json").read_text(encoding="utf-8"))
    grades = Path(grades) if grades else newest_grades(site_dir(arm_dir))
    rows = join(key, json.loads(grades.read_text(encoding="utf-8")))
    with open(jd / "scores.csv", "w", encoding="utf-8", newline="") as handle:
        w = csv.DictWriter(handle, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows({k: ("" if r[k] is None else r[k]) for k in COLUMNS} for r in rows)
    summary = summarise(rows)
    text = markdown(summary, rows, grades.name)
    (jd / "summary.md").write_text(text, encoding="utf-8", newline="\n")
    return {"grades": str(grades), "scores": str(jd / "scores.csv"), "summary": str(jd / "summary.md"), "text": text}
