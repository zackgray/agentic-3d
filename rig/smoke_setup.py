"""Brings a setup up and down without any model calls, to prove it before spending. Free.

    python -m rig.smoke_setup blender-lab [--call tool_name '{"arg": 1}']

Starts the setup on an empty scene (or a task's starting scene with --task), prints its tool count, the token size of its tool definitions
and instructions is left to the real run (counting needs the API), makes one optional call, saves
the scene through the rig's control channel, checks the saved file exists, and shuts down.
"""
import argparse
import json
import sys
import shutil
import time
from pathlib import Path

from .blender import blender_path, make_starting_scene
from .run import SETUPS
from .task import load_task


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("setup", choices=sorted(SETUPS))
    p.add_argument("--call", nargs=2, metavar=("TOOL", "JSON"))
    p.add_argument("--task", help="start on this task's starting scene instead of the empty one")
    args = p.parse_args(argv)
    exe = blender_path()
    work = Path(__file__).resolve().parent.parent / "runs" / "_smoke" / args.setup
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    if True:
        scene = work / "scene.blend"
        if args.task:
            task = load_task(args.task)
            make_starting_scene(exe, task.starting_scene, scene, task.folder)
        else:
            make_starting_scene(exe, "empty", scene)
        before = scene.stat().st_mtime
        setup = SETUPS[args.setup](exe)
        t0 = time.monotonic()
        setup.start(work, scene)
        print(f"{setup.name} {setup.version}: up in {time.monotonic() - t0:.1f} s, {len(setup.tools)} tools, "
              f"system prompt {len(setup.system)} chars, tool definitions {len(json.dumps(setup.tools))} chars")
        try:
            if args.call:
                out = setup.call(args.call[0], json.loads(args.call[1]))
                print(f"call {args.call[0]}: error={out.is_error} {out.seconds:.1f} s images={len(out.images if hasattr(out, 'images') else [])}")
                print("  " + out.text[:600].replace("\n", "\n  "))
        finally:
            setup.stop()
        saved = scene.stat().st_mtime > before
        print(f"final scene saved: {saved}")
        return 0 if saved else 1


if __name__ == "__main__":
    sys.exit(main())
