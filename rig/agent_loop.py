"""A deliberately thin agent loop. The request carries only the setup's system prompt and tools,
so every input token belongs either to the setup under test or to the conversation it produced."""
import json
import time

from .accounting import Counter, Ledger


def run_agent(client, model: str, effort: str, setup, prompt: str, counter: Counter, ledger: Ledger,
              transcript: list, max_turns: int = 40, max_tokens: int = 16000, request: dict | None = None,
              max_cost: float | None = None) -> dict:
    ledger.add("system", counter.system(setup.system))
    ledger.add("tool_definitions", counter.tools(setup.tools))
    ledger.add("task_prompt", counter.text(prompt))
    intro = setup.initial_context() if hasattr(setup, "initial_context") else ""
    if intro:  # a setup may read the scene up front; it rides in the first message, counted on its own
        ledger.add("scene_summary", counter.text(intro))
        prompt = prompt.rstrip() + "\n\n" + intro
    opts = dict(request or {})
    drop_old_thinking = opts.pop("rig_drop_old_thinking", False)
    thinking_by_turn: list[int] = []
    messages = [{"role": "user", "content": prompt}]
    transcript.append({"role": "user", "content": prompt})

    for _ in range(max_turns):
        t0 = time.monotonic()
        api = client.beta.messages if "betas" in opts else client.messages
        resp = api.create(
            model=model, max_tokens=max_tokens, system=setup.system, tools=setup.tools,
            messages=without_old_thinking(messages) if drop_old_thinking else messages,
            output_config={"effort": effort}, cache_control={"type": "ephemeral"}, **opts,
        )
        seconds = time.monotonic() - t0
        text_out = sum(counter.text(b.text) for b in resp.content if b.type == "text")
        code_out = sum(counter.text(json.dumps(b.input)) for b in resp.content if b.type == "tool_use")
        cleared = sum(thinking_by_turn[:-1]) if drop_old_thinking else 0  # thinking this request didn't resend
        row = ledger.turn(resp.usage, text_out, code_out, seconds, resp.stop_reason, cleared_thinking=cleared)
        transcript.append({"role": "assistant", "content": [b.model_dump(mode="json") for b in resp.content],
                           "usage": resp.usage.model_dump(mode="json"), "ledger": row})
        messages.append({"role": "assistant", "content": resp.content})  # unchanged: thinking replays intact
        ledger.add("agent_text", text_out)
        ledger.add("agent_code", code_out)
        thinking_by_turn.append(row["output_by_source"]["thinking"])
        ledger.add("thinking_replay", row["output_by_source"]["thinking"])  # thinking blocks are resent, and billed, as input

        if resp.stop_reason != "tool_use":
            return {"end": resp.stop_reason, "turns": ledger.summary()["turns"]}
        spent = ledger.summary()["cost_usd"]
        if max_cost is not None and spent is not None and spent >= max_cost:
            # A spend guard, scored like the turn cap. No Anthropic run has come near it (dearest
            # $0.10); a weak model sending malformed calls looped 29 turns (2026-11-19).
            return {"end": "cost_cap", "turns": ledger.summary()["turns"]}

        results, finished = [], False
        for b in resp.content:
            if b.type != "tool_use":
                continue
            out = setup.call(b.name, b.input)
            finished = finished or getattr(out, "final", False)
            n = counter.text(out.text)
            images = getattr(out, "images", [])
            n_img = sum(counter.image(mt, data) for mt, data in images)
            ledger.add("tool_results", n)
            ledger.add("images", n_img)
            ledger.tool_call(b.name, out.is_error, out.seconds, n + n_img)
            content = out.text
            if images:  # tool results may carry images; the model sees them as the server sent them
                content = ([{"type": "text", "text": out.text}] if out.text else []) + [
                    {"type": "image", "source": {"type": "base64", "media_type": mt, "data": data}}
                    for mt, data in images]
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": content,
                            "is_error": out.is_error})
        messages.append({"role": "user", "content": results})
        transcript.append({"role": "user", "content": strip_images(results)})
        if finished:  # the setup accepted a call marked final, so no closing turn is needed
            return {"end": "finished_by_tool", "turns": ledger.summary()["turns"]}

    return {"end": "turn_cap", "turns": max_turns}


def without_old_thinking(messages: list) -> list:
    """The history with thinking removed from every assistant message but the latest: a leading run of
    thinking blocks, oldest first, which keeps the remaining blocks valid under the history check."""
    last = max(i for i, m in enumerate(messages) if m["role"] == "assistant") if len(messages) > 1 else -1
    out = []
    for i, m in enumerate(messages):
        if m["role"] == "assistant" and i != last:
            kept = [b for b in m["content"] if getattr(b, "type", None) not in ("thinking", "redacted_thinking")]
            m = {**m, "content": kept or m["content"]}
        out.append(m)
    return out


def strip_images(results: list) -> list:
    """Transcript copy without base64 payloads (they're counted in the ledger, not kept on disk)."""
    out = []
    for r in results:
        c = r["content"]
        if isinstance(c, list):
            c = [b if b["type"] != "image" else {"type": "image", "omitted_bytes": len(b["source"]["data"])}
                 for b in c]
        out.append({**r, "content": c})
    return out
