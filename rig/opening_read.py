"""Prints the harness's opening read for every task that starts from a scripted scene, with its token
count. Free: Blender locally, plus the count_tokens endpoint. For checking a change to the read on
every starting scene (development and all held-out sets) before any paid run.

    python -m rig.opening_read [--only r04,x07] [--no-count] [--out runs/_reads/h7.txt]
"""
import argparse
import sys
from pathlib import Path

from .blender import blender_path, make_starting_scene
from .setups.harness import HarnessSetup
from .task import load_task

ROOT = Path(__file__).resolve().parent.parent
SUITES = ("tasks", "heldout", "heldout2", "heldout3", "heldout4")


def scripted_tasks():
    for suite in SUITES:
        for toml in sorted((ROOT / suite).glob("*/task.toml")):
            task = load_task(toml)
            if task.starting_scene != "empty":
                yield task


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="comma-separated task id prefixes, e.g. r04,x07")
    p.add_argument("--no-count", action="store_true", help="skip the token count (no API call)")
    p.add_argument("--out", help="also write the reads to this file")
    args = p.parse_args(argv)
    only = tuple(args.only.split(",")) if args.only else None
    counter = None
    if not args.no_count:
        import anthropic
        from .accounting import Counter
        from .env import load_env
        load_env(ROOT / ".env")
        counter = Counter(anthropic.Anthropic(), "claude-haiku-5-5")
    exe, chunks, total = blender_path(), [], 0
    for task in scripted_tasks():
        if only and not task.id.startswith(only):
            continue
        work = ROOT / "runs" / "_reads" / task.id
        work.mkdir(parents=True, exist_ok=True)
        scene = work / "scene.blend"
        make_starting_scene(exe, task.starting_scene, scene, task.folder)
        setup = HarnessSetup(exe)
        setup.start(work, scene)
        try:
            text = setup.initial_context()
        finally:
            setup.stop()
        n = counter.text(text) if counter else 0
        total += n
        chunks.append(f"=== {task.id}  ({n} tokens)\n{text}\n")
        print(chunks[-1], flush=True)
    print(f"total {total} tokens over {len(chunks)} reads")
    if args.out:
        Path(args.out).write_text("\n".join(chunks) + f"\ntotal {total} tokens\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
