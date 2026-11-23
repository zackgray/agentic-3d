"""Which builds are judged: the latest non-void row per (product, arm, rep) in results.jsonl, the same
rule as rig/spec_arm_report.py, and only where all four rendered views exist."""
import json
from pathlib import Path

from .compose import missing_views


def rows(results: Path) -> list[dict]:
    best = {}
    for line in Path(results).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("verdict") != "void":
                best[(r["product"], r["arm"], r["rep"])] = r
    return [best[k] for k in sorted(best, key=lambda k: (k[0], k[1], int(k[2])))]


def build_folder(arm_dir: Path, row: dict) -> Path:
    return Path(arm_dir) / row["product"] / ("%s-r%s" % (row["arm"], row["rep"])) / "build"


def collect(arm_dir: Path) -> tuple[list[dict], list[dict]]:
    """(items ready to judge, skipped items with the reason). Each item keeps its render folder."""
    ready, skipped = [], []
    for row in rows(Path(arm_dir) / "results.jsonl"):
        folder = build_folder(arm_dir, row)
        item = {"product": row["product"], "arm": row["arm"], "rep": row["rep"], "run": row.get("run"),
                "folder": folder}
        gone = missing_views(folder)
        if gone:
            skipped.append(dict(item, folder=str(folder), reason="missing " + ", ".join(gone)))
        else:
            ready.append(item)
    return ready, skipped
