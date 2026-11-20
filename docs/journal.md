# Journal

Dated record of the work: what was done, what was decided and why, and what was measured. Newest at the bottom. This is the raw material for the case study. Earlier entries: Phases 0–2 in `docs/journal-phases-0-2.md`; Phase 3 in `docs/journal-phase-3-h1-h6.md` (harness v1 to h6) and `docs/journal-phase-3-h7-h9.md` (h7 to h9, the Sonnet and cross-family arms); the Phase 3 report is `docs/report.md`.

## 2026-11-20 · Phase 3 report written; the image arm, Haiku round

**Report.** Phase 3's target is met on development, held-out and other labs' models, so the write-up the owner deferred on 2026-11-17 is now drafted as `docs/report.md` (the blog-post draft), and the case study's "What it shows" is filled in. Every figure in it traces to a dated journal entry. Phase 3 entries h7 to h9 moved to `docs/journal-phase-3-h7-h9.md`.

**Why images.** Clients send pictures, not only specs. The owner chose to measure in steps: first the full written spec plus pictures (one variable, checks unchanged), on Anthropic models first (paid credits), with the same with- and without-harness baseline as every other arm.

**Built.** A prompt arm, `views`: the task's full prompt plus four 480 px renders of its reference model (front, side and top orthographic, a three-quarter view, one flat colour per object), attached before the text in the first message. One added sentence says the written sizes are exact and the views are for shape. Rendered once by `python -m rig.render_briefs` and committed, so every run sees the same bytes; the image bytes are part of the prompt fingerprint. Revision tasks are left out (they start from a model already), so the arm covers the 22 build tasks. The views show the exact model the checks grade, so this is an upper bound on what a picture can add. Image tokens are their own source in the ledger.

**Measured** (owner's go; Haiku 5.5 low, 22 build tasks, one run per task per cell, both setups sandboxed, harness at h9, no voids; the harness text cell is the 2026-11-20 h9 round). `python -m rig.compare --setups no-mcp-sandbox harness-sandbox --version harness-sandbox=h9 --arm <base|views> --tasks h0 l0 m0 p0`.

| | No MCP, text | No MCP, views | Harness, text | Harness, views |
|---|---|---|---|---|
| Pass | 21/22 | 18/22 | 21/22 | 21/22 |
| Tokens per passed task | 28,722 | 24,296 | 8,712 | 7,975 |
| Typical (geometric mean) tokens | 16,698 | 17,831 | 5,838 | 6,807 |
| Harness ratio, typical | | | 0.35 | 0.38 |
| Wall time per run | 36.1 s | 30.4 s | 16.5 s | 14.5 s |

**What it means.** With a complete written spec, pictures add cost and no accuracy. Four views are 1,308 input tokens, resent on every turn (cached), so the typical task rose 7% without the harness and 17% with it (the harness's runs are short, so the fixed image cost is a bigger share). The per-pass figures fell on both setups, but that is the tail moving (one 176k text-arm baseline run on h04), not the images; the typical figure is the honest one. The harness passed 21/22 either way. The baseline dropped from 21 to 18, but two of its four failures with views were millimetre sizes written as metres (a flashlight and a soap bar built 1,000 times too large), the slip h9 guards against in the harness and nothing guards against in the baseline. The other two were a cream tube 4 mm thick instead of 30 and a speaker's buttons sunk into its body. With 22 runs a cell, 18 against 21 is inside the noise. The harness's advantage holds with images: 0.38 of the baseline on the typical task, against 0.35 with text.

**Next (recommended).** Running Sonnet on this arm (~$2.50) would most likely confirm the same redundancy. Pictures should matter where they carry information the text doesn't: a brief of views plus a few headline sizes. That arm needs the 22 prompts shortened and the checks limited to what the brief pins down, so it is an owner decision.

**Spend.** $0.22 (Haiku, 66 runs including one smoke run). Phase 3 about $15.75 of $20.

## 2026-11-20 · Product-page briefs: four invented products

**Why.** The owner's real briefs look like a retailer's product page: one front photo, the net contents and the container type, with no dimensions. Every task so far hands the agent exact sizes, so the benchmark doesn't yet test the step that matters most to someone who isn't a modeller: turning a thin brief into a dimensioned spec. The workflow discussed: the agent writes a spec from the brief (profile from the photo, scale from the net contents, neck and cap from packaging standards, guesses marked), the owner approves it in plain words, then it builds.

**Built** (free). `products/`: four invented products, each with page text, one product-page style front shot (white background, long lens, slightly above, no scale cue, a printed label band in the picture only), a hidden reference model and a measured key. A contoured 20 fl oz soda bottle with cap (68 × 223 mm, 655 mL outer against 591 mL), a 12 fl oz can at standard can size (66 × 122.2 mm), a ribbed 500 mL water bottle with cap (63 × 195 mm), and a 52 fl oz gable-top carton (90 × 90 × 237 mm). Outer volumes sit about 10% over net contents, as real packaging does for headspace and wall. All names and shapes are invented; no real brand or trade dress, since the repo is public and limited to hypothetical products. `python -m rig.product_briefs` rebuilds the shots and keys; a unit test keeps each product complete and checks that the page text carries no dimensions.

**Housekeeping.** Blender stamps metadata into rendered PNGs, including the local path of the scene file, so the renderers now switch it off and the committed views and shots were stripped. Pixels are unchanged (re-renders of two tasks match bit for bit), so the images the models saw are the ones committed; the 44 image-arm run records were re-fingerprinted, with a note, and the comparison above reproduces exactly.

**Next.** One live spec-first session with the owner on these (cents), before any scoring is built. If the specs come back sensible, the scored arm measures the spec against the key (height, width, volume, profile) and the build against the reference.
