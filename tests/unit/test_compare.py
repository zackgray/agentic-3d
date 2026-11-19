"""rig.compare: the geometric means and ratios behind the headline numbers, and which runs count."""
import json
import math

import pytest

from rig import compare
from rig.compare import gmean, summarise


def run(task, tokens, verdict="pass", wall=10.0, turns=4, cost=0.01, **extra):
    r = {"task": task, "verdict": verdict, "metrics": {"total_tokens": tokens, "wall_seconds": wall,
                                                       "turns": turns, "cost_usd": cost}}
    r.update(extra)
    return r


def test_gmean():
    assert gmean([4, 9]) == pytest.approx(6)
    assert gmean([2, 8, 4]) == pytest.approx(4)
    assert gmean([7]) == pytest.approx(7)


def test_gmean_rejects_zero():
    with pytest.raises(ValueError):
        gmean([0, 10])


def test_summarise_is_a_gmean_of_per_task_gmeans():
    rs = [run("a", 100), run("a", 400), run("b", 1000, verdict="fail")]
    st = summarise(rs)
    assert st["runs"] == 3 and st["passes"] == 2
    assert st["pass_rate"] == pytest.approx(2 / 3)
    assert st["tokens_per_pass"] == pytest.approx(750)  # all tokens, failed runs included, over passes
    assert st["task_gmeans"] == pytest.approx({"a": 200, "b": 1000})
    # each task weighs once however many repeats it has
    assert st["gmean_tokens"] == pytest.approx(math.sqrt(200 * 1000))


def test_summarise_no_passes_is_infinite_tokens_per_pass():
    assert summarise([run("a", 100, verdict="fail")])["tokens_per_pass"] == float("inf")


def test_summarise_cost_treats_unknown_as_zero():
    st = summarise([run("a", 1, cost=0.5), run("a", 1, cost=None)])
    assert st["cost"] == pytest.approx(0.5)


def test_summarise_means():
    st = summarise([run("a", 1, wall=10, turns=2), run("b", 1, wall=20, turns=6)])
    assert st["wall"] == pytest.approx(15) and st["turns"] == pytest.approx(4)


def test_ratio_to_reference():
    ref = summarise([run("a", 100), run("b", 400)])
    new = summarise([run("a", 50), run("b", 200)])
    assert new["gmean_tokens"] / ref["gmean_tokens"] == pytest.approx(0.5)


class Args:
    setups = ["no-mcp", "harness"]
    version = ["harness=h7"]
    model, effort, arm = "claude-haiku-5-5", "low", "base"


def write_runs(root, records):
    for i, r in enumerate(records):
        d = root / "runs" / f"r{i}"
        d.mkdir(parents=True)
        (d / "result.json").write_text(json.dumps(r), encoding="utf-8")


def test_load_runs_filters(tmp_path, monkeypatch):
    monkeypatch.setattr(compare, "ROOT", tmp_path)
    base = dict(model="claude-haiku-5-5", effort="low", prompt_sha="s1")
    write_runs(tmp_path, [
        run("t1", 1, setup="no-mcp", versions={}, **base),                                   # counts
        run("t1", 2, setup="harness", versions={"setup": "harness h7"}, **base),             # counts
        run("t1", 3, setup="harness", versions={"setup": "harness h6"}, **base),             # old version
        run("t1", 4, setup="no-mcp", verdict="void", versions={}, **base),                   # void
        run("t1", 5, setup="no-mcp", versions={}, **{**base, "prompt_sha": "old"}),          # stale prompt
        run("t1", 6, setup="no-mcp", versions={}, **{**base, "prompt_sha": None}),           # no sha
        run("t1", 7, setup="no-mcp", versions={}, **{**base, "effort": "high"}),             # other effort
        run("t1", 8, setup="no-mcp", versions={}, arm="think-off", **base),                  # other arm
        run("t1", 9, setup="meshwire", versions={}, **base),                                  # not asked for
    ])
    runs = compare.load_runs(Args(), {"t1": "s1"})
    assert sorted(r["metrics"]["total_tokens"] for r in runs["no-mcp"]) == [1]
    assert sorted(r["metrics"]["total_tokens"] for r in runs["harness"]) == [2]
    assert "meshwire" not in runs
