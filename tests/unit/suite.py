"""Shared fixtures for the unit tests. Nothing here needs Blender or the network."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITES = ("tasks", "heldout", "heldout2", "heldout3", "heldout4")


def task_folders():
    """Every task folder in every suite, the way rig.compare and rig.batch list them."""
    return [d for s in SUITES for d in sorted((ROOT / s).iterdir()) if d.is_dir() and not d.name.startswith("_")]
