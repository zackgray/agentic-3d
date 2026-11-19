"""Geometry checks. Runs inside headless Blender:

    blender -b scene.blend --factory-startup --python checks.py -- spec.json result.json

spec.json is the task's [[checks]] list. Writes {"passed": bool, "checks": [...]}.
All lengths are metres in world space, measured on the evaluated mesh (modifiers applied).
Check types live in checks_core (structure), checks_thread and checks_shape (measurement).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import checks_core  # noqa: E402
import checks_shape  # noqa: E402
import checks_thread  # noqa: E402
from check_scene import Scene  # noqa: E402

CHECKS = {
    k[len("check_"):]: v
    for mod in (checks_core, checks_thread, checks_shape)
    for k, v in vars(mod).items() if k.startswith("check_")
}


def required_objects(c):
    names = [c[k] for k in ("object", "a", "b") if k in c] + list(c.get("objects", []))
    return names if c["type"] != "objects" else []


def main():
    spec_path, result_path = sys.argv[sys.argv.index("--") + 1:][:2]
    with open(spec_path, encoding="utf-8") as f:
        specs = json.load(f)
    s = Scene()
    results = []
    for c in specs:
        label = c.get("label", c["type"])
        if c["type"] not in CHECKS:
            raise ValueError(f"unknown check type {c['type']!r}")
        missing = [n for n in required_objects(c) if s.obj(n) is None]
        if missing:
            results.append({"check": label, "passed": False, "detail": {"missing_objects": missing}})
            continue
        ok, detail = CHECKS[c["type"]](s, c)
        results.append({"check": label, "passed": bool(ok), "detail": detail})
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({"passed": all(r["passed"] for r in results), "checks": results}, f, indent=2)


main()
