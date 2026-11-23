"""Blind judging page for the arm builds: compose each build's four views, shuffle behind opaque IDs,
grade shape 1 to 5 on a local page, then join the grades to the key (python -m rig.judge build|serve|reveal)."""
from pathlib import Path

FORMAT = "agentic-3d-grades-1"
SCORES = (1, 2, 3, 4, 5)
VIEWS = ("front", "side", "three_quarter", "top")  # composite order: front, side / three_quarter, top

ROOT = Path(__file__).resolve().parents[2]
ARM_DIR = ROOT / "runs" / "_arm"
PRODUCTS = ROOT / "products"


def judge_dir(arm_dir: Path) -> Path:
    """Holds key.json, scores.csv and summary.md; the served page is its site/ subfolder."""
    return Path(arm_dir) / "judge"


def site_dir(arm_dir: Path) -> Path:
    return judge_dir(arm_dir) / "site"
