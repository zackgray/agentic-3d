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

## 2026-11-20 · First spec-first session: the soda bottle, Haiku throughout

**Built** (free). A two-step runner for the product-page briefs, `python -m rig.spec_session spec|build|compare <product>`. Step 1 is one call with no tools: the page text and the shot, and a request for a dimensioned spec with every value marked [page], [photo], [standard] or [guess] and the scale solved from the net contents. Step 2 is an ordinary sandboxed rig run on a task generated from the approved spec plus the owner's corrections, with the shot attached and only generic checks (names, transforms, watertight, no self-intersection, no overlap). A third step measures the build against the hidden key and renders it beside the reference, for the owner only. A task can now carry its own attached images, folded into the prompt fingerprint like the image arm's views.

**Measured** (owner's go: Haiku 5.5 low for both steps, Volta Citrus Soda, one session). The spec cost $0.003 (1,166 in, 5,563 out, 4,227 of them thinking). From one photo and "591 mL" it solved the bottle to 67 × 221 mm against the key's 68 × 223, and the cap to 30 × 17 mm against 30 × 16.5. It read the waist, the label band (correctly as print, not shape) and the shoulder. Its flaws were ones a non-modeller would approve: a hollow bottle with a 0.3 mm wall, and the neck stopping below the cap instead of running up inside it. The owner approved it with one plain-words correction ("make it solid; the neck continues up inside the cap; flat base and plain cap are fine"). The build passed every check in one turn, 5,343 tokens, $0.0013, 10.6 s: two lathes from the spec's station table.

| | Build | Key |
|---|---|---|
| Bottle size | 67 × 203.5 mm | 68 × 220 mm |
| Bottle volume | 610.7 mL | 654.7 mL |
| Cap size, top | 30 × 16.6 mm, top at 221.1 | 30 × 16.5 mm, top at 223.0 |
| Cap volume | 11.6 mL | 11.7 mL |

**What it means.** The thin brief was not the hard part: scale from net contents landed within 2% on height and width, and the spec read the photo well. Where it broke is the correction. The build made the bottle solid but ignored "the neck continues up inside the cap", because it traced the spec's station table literally and the table still stopped the neck at 203.5 mm. So the bottle is 16.5 mm short and the cap floats 1 mm above it, which no generic check catches. The waist is also shallower than the reference's. Lesson for the workflow: a correction has to go back into the spec (the agent revises the spec and the owner re-approves) rather than ride alongside it, since the builder trusts numbers over prose.

**Change and rerun.** Corrections now go back through the spec writer (`revise`: the owner's words as a follow-up turn, the full spec rewritten with the change in its numbers and marked), and the builder sees only the revised spec. The revision ($0.002) put a 26 mm neck from the finish ring up to 217 mm inside a hollow cap with a 1 mm wall, and asked one fair question (the cap is narrower than the finish ring, in the photo and the reference alike). It also added a "cap bottom edge" row to the bottle's station table, a trap a non-modeller wouldn't see; built as-is to test it. The build passed in two turns, 11,675 tokens, $0.0018, and skipped the trap: the neck now runs inside the cap with no overlap, bottle 67 × 217 mm (key 68 × 220), 618 mL (key 655), cap top at 221.1 (key 223.0). The cap is a hollow shell (2.5 mL) where the key's is solid (11.7 mL); that's a reference choice, not an error. What's still off is the spec's reading of the photo, not the hand-off: the waist is drawn 63 mm against a 67 mm body, shallower than the reference's, so the bottle is about 6% light.

**Spend.** $0.008 for the session, all Haiku.

## 2026-11-20 · Spec-first on the other three products (Haiku throughout)

**Run** (owner's go, owner away: the agent wrote the plain-words corrections a non-modeller would give, from the photo and the spec only, without looking at the key). Each product: spec from page text and shot, one revision with the corrections, build on harness-sandbox at h9, compare against the key. All Haiku 5.5 low, one session each.

| Product | Correction given | Build | Key | Build cost |
|---|---|---|---|---|
| Halden can | "a normal 12 oz drinks can; closed flat lid slightly below the rim; simple base" | 66 × 122.2 mm, 393 mL | 66 × 122.2 mm, 390 mL | 1 turn, 4,991 tokens |
| Northpeak bottle | "sounds too big for half a litre; check the volume works out to ~500 mL; ordinary small cap" | 64 × 203 mm, bottle 512 mL | 63 × 195 mm, bottle 500 mL | 1 turn, 5,566 tokens |
| Orchard carton | "standard gable-top carton: square, the top slopes like a roof to a thin sealed fin" | 88 × 88 × 230 mm, 1.58 L | 90 × 90 × 237 mm, 1.68 L | 2 turns, 10,742 tokens |

Every build passed its generic checks first time.

**What it means.** The first specs got two of three right on scale: the can within 2% from the photo alone, the carton within 3%. The ribbed bottle's first spec was 16% oversized (73 × 231 mm), and its own volume didn't add up to its stated target; a client's "that sounds too big, check the volume" fixed it to within 4%. Naming the standard ("a normal 12 oz can") snapped the can to exact standard dimensions. The carton's front shot hides the gable (face-on, a roof reads as a flat band), so the first spec drew a near-flat top; one sentence from the client gave a correct roof and fin. Two weaknesses repeat: the water bottle's neck again stops below the cap (the cap sits on top, as in the soda's first build, because the correction didn't mention it this time), and its ribs came out as three broad grooves where the photo shows five tight ones. So across four products: scale from net contents plus a photo is within a few per cent once a client sanity-checks it, the hand-off now carries corrections, and what's left is detail read from the photo (rib count, waist depth) and the neck-inside-cap convention, which a standing line in the spec prompt could fix.

**Spend.** $0.02 for the three sessions; about $0.03 for the day's spec-first work. Phase 3 about $15.78 of $20.

**Next (recommended).** Add one line on closures (the neck runs up inside the cap) to the spec prompt and rerun the water bottle; then decide whether to build the scored arm (spec and build scored against the key over several runs per product).

## 2026-11-23 · The closure line, and the water bottle rerun

**Changed.** One standing line in the spec prompt: a closure fits over the container the way the real one does, with the neck running up inside the cap to just below its top, so the cap's height range overlaps the neck's in the station table.

**Measured** (owner's go, Haiku 5.5 low, Northpeak bottle, same plain-words correction as on 2026-11-20 so the line is the only change). The first spec put the neck inside the cap unprompted (neck to 198 mm inside a cap to 200 mm), and this time landed on scale before any correction: 63 × 200 mm against the key's 63 × 195, where the earlier first spec was 73 × 231. The revision and build followed: bottle 64 × 198 mm, 510 mL (key 63 × 191 mm, 500 mL), cap top at 200 (key 195), all generic checks passed in two turns, 14,927 tokens, $0.0028. The render reads as the same product as the reference. Still off: three broad grooves where the reference has five tight ones, and a hollow 22 mm cap where the key's is a solid 15 mm one (a reference convention, as with the soda).

**What it means.** The neck-inside-cap fault is fixed by the prompt rather than by the client having to know to ask. The first spec's scale swung from 16% oversized to within 3% between two runs of the same prompt, so single sessions can't say how good the first spec is; that's what the scored arm is for.

**Spend.** $0.008 (spec $0.0021, revision $0.0035, build $0.0028). Phase 3 about $15.79 of $20.

## 2026-11-23 · The scored spec-first arm: 60 builds against the hidden keys

**Built** (free). A repeat runner over three arms, a scorer, review renders and a blind judging page. The arms, per product and rep: *direct* (page text and photo straight to the builder, no spec), *spec* (the first spec built unread, as if a non-modeller approved it), and *spec1* (the first spec, one fixed correction, the revised spec built). The corrections were written and frozen before any run, one per product, naming the kind of product and no numbers ("a standard 20 oz soda bottle; make it solid", "a normal 12 oz drinks can with a closed lid", "an ordinary half-litre water bottle; check the volume works out", "a standard gable-top carton, the top slopes like a roof to a thin fin"). A rep passes when the main container's height, width and volume are all within 5% of the key and the generic build checks pass.

**Scorer change before the run.** The first smoke rep showed enclosed volume punishes a convention: a first-spec can drew a thin-walled hollow can, matched height and width exactly, and scored −92% on volume. The scorer now measures the outside: rays fired inward at 120 heights × 32 angles on both the build and the key's reference model, integrated into an outside volume. Solid or hollow no longer counts, as already for caps. A scale-free profile error is recorded but not scored.

**Measured** (owner's go, Haiku 5.5 low, harness-sandbox at h9, 4 products × 3 arms × 5 reps, no voids, $0.25).

| Arm | Passed | Median tokens | Tokens per pass | Cost |
|---|---|---|---|---|
| direct | 7/20 | 5,103 | 17,988 | $0.034 |
| spec | 10/20 | 11,882 | 26,985 | $0.082 |
| spec1 | 11/20 | 22,620 | 54,462 | $0.150 |

| Product | direct | spec | spec1 |
|---|---|---|---|
| Can | 5/5 | 4/5 | 4/5 |
| Water bottle | 1/5 | 1/5 | 4/5 |
| Carton | 0/5 | 1/5 | 2/5 |
| Soda | 1/5 | 4/5 | 1/5 |

**What it means.** The spec step earns its tokens: 10 passes against 7, at 1.5× the tokens per pass, and it's what makes the soda land (4/5 against 1/5). Building straight from the brief only works for a product with one obvious standard size (the can, 5/5 at 4k tokens). The generic correction is a coin flip: it fixes what the first spec got wrong (water bottle 1 → 4, the first specs ran 7% tall and 16% over volume) and breaks what it got right (soda 4 → 1: "a standard 20 oz bottle" pulls the height to the model's idea of a standard bottle, 6–9% shorter than this reference). It also doubles the tokens, and the corrected water bottles turned into 3–6-turn builds of hollow bottles (median 51k). The carton is the weak product in every arm: widths 6–12% narrow, since a face-on shot hides the depth and the gable. Five reps per cell is small; the direction is clear, the per-cell numbers are not.

**Next.** The owner grades shape blind on the judging page (60 items); the reveal joins grades to arms. Then the case study.

**Owner's shape grades (blind, 60 of 60).** "Does it look like the product in the photo?", 1–5, arms hidden and shuffled. Mean by arm: direct 2.45, spec 2.95, spec1 3.25. By product, the can was the clearest: spec 4.6, spec1 4.4, direct 2.4. The carton: spec1 3.4, the others 2.2–2.4. Water bottle 2.2–2.8 throughout. Soda: direct 3.0, spec 2.2, spec1 2.4. Only 12 of 60 builds scored 4 or 5, and 8 of those also passed on size.

**What the grades add.** Size and shape are different questions, and the spec step solves the first more than the second. The direct can was exact on size (5/5 passes) and graded 2.4: it came out as a tin with an overhanging lid. The first-spec soda passed on size 4 times in 5 and was graded 2.2: a straight conical shoulder and a shallow waist where the photo shows a rounded shoulder and a deep waist. The measured profile error tracks the grades only loosely (correlation −0.5). So scale from net contents is solved; reading the profile's character from the photo is the open problem, and it's the next lever.
