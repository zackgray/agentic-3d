"""Prompt arms for controlled prompt tests. An arm appends one passage to the task prompt and is
recorded in the run, so a prompt change is measured on its own before it reaches the real tasks.

"base" is the task prompt unchanged. An arm may instead (or also) change the request: REQUEST holds
the extra API parameters for such arms, so a settings change is recorded and matched like any arm.
"""
ARMS = {
    "base": "",
    # Owner's test 2026-11-17: does saying it stop duplicate vertex rings (zero-length edges)?
    # It did (7/50 -> 0/50), so since 2026-11-17 this text is in every task prompt and "base"
    # includes it. Kept so the test's runs stay reproducible; apply() refuses to add it twice.
    "clean-mesh": (
        "Mesh hygiene: no duplicate or coincident vertices, no zero-length edges and no zero-area "
        "faces. Merge any coincident vertices before you finish."
    ),
    # Thinking arm (owner, 2026-11-18): same prompt, thinking turned off. Haiku 5.5 accepts this at
    # low effort. Applied to no-MCP and the harness alike (Phase 3 ground rules).
    "think-off": "",
    # Thinking arm, part 2 (owner, 2026-11-18): thinking on, but only the latest response's thinking
    # is resent. Server-side clearing can't do this: it treats a whole tool loop as one turn and keeps
    # it. Dropping a leading run of thinking blocks (oldest first) keeps later blocks valid on Haiku 5.5.
    "clear-thinking": "",
    # Image arm (owner, 2026-11-20): the full written spec plus rendered views of the reference model,
    # attached to the first message (IMAGES). Build tasks only; views from rig/render_briefs.py.
    "views": (
        "Attached are four views of the finished product: front (looking along +Y), side (looking "
        "along -X) and top, all orthographic, and a three-quarter view. Each object has its own flat "
        "colour. The written sizes above are exact; use the views for shape."
    ),
}

IMAGES = {"views": "brief"}  # arm -> the task subfolder whose rendered views ride in the first message

REQUEST = {
    "think-off": {"thinking": {"type": "disabled"}},
    "clear-thinking": {"rig_drop_old_thinking": True},  # handled by the agent loop, not sent to the API
}


def apply(prompt: str, arm: str) -> str:
    extra = ARMS[arm]
    if extra and extra in prompt:
        raise ValueError(f"arm {arm!r} is already part of this task's prompt")
    return prompt if not extra else prompt.rstrip() + "\n\n" + extra
