"""rig.batch: task prefixes resolve to exactly one folder, and resumed batches count only scored runs."""
import json

import pytest

from rig import batch
from rig.batch import resolve_tasks


@pytest.fixture
def folders(tmp_path):
    names = ["h01-cosmetic-compact", "h02-lipstick", "p01-threaded-bottle", "r01-cap-taller", "r10-new"]
    out = []
    for n in names:
        (tmp_path / n).mkdir()
        out.append(tmp_path / n)
    return out


def test_prefix_resolves_in_given_order(folders):
    got = resolve_tasks(folders, ["p01", "h02-lip", "h01-cosmetic-compact"])
    assert [g.name for g in got] == ["p01-threaded-bottle", "h02-lipstick", "h01-cosmetic-compact"]


@pytest.mark.parametrize("prefix", ["h0", "x01", "r", "lipstick"])
def test_ambiguous_missing_or_non_prefix_stops(folders, prefix):
    with pytest.raises(SystemExit):
        resolve_tasks(folders, [prefix])


def test_short_prefixes_that_are_unique_resolve(folders):
    assert [g.name for g in resolve_tasks(folders, ["r0", "r1"])] == ["r01-cap-taller", "r10-new"]


def test_done_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(batch, "ROOT", tmp_path)
    recs = [
        dict(task="t1", setup="harness", verdict="pass", prompt_sha="s1"),
        dict(task="t1", setup="harness", verdict="fail", prompt_sha="s1"),
        dict(task="t1", setup="harness", verdict="void", prompt_sha="s1"),
        dict(task="t1", setup="harness", verdict="pass", prompt_sha="old"),
        dict(task="t1", setup="harness", verdict="pass", prompt_sha="s1", arm="think-off"),
        dict(task="t1", setup="no-mcp", verdict="pass", prompt_sha="s1", effort="high"),
    ]
    for i, r in enumerate(recs):
        d = tmp_path / "runs" / f"r{i}"
        d.mkdir(parents=True)
        r.setdefault("model", "claude-haiku-5-5")
        r.setdefault("effort", "low")
        (d / "result.json").write_text(json.dumps(r), encoding="utf-8")
    c = batch.done_counts("claude-haiku-5-5", "low", "base", {"t1": "s1"})
    assert c[("t1", "harness")] == 2
    assert c[("t1", "no-mcp")] == 0
