"""python -m rig.judge build | serve | reveal   (defaults read runs/_arm and products/ in this repo)"""
import argparse
import json
import sys
from pathlib import Path

from . import ARM_DIR, PRODUCTS, site_dir


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m rig.judge")
    p.add_argument("--arm-dir", type=Path, default=ARM_DIR, help="folder holding results.jsonl and the renders")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="compose, strip and shuffle the builds into the blind page and its key")
    b.add_argument("--products", type=Path, default=PRODUCTS)
    b.add_argument("--seed", type=int, help="shuffle seed (default: the existing key's, else random)")
    s = sub.add_parser("serve", help="serve the page on 127.0.0.1")
    s.add_argument("--port", type=int, help="default: the first free port from 8741")
    r = sub.add_parser("reveal", help="join a grades file to the key; write scores.csv and summary.md")
    r.add_argument("--grades", type=Path, help="default: the newest grades file beside the page")
    a = p.parse_args(argv)
    if a.cmd == "build":
        from .build import build
        info = build(a.arm_dir, a.products, a.seed)
        print(json.dumps(info, indent=1))
        print("Do not open key.json until your grades are in.")
    elif a.cmd == "serve":
        from .serve import serve
        serve(site_dir(a.arm_dir), a.port)
    else:
        from .reveal import reveal
        info = reveal(a.arm_dir, a.grades)
        print(info.pop("text"))
        print(json.dumps(info, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
