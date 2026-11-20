"""rig.openai_compat: Anthropic-shaped conversations translate to OpenAI-style requests and back."""
import pytest

from rig.accounting import Ledger
from rig.openai_compat import AdapterError, Block, from_openai, to_openai


def test_conversation_round_trip():
    history = [
        {"role": "user", "content": "Model a box."},
        {"role": "assistant", "content": [
            Block("thinking", thinking="plan", raw={"reasoning_details": [{"type": "x"}]}),
            Block("text", text="Building."),
            Block("tool_use", id="c1", name="blender", input={"code": "box()", "done": True})]},
        {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "ok",
                                      "is_error": False}]},
    ]
    out = to_openai("SYS", history)
    assert out[0] == {"role": "system", "content": "SYS"}
    assert out[1] == {"role": "user", "content": "Model a box."}
    a = out[2]
    assert a["content"] == "Building." and a["reasoning_details"] == [{"type": "x"}]
    assert a["tool_calls"][0]["function"] == {"name": "blender", "arguments": '{"code": "box()", "done": true}'}
    assert out[3] == {"role": "tool", "tool_call_id": "c1", "content": "ok"}


def test_response_with_tool_call_and_usage():
    data = {"provider": "OpenAI", "choices": [{"finish_reason": "tool_calls", "message": {
        "content": None, "reasoning": "think",
        "tool_calls": [{"id": "t1", "type": "function",
                        "function": {"name": "blender", "arguments": '{"code": "x", "done": false}'}}]}}],
        "usage": {"prompt_tokens": 1000, "completion_tokens": 300, "cost": 0.0042,
                  "prompt_tokens_details": {"cached_tokens": 600},
                  "completion_tokens_details": {"reasoning_tokens": 200}}}
    r = from_openai(data, local=False)
    assert r.stop_reason == "tool_use"
    assert [b.type for b in r.content] == ["thinking", "tool_use"]
    assert r.content[1].input == {"code": "x", "done": False}
    assert (r.usage.input_tokens, r.usage.cache_read_input_tokens, r.usage.output_tokens) == (400, 600, 300)
    row = Ledger("gpt-6.2-sol-pro").turn(r.usage, 0, 5, 1.0, r.stop_reason)
    assert row["cost_usd"] == 0.0042 and row["output_by_source"]["thinking"] == 200
    assert row["input_total"] == 1000


def test_local_costs_nothing_and_stop_reasons():
    r = from_openai({"choices": [{"finish_reason": "length", "message": {"content": "partial"}}],
                     "usage": {"prompt_tokens": 10, "completion_tokens": 5}}, local=True)
    assert r.stop_reason == "max_tokens" and r.usage.cost_usd == 0.0
    r = from_openai({"choices": [{"finish_reason": "stop", "message": {"content": "done"}}], "usage": {}}, local=True)
    assert r.stop_reason == "end_turn"


def test_malformed_arguments_reach_the_setup_as_bad_input():
    r = from_openai({"choices": [{"finish_reason": "tool_calls", "message": {"tool_calls": [
        {"id": "t", "function": {"name": "blender", "arguments": "{not json"}}]}}]}, local=True)
    assert r.content[0].input == {"_unparsed": "{not json"}


def test_provider_error_is_void():
    with pytest.raises(AdapterError):
        from_openai({"error": {"message": "no endpoints"}}, local=False)
