"""rig.accounting: cost arithmetic and the split of each turn's tokens by source."""
from types import SimpleNamespace

import pytest

from rig.accounting import CACHE_WRITE, PRICES, Counter, Ledger


def usage(inp=0, out=0, write=0, read=0, thinking=None):
    details = SimpleNamespace(thinking_tokens=thinking) if thinking is not None else None
    return SimpleNamespace(input_tokens=inp, output_tokens=out, cache_creation_input_tokens=write,
                           cache_read_input_tokens=read, output_tokens_details=details)


def test_cost_matches_list_price():
    pin, pout, pread = PRICES["claude-haiku-5-5"]
    row = Ledger("claude-haiku-5-5").turn(usage(1000, 500, write=2000, read=10_000), 0, 0, 1.0, "end_turn")
    want = (1000 + 2000 * CACHE_WRITE) * pin / 1e6 + 10_000 * pread / 1e6 + 500 * pout / 1e6
    assert row["cost_usd"] == pytest.approx(want, abs=1e-6)


def test_cost_one_million_each():
    led = Ledger("claude-sonnet-5-5")
    pin, pout, pread = PRICES["claude-sonnet-5-5"]
    assert led._cost(1_000_000, 0, 0, 1_000_000) == pytest.approx(pin + pout)
    assert led._cost(0, 1_000_000, 0, 0) == pytest.approx(pin * CACHE_WRITE)
    assert led._cost(0, 0, 1_000_000, 0) == pytest.approx(0.10)  # Sonnet 5.5 cache reads are $0.10, not 0.1x input


def test_unknown_model_has_no_cost():
    led = Ledger("some-other-model")
    led.turn(usage(10, 10), 0, 0, 0.1, "end_turn")
    assert led.turns[0]["cost_usd"] is None
    assert led.summary()["cost_usd"] is None


def test_input_split_and_unattributed():
    led = Ledger("claude-haiku-5-5")
    led.add("system", 300)
    led.add("tool_definitions", 200)
    led.add("images", 0)  # zero sources are left out of the split
    row = led.turn(usage(100, 50, write=400, read=50), 0, 0, 0.5, "tool_use")
    assert row["input_total"] == 550
    assert row["input_by_source"] == {"system": 300, "tool_definitions": 200}
    assert row["input_unattributed"] == 50


def test_output_split_reported_thinking():
    row = Ledger("claude-haiku-5-5").turn(usage(1, 100, thinking=60), text_out=15, code_out=20,
                                          seconds=0, stop_reason="end_turn")
    assert row["output_by_source"] == {"thinking": 60, "agent_code": 20, "agent_text": 15, "unattributed": 5}


def test_output_split_inferred_thinking():
    row = Ledger("claude-haiku-5-5").turn(usage(1, 100), text_out=15, code_out=20, seconds=0, stop_reason="end_turn")
    assert row["output_by_source"]["thinking"] == 65
    assert row["output_by_source"]["unattributed"] == 0


def test_cleared_thinking_is_not_attributed():
    led = Ledger("claude-haiku-5-5")
    led.add("thinking_replay", 500)
    row = led.turn(usage(1000), 0, 0, 0, "tool_use", cleared_thinking=300)
    assert row["input_by_source"]["thinking_replay"] == 200
    assert led.context["thinking_replay"] == 500  # the running ledger itself is unchanged
    row = led.turn(usage(1000), 0, 0, 0, "tool_use", cleared_thinking=900)
    assert row["input_by_source"]["thinking_replay"] == 0


def test_summary_totals():
    led = Ledger("claude-haiku-5-5")
    led.add("system", 10)
    led.turn(usage(100, 40, read=20), 0, 0, 1.25, "tool_use")
    led.turn(usage(200, 60, write=10), 0, 0, 2.0, "end_turn")
    led.tool_call("blender", False, 0.5, 30)
    led.tool_call("blender", True, 1.0, 10)
    s = led.summary()
    assert s["turns"] == 2
    assert (s["input_tokens"], s["output_tokens"], s["total_tokens"]) == (330, 100, 430)
    assert s["cache_read_tokens"] == 20
    assert s["input_by_source"] == {"system": 20, "unattributed": 310}
    assert s["tool_calls"] == 2 and s["failed_tool_calls"] == 1
    assert s["model_seconds"] == pytest.approx(3.2) and s["tool_seconds"] == pytest.approx(1.5)
    assert s["cost_usd"] == pytest.approx(sum(r["cost_usd"] for r in led.turns), abs=1e-5)


class FakeClient:
    """count_tokens stand-in: 5 tokens of framing plus one per character; counts its calls."""

    def __init__(self):
        self.calls = 0
        self.messages = self

    def count_tokens(self, model, messages, system="", tools=()):
        self.calls += 1
        content = messages[0]["content"]
        n = len(content) if isinstance(content, str) else sum(len(b["text"]) if b["type"] == "text" else 100 for b in content)
        return SimpleNamespace(input_tokens=5 + n + len(system) + 10 * len(tools))


def test_counter_subtracts_framing_and_caches():
    client = FakeClient()
    c = Counter(client, "claude-haiku-5-5")
    assert c.base == 6
    assert c.text("") == 0
    assert c.text("hello") == 5
    calls = client.calls
    assert c.text("hello") == 5 and client.calls == calls
    assert c.system("abc") == 3
    assert c.tools([{}, {}]) == 20
    assert c.image("image/png", "xyz") == 100
