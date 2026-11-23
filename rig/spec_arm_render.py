"""Review renders for the scored spec-first arm's judging page (rig/judge): each scored build's four
views into runs/_arm/<product>/<arm>-r<rep>/build/, and each product's reference into
runs/_arm/<product>/reference/. Free (no model calls); skips folders already rendered.

    python -m rig.spec_arm_render
"""
import json
import sys
import tempfile
from pathlib import Path

from .blender import blender_path, run_script
from .product_briefs import build as build_reference
from .spec_arm import ARM_DIR, RESULTS
from .spec_arm_report import rows
from .spec_session import PRODUCTS, ROOT


def render(exe: Path, blend: Path, out: Path) -> None:
    if (out / "top.png").is_file():
        return
    proc = run_script(exe, "review_render.py", [str(out)], blend=blend, timeout=300)
    if proc.returncode != 0:
        print(f"render failed for {out}: {proc.stderr[-500:]}")


def main() -> int:
    exe = blender_path()
    data = rows(RESULTS)
    for product in sorted({r["product"] for r in data}):
        ref = ARM_DIR / product / "reference"
        if not (ref / "top.png").is_file():
            with tempfile.TemporaryDirectory() as t:
                render(exe, build_reference(exe, PRODUCTS / product, Path(t)), ref)
    for r in data:
        render(exe, ROOT / "runs" / r["run"] / "scene.blend", ARM_DIR / r["product"] / f"{r['arm']}-r{r['rep']}" / "build")
    print(f"rendered {len(data)} builds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
