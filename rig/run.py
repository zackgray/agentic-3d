"""Runs one task on one setup and records pass / fail / void.

    python -m rig.run tasks/p01-threaded-bottle --setup no-mcp --model claude-haiku-5-5 --effort low

Void means the rig or environment broke (Blender missing, API unreachable, a check crashed), so the
run says nothing about the agent. Records go to runs/<run id>/ (git-ignored).
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from .accounting import Counter, Ledger
from .agent_loop import run_agent
from .env import load_env
from .blender import SetupError, blender_path, blender_version, make_starting_scene, run_checks
from .prompt_arms import ARMS, REQUEST, apply
from .setups.harness import HarnessSetup
from .setups.mcp_servers import MCP_SETUPS
from .setups.no_mcp import NoMcpSetup
from .task import load_task

ROOT = Path(__file__).resolve().parent.parent
SETUPS = {"no-mcp": NoMcpSetup, "harness": HarnessSetup, **MCP_SETUPS}


def rig_version() -> str:
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except OSError:
        return "unknown"


def prompt_sha(prompt: str, arm: str, scene_text: str = "") -> str:
    """Identifies the exact prompt (and scripted starting scene) a run saw, so an edit to either never
    mixes with older runs. With the empty scene it hashes the prompt alone, as before."""
    return hashlib.sha256((apply(prompt, arm) + scene_text).encode("utf-8")).hexdigest()[:12]


def execute(args, rec: dict, run_dir: Path, transcript: list) -> None:
    exe = blender_path(args.blender)
    rec["versions"]["blender"] = blender_version(exe)
    task = load_task(args.task)
    rec["prompt_sha"] = prompt_sha(task.prompt, args.arm, task.scene_text)
    client = anthropic.Anthropic(max_retries=4)
    try:
        counter = Counter(client, args.model)  # first API call: bad key or no network fails here, as void
    except TypeError as e:  # the SDK raises TypeError when it finds no credentials at all
        raise SetupError(f"no Anthropic credentials: {e}") from e
    ledger = Ledger(args.model)
    scene = run_dir / "scene.blend"
    make_starting_scene(exe, task.starting_scene, scene, task.folder)
    setup = SETUPS[args.setup](exe)
    rec["versions"]["setup"] = f"{setup.name} {setup.version}"
    setup.start(run_dir, scene)
    t0 = time.monotonic()
    try:
        rec["agent"] = run_agent(client, args.model, args.effort, setup, apply(task.prompt, args.arm), counter, ledger,
                                 transcript, max_turns=args.max_turns,
                                 request=REQUEST.get(args.arm))
    finally:
        setup.stop()
        rec["metrics"] = ledger.summary()
        rec["metrics"]["wall_seconds"] = round(time.monotonic() - t0, 1)
        rec["turns"] = ledger.turns
        rec["tool_calls"] = ledger.tool_calls
    rec["checks"] = run_checks(exe, scene, task.checks)
    rec["verdict"] = "pass" if rec["checks"]["passed"] else "fail"


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("task")
    p.add_argument("--setup", default="no-mcp", choices=sorted(SETUPS))
    p.add_argument("--arm", default="base", choices=sorted(ARMS), help="prompt arm (rig/prompt_arms.py)")
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--effort", default="low")
    p.add_argument("--max-turns", type=int, default=40)
    p.add_argument("--blender", help="override the Blender executable (a wrong path must give void)")
    args = p.parse_args(argv)
    load_env(ROOT / ".env")

    started = datetime.now(timezone.utc)
    task_id = Path(args.task).resolve().name
    run_id = f"{started:%Y%m%d-%H%M%S}_{task_id}_{args.setup}_{args.model}-{args.effort}"
    if args.arm != "base":
        run_id += f"_{args.arm}"
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True)
    rec = {"run_id": run_id, "task": task_id, "setup": args.setup, "model": args.model,
           "effort": args.effort, "arm": args.arm, "started": started.isoformat(), "verdict": None,
           "versions": {"rig": rig_version(), "anthropic_sdk": anthropic.__version__,
                        "python": sys.version.split()[0]}}
    transcript: list = []
    try:
        execute(args, rec, run_dir, transcript)
    except SetupError as e:
        rec["verdict"], rec["void_reason"] = "void", f"setup: {e}"
    except anthropic.AnthropicError as e:  # auth, network, rate limit, server, or a malformed request from the rig
        rec["verdict"], rec["void_reason"] = "void", f"api: {type(e).__name__}: {e}"
    except Exception as e:  # a bug in the rig is never the agent's failure
        rec["verdict"], rec["void_reason"] = "void", f"rig: {type(e).__name__}: {e}"
        rec["traceback"] = traceback.format_exc()
    rec["finished"] = datetime.now(timezone.utc).isoformat()
    (run_dir / "result.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (run_dir / "transcript.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")

    m = rec.get("metrics", {})
    print(f"{rec['verdict'].upper()}  {run_id}")
    if rec.get("void_reason"):
        print(f"  void: {rec['void_reason']}")
    if m:
        print(f"  turns {m['turns']}  tokens {m['total_tokens']} (in {m['input_tokens']}, out {m['output_tokens']})"
              f"  cost ${m['cost_usd']}  wall {m['wall_seconds']} s  failed calls {m['failed_tool_calls']}")
        print(f"  input by source  {m['input_by_source']}")
        print(f"  output by source {m['output_by_source']}")
    for c in rec.get("checks", {}).get("checks", []):
        if not c["passed"]:
            print(f"  FAIL {c['check']}: {json.dumps(c['detail'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
