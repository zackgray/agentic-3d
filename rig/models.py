"""Which backend serves each model the rig can run, and how it is pinned.

Anthropic models go to the Anthropic API as before. Cross-family models (owner's go, 2026-11-19;
Kimi stays excluded) go through OpenRouter, each pinned to one provider with fallbacks off, so every
run sees the same weights and serving. A local model goes to an OpenAI-compatible server whose
address comes from LOCAL_MODEL_URL in the environment (kept out of the repository).

The key is the name used on the command line and in run folders.
"""

OPENROUTER = {
    # key: (OpenRouter id, provider, quantizations or None, reasoning supported)
    "gpt-6.2-sol": ("openai/gpt-6.2-sol", "OpenAI", None, True),
    # Screened 2026-11-19 and replaced: Sol Pro is Sol in a "pro" mode that bills about 4x the
    # input for the same prompt; the 8B Llama never made a valid tool call (0/6).
    "gpt-6.2-sol-pro": ("openai/gpt-6.2-sol-pro", "OpenAI", None, True),
    "gemini-4-neon": ("google/gemini-4-neon", "Google AI Studio", None, True),
    "qwen4-max": ("qwen/qwen4-max", "Alibaba", None, True),
    "deepseek-v4.1-flash": ("deepseek/deepseek-v4.1-flash", "DeepInfra", ["fp8"], True),
    "llama-3.1-8b": ("meta-llama/llama-3.1-8b-instruct", "CoreWeave", ["bf16"], False),
    "mistral-small": ("mistralai/mistral-small-2603", "Mistral", None, True),
}
LOCAL = ("local-qwen3.6-27b",)


def backend(model: str) -> str:
    if model.startswith("claude-"):
        return "anthropic"
    if model in OPENROUTER:
        return "openrouter"
    if model in LOCAL:
        return "local"
    raise SystemExit(f"unknown model {model!r}: add it to rig/models.py")


def make_client(model: str):
    """An Anthropic client, or an adapter with the same surface for any other backend."""
    import anthropic

    kind = backend(model)
    if kind == "anthropic":
        return anthropic.Anthropic(max_retries=4)
    from .openai_compat import CompatClient
    return CompatClient(model, kind)
