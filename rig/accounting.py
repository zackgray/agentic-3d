"""Token accounting by source.

Every request bills input for the whole context. The ledger tracks how many tokens of each source
sit in the context, so each turn's input can be split by source. Replayed thinking is estimated from
the API's own thinking-token count for the turn that produced it; whatever the counts don't explain
(message framing, counting error) is reported as "unattributed" rather than hidden.
Block sizes come from the count_tokens endpoint (free), never a third-party tokenizer.
"""
from collections import defaultdict

# USD per million tokens, list price (Claude API skill table cached 2026-11-03). Haiku 5.5 is for prompts up to 100K.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}
CACHE_WRITE, CACHE_READ = 1.25, 0.10  # multiples of the input price (5-minute cache)

INPUT_SOURCES = ("system", "tool_definitions", "task_prompt", "agent_code", "agent_text",
                 "tool_results", "images", "thinking_replay")


class Counter:
    def __init__(self, client, model: str):
        self.client, self.model = client, model
        self._cache: dict[str, int] = {}
        self.base = self._count([{"role": "user", "content": "a"}])  # one-token message plus framing

    def _count(self, messages, **kw) -> int:
        return self.client.messages.count_tokens(model=self.model, messages=messages, **kw).input_tokens

    def text(self, s: str) -> int:
        if not s:
            return 0
        if s not in self._cache:
            self._cache[s] = self._count([{"role": "user", "content": s}]) - self.base + 1
        return self._cache[s]

    def image(self, media_type: str, data: str) -> int:
        """Tokens for one image block, counted the same way as text: the endpoint, minus framing."""
        key = f"img:{media_type}:{len(data)}:{hash(data)}"
        if key not in self._cache:
            block = {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}
            self._cache[key] = self._count([{"role": "user", "content": [block, {"type": "text", "text": "a"}]}]) - self.base
        return self._cache[key]

    def system(self, system: str) -> int:
        return self._count([{"role": "user", "content": "a"}], system=system) - self.base

    def tools(self, tools: list[dict]) -> int:
        return self._count([{"role": "user", "content": "a"}], tools=tools) - self.base


class Ledger:
    def __init__(self, model: str):
        self.price = PRICES.get(model)
        self.context: dict[str, int] = defaultdict(int)
        self.turns: list[dict] = []
        self.tool_calls: list[dict] = []

    def add(self, source: str, tokens: int) -> None:
        self.context[source] += tokens

    def turn(self, usage, text_out: int, code_out: int, seconds: float, stop_reason: str,
             cleared_thinking: int = 0) -> dict:
        write = usage.cache_creation_input_tokens or 0
        read = usage.cache_read_input_tokens or 0
        total_in = usage.input_tokens + write + read
        details = getattr(usage, "output_tokens_details", None)
        thinking = getattr(details, "thinking_tokens", None) if details else None
        if thinking is None:  # older response shape: infer
            thinking = max(0, usage.output_tokens - text_out - code_out)
        attributed = {k: v for k, v in self.context.items() if v}
        if cleared_thinking:  # this much earlier thinking wasn't resent with this request
            attributed["thinking_replay"] = max(0, attributed.get("thinking_replay", 0) - cleared_thinking)
        row = {
            "turn": len(self.turns) + 1,
            "stop_reason": stop_reason,
            "model_seconds": round(seconds, 2),
            "input_total": total_in,
            "input_uncached": usage.input_tokens,
            "cache_write": write,
            "cache_read": read,
            "input_by_source": attributed,
            "input_unattributed": total_in - sum(attributed.values()),
            "cleared_thinking": cleared_thinking,
            "output_total": usage.output_tokens,
            "output_by_source": {"thinking": thinking, "agent_code": code_out, "agent_text": text_out,
                                 "unattributed": usage.output_tokens - thinking - code_out - text_out},
            "cost_usd": self._cost(usage.input_tokens, write, read, usage.output_tokens),
        }
        self.turns.append(row)
        return row

    def tool_call(self, name: str, is_error: bool, seconds: float, result_tokens: int) -> None:
        self.tool_calls.append({"tool": name, "is_error": is_error, "seconds": round(seconds, 2),
                                "result_tokens": result_tokens})

    def _cost(self, fresh, write, read, out) -> float | None:
        if not self.price:
            return None
        pin, pout = self.price
        return round((fresh + write * CACHE_WRITE + read * CACHE_READ) * pin / 1e6 + out * pout / 1e6, 6)

    def summary(self) -> dict:
        t = self.turns
        by_in: dict[str, int] = defaultdict(int)
        by_out: dict[str, int] = defaultdict(int)
        for row in t:
            for k, v in row["input_by_source"].items():
                by_in[k] += v
            by_in["unattributed"] += row["input_unattributed"]
            for k, v in row["output_by_source"].items():
                by_out[k] += v
        costs = [r["cost_usd"] for r in t]
        return {
            "turns": len(t),
            "input_tokens": sum(r["input_total"] for r in t),
            "output_tokens": sum(r["output_total"] for r in t),
            "total_tokens": sum(r["input_total"] + r["output_total"] for r in t),
            "cache_read_tokens": sum(r["cache_read"] for r in t),
            "input_by_source": dict(by_in),
            "output_by_source": dict(by_out),
            "tool_calls": len(self.tool_calls),
            "failed_tool_calls": sum(c["is_error"] for c in self.tool_calls),
            "model_seconds": round(sum(r["model_seconds"] for r in t), 1),
            "tool_seconds": round(sum(c["seconds"] for c in self.tool_calls), 1),
            "cost_usd": None if None in costs else round(sum(costs), 5),
        }
