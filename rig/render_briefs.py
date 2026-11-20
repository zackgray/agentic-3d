"""Renders the reference views the "views" prompt arm attaches to a build task's brief. Free (no model
calls); the PNGs are committed so every run sees the same bytes.

    python -m rig.render_briefs              # every non-revision task in tasks/
    python -m rig.render_briefs p01 h02      # a subset, by prefix

Each task's reference model ("good" variant) is rendered by the review renderer: front, side and top
orthographic, plus a three-quarter view, 480 px, one flat colour per object. Revision tasks are skipped:
they already start from a model, and a view of the finished edit would hand over the answer's shape.
The views come from the exact model the checks grade, so this arm is an upper bound on what a picture
can add.
"""
import shutil
import sys
import tempfile
from pathlib import Path

from .blender import blender_path, run_script
from .task import BRIEF_VIEWS, load_task
from .verify_checks import build

ROOT = Path(__file__).resolve().parent.parent


def render_task(exe, folder: Path) -> Path:
    task = load_task(folder)
    out = folder / "brief"
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        blend = build(exe, task, "good", tmp)
        proc = run_script(exe, "review_render.py", [str(tmp / "views")], blend=blend, timeout=300)
        if proc.returncode != 0:
            raise RuntimeError(f"render failed for {folder.name}: {proc.stderr[-800:]}")
        out.mkdir(exist_ok=True)
        for v in BRIEF_VIEWS:
            shutil.copyfile(tmp / "views" / f"{v}.png", out / f"{v}.png")
    return out


def main(argv: list[str]) -> int:
    exe = blender_path()
    folders = sorted(d for d in (ROOT / "tasks").iterdir() if d.is_dir() and not d.name.startswith("_"))
    folders = [d for d in folders if load_task(d).starting_scene == "empty" or not d.name.startswith("r")]
    if argv:
        folders = [d for d in folders if any(d.name.startswith(p) for p in argv)]
    for d in folders:
        print("rendered", render_task(exe, d).relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
