"""Runs the harness's opening read on recorded runs' final scenes: agent-built geometry of every
kind, to show the read never fails or stalls on a mesh it wasn't designed around. Free.

    python tests/read_stress.py [--sample 300] [--seed 1] [--out runs/_reads/stress.json]
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rig.blender import blender_path  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", type=int, default=300)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", default=str(ROOT / "runs" / "_reads" / "stress.json"))
    a = p.parse_args()
    scenes = sorted(str(s) for s in ROOT.glob("runs/**/scene.blend") if "_reads" not in s.parts)
    random.Random(a.seed).shuffle(scenes)
    scenes = scenes[:a.sample]
    with tempfile.TemporaryDirectory() as tmp:
        lst = Path(tmp) / "scenes.json"
        lst.write_text(json.dumps(scenes), encoding="utf-8")
        subprocess.run([str(blender_path()), "-b", "--factory-startup", "--python",
                        str(ROOT / "tests" / "read_stress_side.py"), "--", str(lst), a.out],
                       capture_output=True, timeout=3600)
    rows = json.loads(Path(a.out).read_text(encoding="utf-8"))
    errors = [r for r in rows if "error" in r]
    slow = sorted((r for r in rows if "seconds" in r), key=lambda r: -r["seconds"])[:5]
    print(f"{len(rows)} scenes, {len(errors)} errors")
    for r in errors[:10]:
        print(r["scene"], r["error"].strip().splitlines()[-1])
    for r in slow:
        print(f"slowest {r['seconds']:.2f} s  {r['scene']}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
