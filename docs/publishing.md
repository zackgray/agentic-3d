# Publishing

How changes reach the public repository. Read before any commit that will be pushed.

## Branches

- `main` is the only public branch. Push `main` and explicit tags, nothing else.
- Experiments live on a local branch each and are never pushed. If one is adopted, its changes come to `main`; if not, the branch stays local as the record, and the journal says what was measured.
- Don't rewrite history on `main` once pushed.

## Before every push

1. Run the unit tests: `python -m pytest`. CI runs them again on the push. If the change touched the harness or the sandbox, also run the live tests: `python tests/harness_selftest.py`, with `--sandbox` too, and `python tests/sandbox_walls.py`.
2. Read the diff for anything that mustn't be public: personal details, names of businesses or clients, internal machine names, local paths that contain a user name, keys or tokens. `.env` and `runs/` are git-ignored; keep them that way.
3. Check that the docs match the change (below).

## Docs ship with the code

- `docs/journal.md`: a dated entry for every session: what was done, decided (and why), and measured, with the numbers.
- `docs/case-study.md`: updated when a measured result lands.
- `README.md`: updated when setup steps, commands or headline numbers change.
- Pushing `main` publishes all of these; there is no separate docs step.

## Tags and releases

- Tag and release only when a harness version is frozen and measured, or a held-out result is published. The tag is the harness version (for example `h7`).
- Run records never go in git. They are attached to the release as one zip of the runs behind its published figures (`h7` carries `agentic-3d-runs.zip`). Runs from experiments, check rounds and arms not in a release stay local.
- Infrastructure that doesn't change what the model sees (such as the sandbox) and experiments that weren't adopted get no tag.

## Commits

- One plain sentence saying what changed, with detail in the body if needed. The journal carries the reasoning.
- Keep the co-author line on commits made with Claude.
