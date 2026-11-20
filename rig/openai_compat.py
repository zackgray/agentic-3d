"""An adapter with the Anthropic client's surface (messages.create, messages.count_tokens) over an
OpenAI-style chat endpoint: OpenRouter, or a local server. The agent loop, setups and ledger stay as
they are; requests and responses are translated here.

Accounting differences, recorded with every run:
- Totals (input, output, cached, cost) are the provider's own figures. OpenRouter reports the cost
  of each request; a local model costs 0.
- The split of input by source is approximate: block sizes are estimated at 4 characters a token,
  because these providers have no free counting endpoint. Whatever that misses lands in
  "unattributed", as before.
- Thinking tokens are the provider's reasoning-token count where it gives one; otherwise the ledger
  infers them as before.
"""
import json
import math
import os
import time
import uuid
from dataclasses import asdict, dataclass, field

import anthropic
import httpx

from .models import OPENROUTER

OPENROUTER_URL = "https://openrouter.ai/api/v1"
TIMEOUT = 600  # s per request: reasoning and local models can be slow
RETRIES = 5


class AdapterError(anthropic.AnthropicError):
    """An API fault on a non-Anthropic backend; the runner records the run as void."""


@dataclass
class Block:
    type: str
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict | None = None
    thinking: str | None = None
    raw: dict | None = None  # reasoning fields to send back unchanged

    def model_dump(self, mode=None):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Details:
    thinking_tokens: int | None


@dataclass
class Usage:
    input_tokens: int
    cache_read_input_tokens: int
    output_tokens: int
    output_tokens_details: Details
    cost_usd: float | None
    provider: str | None
    cache_creation_input_tokens: int = 0

    def model_dump(self, mode=None):
        return asdict(self)


@dataclass
class Response:
    content: list
    stop_reason: str
    usage: Usage


@dataclass
class Count:
    input_tokens: int


def estimate(n_chars: int) -> int:
    return math.ceil(n_chars / 4)


def to_openai(system: str, messages: list) -> list:
    out = [{"role": "system", "content": system}]
    for m in messages:
        c = m["content"]
        if m["role"] == "user":
            if isinstance(c, str):
                out.append({"role": "user", "content": c})
                continue
            for b in c:
                if b.get("type") == "tool_result":
                    body = b["content"]
                    if isinstance(body, list):
                        body = "\n".join(x.get("text", "") for x in body if x.get("type") == "text")
                    out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": body})
                elif b.get("type") == "text":
                    out.append({"role": "user", "content": b["text"]})
            continue
        msg = {"role": "assistant", "content": "".join(b.text for b in c if b.type == "text") or None}
        calls = [{"id": b.id, "type": "function",
                  "function": {"name": b.name, "arguments": json.dumps(b.input)}} for b in c if b.type == "tool_use"]
        if calls:
            msg["tool_calls"] = calls
        for b in c:
            if b.type == "thinking" and b.raw:
                msg.update(b.raw)
        out.append(msg)
    return out


def from_openai(data: dict, local: bool) -> Response:
    if "error" in data:
        raise AdapterError(f"provider error: {json.dumps(data['error'])[:500]}")
    choice = data["choices"][0]
    msg = choice.get("message") or {}
    blocks = []
    reasoning = msg.get("reasoning") or msg.get("reasoning_content")
    raw = {k: msg[k] for k in ("reasoning_details", "reasoning_content") if msg.get(k)}
    if reasoning or raw:
        blocks.append(Block("thinking", thinking=reasoning or "", raw=raw or None))
    if msg.get("content"):
        blocks.append(Block("text", text=msg["content"]))
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:  # malformed arguments are the model's failure, shown as bad input
            args = {"_unparsed": fn.get("arguments")}
        blocks.append(Block("tool_use", id=tc.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                            name=fn.get("name"), input=args if isinstance(args, dict) else {"_unparsed": args}))
    has_calls = any(b.type == "tool_use" for b in blocks)
    stop = "tool_use" if has_calls else ("max_tokens" if choice.get("finish_reason") == "length" else "end_turn")
    u = data.get("usage") or {}
    cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
    prompt = u.get("prompt_tokens") or 0
    usage = Usage(input_tokens=prompt - cached, cache_read_input_tokens=cached,
                  output_tokens=u.get("completion_tokens") or 0,
                  output_tokens_details=Details((u.get("completion_tokens_details") or {}).get("reasoning_tokens")),
                  cost_usd=0.0 if local else u.get("cost"), provider=data.get("provider"))
    return Response(blocks, stop, usage)


@dataclass
class CompatClient:
    model: str
    kind: str  # "openrouter" or "local"
    _http: httpx.Client = field(init=False, repr=False)

    def __post_init__(self):
        self.messages = self
        if self.kind == "openrouter":
            key = os.environ.get("OPENROUTER_API_KEY")
            if not key:
                raise AdapterError("OPENROUTER_API_KEY is not set")
            self.base, headers = OPENROUTER_URL, {"Authorization": f"Bearer {key}"}
            self.model_id, self.provider, self.quant, self.reasons = OPENROUTER[self.model]
        else:
            self.base, headers = os.environ.get("LOCAL_MODEL_URL", "").rstrip("/"), {}
            if not self.base:
                raise AdapterError("LOCAL_MODEL_URL is not set")
            self.provider, self.quant, self.reasons = "local", None, True
        self._http = httpx.Client(headers=headers, timeout=TIMEOUT)
        if self.kind == "local":
            self.model_id = self._send("GET", "/models")["data"][0]["id"]

    def describe(self) -> str:
        pin = f" quant {','.join(self.quant)}" if self.quant else ""
        return f"{self.kind} {self.model_id} via {self.provider}{pin}"

    def _send(self, method: str, path: str, body: dict | None = None) -> dict:
        for attempt in range(RETRIES):
            try:
                r = self._http.request(method, self.base + path, json=body)
            except httpx.HTTPError as e:
                err = f"{type(e).__name__}: {e}"
            else:
                if r.status_code == 200:
                    return r.json()
                err = f"HTTP {r.status_code}: {r.text[:500]}"
                if r.status_code not in (408, 429, 500, 502, 503, 504):
                    raise AdapterError(err)
            time.sleep(2 ** (attempt + 1))
        raise AdapterError(f"gave up after {RETRIES} tries: {err}")

    def create(self, model, max_tokens, system, tools, messages, output_config=None, cache_control=None, **_):
        effort = (output_config or {}).get("effort")
        body = {"model": self.model_id, "messages": to_openai(system, messages), "max_tokens": max_tokens,
                "tools": [{"type": "function", "function": {"name": t["name"], "description": t["description"],
                                                            "parameters": t["input_schema"]}} for t in tools]}
        if self.kind == "openrouter":
            body["provider"] = {"order": [self.provider], "allow_fallbacks": False, "data_collection": "deny",
                                **({"quantizations": self.quant} if self.quant else {})}
            body["usage"] = {"include": True}
            if self.reasons and effort:
                body["reasoning"] = {"enabled": False} if effort == "none" else {"effort": effort}
        elif effort == "none":
            body["chat_template_kwargs"] = {"enable_thinking": False}
        return from_openai(self._send("POST", "/chat/completions", body), self.kind == "local")

    def count_tokens(self, model, messages, system=None, tools=None, **_) -> Count:
        """Approximate (4 characters a token); see the module docstring."""
        n = len(system or "") + (len(json.dumps(tools)) if tools else 0)
        for m in messages:
            c = m["content"]
            n += len(c) if isinstance(c, str) else len(json.dumps(c))
        return Count(estimate(n) + 4)
