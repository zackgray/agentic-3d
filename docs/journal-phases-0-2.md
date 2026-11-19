# Journal, Phases 0–2 (2026-11-16 to 2026-11-17)

The earlier half of the dated record, split from `docs/journal.md` to keep files small. Phase 3 onward is in `docs/journal.md`.

## 2026-11-16 · Exploration and project start

**Question going in:** how is agentic 3D modeling done today, what MCP servers exist, and could a harness (or a fine-tuned local model) make it more efficient?

**What the research found** (detail and sources in `research.md`):

- Three approaches are converging: an LLM driving Blender over MCP, code-as-geometry research (LL3M, BlenderAlchemy, CadQuery benchmarks), and generative mesh models (TRELLIS 2, Hunyuan3D).
- The current Blender MCP servers waste tokens in four places: 100–200-tool menus sent every turn, a screenshot as the only feedback, brittle step-by-step scripts with no persistent scene state, and one frontier model doing both judgement and chores.
- Cinema 4D got an official MCP server in 2026.4 (Sept 2026). Blender still wins for an agent because it runs headless, free, in parallel, and models write its Python far more fluently.
- Fine-tuning is viable because code-to-geometry checks itself: frontier runs that pass the checks become training data. Expected payoff is cost and latency on the inner loop, not better spatial judgement than a frontier model.

**Key insight:** a 3D scene is numbers, but raw numbers are the worst encoding. A 100k-vertex mesh as text is over a million tokens; a render is ~1.5k. The compressed form is the *description of how it was built* (code, parameters, a scene graph), plus computed facts (dimensions, gaps, intersections) that an image can only estimate. Images stay for appearance only.

**Decisions:**

- Use case: commercial product CGI, all tasks hypothetical. The agent models; a human artist lights and textures.
- Eval suite and baselines before any harness code. Why: goal #1 is fewer tokens, and that claim needs a measured "before".
- Baseline model: Claude Haiku 5.5 at low effort (cheapest, least token-hungry), stepping up to Sonnet 5.5 if Haiku can't pass the pilot. Kimi as a second column. Why: compare harnesses within a model; the cheapest viable model keeps the matrix affordable.
- Interface: a stripped-down Blender viewport to watch the agent live, with interrupt between atomic steps. Why: seeing it work and stopping it early saves both tokens and frustration. Browser three.js was considered and set aside for now; it's a display layer, not an authoring tool.
- Named, bounded parameters as a core concept, shared by agent and UI. Why: one number per change is cheap for the agent and lets the owner art-direct with sliders.
- Evaluate pass / fail / void. Why: carried from earlier agent work, where setup faults were once misread as model limits.

**Next:** draft the pilot (5 product tasks, starting scenes, automatic checks), then set up the four baselines.

## 2026-11-16 · Roadmap

Drafted `roadmap.md`: eight phases from the eval rig to product animation, each ending at a written exit check and an owner gate. Ordering choices and why:

- The eval rig (Phase 0) comes before even the pilot, because every later claim rests on the checks and the token breakdown being right. A deliberately broken setup must come out void, not fail.
- The baseline report (Phase 2) is treated as a deliverable in its own right: no Blender-specific agent benchmark exists, so a measured account of where Blender agents spend tokens is citable before any harness exists.
- The harness (Phase 3) is designed from the Phase 2 breakdown, not from the principles in the README, which stay hypotheses until measured.
- Watch mode (Phase 4) follows the harness because interrupting needs the harness's one-undo-step-per-action design.
- The local model (Phase 6) is gated on evidence that inner-loop volume makes cost or latency matter.
- Kimi does the heavy authoring for Phases 0–1 first.

Open for the owner: the Phase 3 target (proposed: half the tokens of the best baseline at an equal or better pass rate) and whether the baseline report is published.

**Decided (owner, same day):** the Phase 3 target stands as a starting bar. The owner's view that current Blender harnesses are heavy comes from reading, not first-hand use, so the target is revisited once the baselines are measured. The baseline report will be published as a blog post, which raises the bar for Phase 2: pinned versions, a publishable task set and checks, and fair treatment of each baseline's authors.

## 2026-11-16 · Kimi dropped

Checked how Kimi could be driven: only as the Kimi Code CLI in headless print mode, building in a throwaway working copy with Claude reviewing the diff. That suits authoring but can't serve as a measured column: the CLI adds its own system prompt, tools and sub-agents and reports no per-turn usage. A direct API column would have needed a separate key.

**Decided (owner):** drop Kimi entirely, as a baseline column and as an authoring worker. Anthropic models only. Why: a second model family added cost and setup without serving goal #1, since harnesses are compared within one model. The runner's named risk narrows to clean token attribution in our own loop.

## 2026-11-16 · Phase 0: eval rig built, first task's checks proven

**Built:** the rig, in Python, about 950 lines across small files. It covers the task format (one folder per task: prompt, starting scene, checks), a check library that runs inside headless Blender, the first baseline setup (no MCP: one tool that runs agent-written Python in headless Blender against the saved scene), a thin agent loop on the Anthropic SDK, token accounting by source, and a run record under `runs/`.

**First task, p01:** a bottle (70 mm body, 28 mm neck with a 3 mm-pitch helical thread) and a hollow screw cap seated on it, all dimensions exact. Eleven checks: object names, transforms applied, two bounding boxes (±0.5 mm), a helical thread, watertight, self-intersection, cap-to-bottle intersection, topology health (degenerate faces, loose geometry, consistent outward normals) and two face budgets.

**Checks proven before any agent touched them (free):** a hand-written reference model passes all eleven, and six deliberately broken versions each fail exactly the check they target and nothing else (no thread, stacked rings instead of a helix, a cap too tight for the thread, an unapplied transform, an open mesh, a block poking through the surface). The thread check uses phase concentration: on a helix, the crest vertices' height-minus-angle phase is constant, so stacked rings score near zero (reference 0.77, threshold 0.6).

**Void path proven:** a wrong Blender path and missing API credentials both record void without a model call. Any exception from the rig itself also records void, never fail.

**Decisions and why:**

- Our own loop, not the Agent SDK or Claude Code, because the request must carry only the setup's own system prompt and tools for the token split to mean anything.
- Each input turn is split by source using the free count-tokens endpoint per block; whatever the counts don't explain (replayed thinking, framing) is reported as "unattributed", not hidden. Thinking output comes straight from the API's own thinking-token count.
- Prompt caching on (top-level automatic), as any sensible user would run it. Tokens are counted the same either way; it only changes cost.
- Every tool call is one atomic step: a script that raises leaves the scene untouched. That is the rig's convention for the no-MCP baseline, recorded as setup version rig-1.

**Measured:** nothing on a model yet. Blender starts per tool call in about 1.5 s; the full check self-test takes about 35 s.


## 2026-11-17 · Phase 0: first real runs, a check bug caught, exit check met

**API access:** the eval runs on a dedicated API organization. A subscription login was ruled out for the harness (its usage would mix with other use and the numbers wouldn't reproduce), and so was OpenRouter (no count-tokens endpoint, so the per-source split would break). The key is scoped to 30 days and lives in the repo's git-ignored `.env`.

**Run 1** (p01, no MCP, Haiku 5.5 low): 2 turns, 18,112 tokens, $0.0052, 44 s. Haiku wrote the whole model in one script, checked it, and declared it done. Recorded as fail on two checks. Reviewing why before trusting it:

- *Cap normals: a correct fail.* The cap's top and inner-top faces are wound opposite to its walls (128 mismatched edges), which would render as a shading fault on the most visible face of the product. The agent's own self-check said the normals were fine because total signed volume was positive; that test can't see a partial flip.
- *Thread: a check bug.* The agent built a valid helix with a wide flat crest. The thread check implicitly assumed a narrow crest and scored it 0.30 against a 0.6 bar. Replaced with a profile-independent test: on a screw surface a vertex's radius depends only on its phase along the helix, so phase bins explain nearly all radius variance (reference 0.997; the agent's wide-crest thread passes; stacked rings fail). A wide-crest variant joined the self-test, and the run was re-checked with its original verdict kept in its record.

**Accounting fix:** run 1 left 5,469 input tokens unattributed on turn 2, matching turn 1's 5,578 thinking tokens: thinking blocks are resent, and billed, as input. They're now attributed as "thinking replay", estimated from the API's own thinking count.

**Run 2** (same setup): pass. 2 turns, 17,533 tokens, $0.0048, 44.5 s. Unattributed input fell to -54 of 9,761 (0.6%).

**Where the tokens went in run 2:** thinking is 75% of output (5,804 of 7,772), and its replay is 59% of input (5,728 of 9,761). The agent's code is 1,545 each way; the tool definition is 880; the system prompt 240. Two runs is not a finding, but it points somewhere the README's hypotheses didn't: on a one-script task at low effort, reasoning, not tool menus or scene reads, is the bulk of the bill.

**Phase 0 exit check: met.** One task ran end to end on one baseline with a correct verdict (a fail and a pass, each confirmed) and a full token breakdown; a wrong Blender path and missing credentials both recorded void. The method also worked as intended: the first real run caught a check that would have failed valid work, before any number was trusted.

**Next (owner's gate):** Phase 1 needs four more tasks and the three MCP baselines wired into the same loop.


## 2026-11-17 · Phase 1: four new tasks, three MCP baselines, the pilot

**Tasks.** Four new hard-surface tasks joined p01: an electronics housing with screw bosses and pilot holes (p02), a pump-dispenser bottle in four parts with a hollow bottle and clearances between every part (p03, the long build), a gable-top carton with a seal fin (p04, the short one), and an earbud case with two different edge radii, a split line and pockets (p05). Each has a hand-built reference and deliberately broken variants: 34 variants across the five tasks, each failing exactly the checks it should.

**New checks, and why.** A *ray probe* fires rays at the model and compares where they land with where the reference surface is; one mechanism measures holes, pocket depths, wall thickness, fillet radii and orientation without caring how the model was built. A *volume* check catches hollow-vs-solid and thickness errors globally. A *shells* check exists because the first draft of p04 showed a floating fin would pass everything: two closed shells are still watertight. And the overlap check now also catches a part sealed entirely inside another, a gap found when a "solid bottle" variant swallowed the dip tube without any surfaces crossing. Volume is unsigned so an inside-out model fails one check (topology), not two.

**Baselines: how each reaches Blender.** Checked from source before building anything (details in research.md). Only Blender's official server runs headless; the community server and Meshwire need a GUI Blender. The official one also runs in GUI here, because its screenshot tools need a window and running it headless would hand it tools that always fail. Each server is pinned, installed into its own isolated Blender profile (the owner's Blender settings are never touched), started per run in a fresh GUI Blender on the starting scene, and driven over MCP with its tool definitions and instructions passed through unchanged. The rig saves the final scene through a private control channel the agent never sees. Screenshot and render images returned by tools reach the model and are counted in the ledger. Meshwire replaced the PoBruno server as the typed baseline: actively maintained and tested on 5.2, where PoBruno has no releases and no commits since July.

**Owner's decisions (2026-11-17):** Meshwire runs with "Allow Python" off, its shipped default, so it's a test of the typed tools. GUI runs are fine, one at a time. The community server's anonymous telemetry is off; it changes nothing the model sees.

**Pilot measured** (Haiku 5.5, low effort; 5 tasks × 4 setups × 3 repeats; 0 voids; $0.49 in total):

| Setup | Pass | Tokens per run | Tokens per pass | Cost | Wall per run |
|---|---|---|---|---|---|
| No MCP | 11/15 | 16,516 | 22,523 | $0.058 | 31 s |
| Blender Lab | 14/15 | 69,798 | 74,784 | $0.093 | 57 s |
| ahujasid | 13/15 | 60,670 | 70,004 | $0.083 | 59 s |
| Meshwire | 5/15 | 333,892 | 1,001,677 | $0.258 | 76 s |

- *Fixed overhead is the story so far.* Tool definitions per turn: 880 tokens with no MCP, about 6,400 for Lab plus 2,000 of its own instructions, about 7,700 for ahujasid, and about 62,000 for Meshwire's 225 tools. Every turn pays them again.
- *Meshwire's failures are mostly one behaviour.* 9 of its 10 fails are the agent trying a Python script first, getting refused, and stopping to ask the user to switch Python on; the tenth is an inside-out carton. Its 5 passes came through the typed tools, at up to 786,000 tokens a run. So with the gate off, the result says more about the shipped default than about typed tools.
- *Every non-Meshwire failure was checked against the model before being trusted.* Real defects: flipped normals on a cap, a pocket 0.5 mm too shallow, a missing roundover, a badly broken earbud case. Three runs fail only on zero-area faces that turned out to be duplicate vertex rings (zero-length edges): invisible in a render, but they break smoothing in a finishing pass. The prompts don't say "no duplicate vertices", so the owner decides whether that's fair.
- *Image tokens* now land in the ledger for the two servers that return images.

**Gate questions.** Haiku passes far above the one-third bar, so the comparison has signal on Haiku. The full matrix (about 30 tasks × 4 setups × 3–5 repeats) prices at roughly $5–10 on Haiku at these rates, so it's affordable as specified.

**Owner's review (2026-11-17):** the verdicts on the review sheet match what the owner sees, so Phase 1's exit check is met. Meshwire is to be tested as a user would run it, with "Allow Python" on, as a new setup `meshwire-py`; the gate-off runs stay on record as `meshwire`. Duplicate vertices get their own controlled test before any prompt changes: the same task with and without one added passage of mesh-hygiene language (a recorded "prompt arm"), so its effect is measured on its own.

**Meshwire as a user runs it** (`meshwire-py`, "Allow Python" on; 15 runs, $0.20): **14 of 15 pass**, at 200,615 tokens per run and 214,945 per pass, 2.8 turns and 49 s on average. Switching Python on took Meshwire from the worst pass rate to among the best. Its cost is still about 3× the other MCP servers' and nearly 10× no-MCP, because its 225 tool definitions (about 62,000 tokens) are resent on every turn whether or not the agent uses them. In practice the agent did almost all its modelling in one Python script and used the typed tools only to validate and clean up. The one fail built the pump at 1,000× scale: it wrote millimetre numbers into a metre scene, printed dimensions of 50 × 50 × 145, and still reported "coordinates are in metres".

**A rig fault found and fixed.** The first try at that cell came back void: the check script hung for ten minutes. The cause was the containment test added this session. It steps a ray forward a fixed 0.1 µm past each hit, and on a model 1,000× too large that step is below single-precision resolution, so the ray never advances. The step now scales with the coordinates and the loop is capped. Checks on that scene finish in 2 s and give a fail on the size checks. Per the rules the void stays void and the cell was rerun.

**Prompt test: does saying "no duplicate vertices" stop them?** Task p05 with no MCP, 20 runs with the task prompt as written and 20 with one added paragraph on mesh hygiene (`clean-mesh` arm). The as-written side includes the 3 pilot runs, which used the same prompt and setup. The as-written runs ran before the clean-mesh runs rather than interleaved; drift is unlikely to affect mesh hygiene, but it's noted.

| Arm | Duplicate-vertex defect | Pass | Other failed checks | Tokens per run | Cost |
|---|---|---|---|---|---|
| As written | 3 of 20 | 14/20 | pocket depth 2, edge roundover 1, base volume 1 | 24,874 | $0.083 |
| Clean-mesh | 0 of 20 | 19/20 | edge roundover 1, base volume 1 | 17,152 | $0.077 |

The defect disappeared with the extra paragraph, but 3 against 0 is not significant at this sample (one-sided Fisher p = 0.12): it's a direction, not a finding. The pass-rate gain (19 vs 14, p = 0.05) is mostly the pocket-depth failures going away, and nothing in the added paragraph is about pockets, so it's probably noise until repeated. The added text didn't raise token cost.

**Prompt test, rerun at 50 per arm** (owner's call; 60 more runs, $0.23, arms alternated run by run this time, 0 voids):

| Arm | Duplicate-vertex defect | Pass | Failed checks, all runs | Tokens per run |
|---|---|---|---|---|
| As written | 7 of 50 | 36/50 | topology 8, edge roundover 6, base volume 5, pocket depth 4, plan corners 3, bbox 4, shells 2, self-intersection 1 | 19,619 |
| Clean-mesh | 0 of 50 | 47/50 | edge roundover 3, base volume 2 | 16,630 |

- **The defect answer is real:** 7 of 50 against 0 of 50, one-sided Fisher p = 0.006. The 30 new runs alone replicate the first 20 (4 of 30 against 0 of 30).
- **The pass rate rose too:** 36 against 47 (p = 0.003). The rise isn't confined to hygiene. Failures on pockets, corners, bounds and separate shells also mostly went away, even though the paragraph mentions none of them. One plausible reading is that asking for a final cleanup makes the agent check its work more carefully overall. That's a hypothesis, not something measured here.
- **Tokens went down, not up:** about 15% fewer per run.
- **Limits:** one task, one setup, one model. Whether it carries to the other tasks and the MCP setups is unmeasured. Adding the same paragraph to every task keeps the setup comparison fair, but it means Phase 2 numbers won't be directly comparable with the pilot's.

**Adopted (owner, 2026-11-17):** the clean-mesh paragraph is now in all five task prompts, before "Tell me when you're done." Runs now record a fingerprint of the exact prompt they saw, and the batch runner only counts runs with the current prompt, so pilot runs never fill Phase 2 cells. Phase 1 is closed. Total API spend across Phase 1: about $1.10.


## 2026-11-17 · Phase 2: starting scenes and the full task set

**Starting scenes.** A task can now start from an approved model instead of an empty scene: `starting_scene = "start.py"` builds it from a task-local script before the agent sees it. The script's text is folded into each run's prompt fingerprint, so editing a starting model can never mix new runs with old ones; for empty-scene tasks the fingerprint is unchanged, so the five existing tasks keep theirs. The smoke test can now start any setup on a task's scene, and all four setups opened a revision scene with its objects intact.

**The first revision task caught its own starting model.** r01 (make a cap 10% taller) needs an "unchanged" variant that fails only the checks the edit should change. On the first proof it also failed the no-touch check: the approved cap's ceiling sat exactly on the bottle's neck. The starting model now has 0.5 mm of clearance. Every revision task now carries an "unchanged" variant for this reason (written into the new `docs/task-authoring.md`).

**The task set is 30.** 25 new tasks, written by four parallel authors to one authoring guide, then re-proved together from scratch: 30 tasks, 224 variants, every one failing exactly the checks it should, every prompt carrying the clean-mesh paragraph.

| Group | Tasks | Examples |
|---|---|---|
| Hard-surface | 13 | p01, p02, p04, p05, compact, lipstick with a 40° tip, perfume flacon, 24-rib cap, wall charger, cream tube, wide-mouth jar, soap bar with a deboss |
| Revision | 8 | cap 10% taller, logo emboss, soften an edge, move and enlarge holes, chamfer, lengthen a pen 20 mm, 12 to 16 ribs, thicken a wall inward |
| Layout | 5 | 3×4 jar grid on a tray, size lineup, radial display with flats facing out, box pyramid, duplicate an approved product into a row |
| Multi-step | 4 (+p03) | flashlight, speaker with an 80-hole grille, toothbrush in its dock, hand coffee grinder |

Revision prompts read like client notes: what changes and what stays, without restating the model's dimensions, because reading the scene is part of what the benchmark should cost. Each revision includes the naive wrong edit as a variant (scale the whole cap, stretch the whole pen, add four ribs without respacing), and the checks catch each one.

**Known check limits, recorded before any run.**
- Volume can't see small features (a grille, a deboss, a port: under 1% of the part), so ray probes carry those.
- A few volume tolerances are tight (0.2–0.5% on revisions where the edit itself is under 1%). A legitimate low-segment fillet could fail one; first runs will show whether that bites.
- The no-touch check doesn't reliably catch two flat faces sitting exactly on each other (found on the box stack). Layout tasks enforce clearances by bounding box instead; the gap stays open.
- The rib cap and the speaker grille have a trap: the obvious boolean build leaves zero-area faces. The prompt's hygiene paragraph covers it, so it's fair, but expect their failures to be hygiene rather than shape.

**Ready for the matrix.** Priced from pilot rates (about $0.029 per task across all four setups), 30 tasks × 4 setups × 3 repeats is about $2.60, plausibly $4–6 because the new prompts and builds are longer; 5 repeats is about $4.40, plausibly $7–10. Wall time is the real cost: about 5 minutes per task across the four setups, so about 8 hours for 3 repeats and 13 for 5, one run at a time. Waiting on the owner's go.

**GUI runs happen on a hidden desktop.** The three MCP setups need a real Blender window, and during the first matrix runs those windows kept appearing on the owner's screen. Three fixes failed, each for a reason worth knowing. Opening without focus still pops the window to the front. Moving it off-screen after launch loses a race: Blender creates and shows its window before it processes any outside request, and it's busy loading for about two seconds. Blender's own start-up scripts, even from the system startup folder, run after the window is already visible, and it ignores a launch request to start minimized. What works is a second Windows desktop: a session can hold several and only the input desktop is ever displayed. GUI Blender now launches on a hidden desktop. It gets a real GPU context and opens maximized at the same 3840 × 2054 size, so Blender Lab's window screenshot is byte-identical to the on-screen one. Zero windows reached the owner's desktop across all three setups. A side benefit: an on-screen window could pick up hover highlights from the owner's mouse, which slightly changed screenshot bytes between runs; the hidden desktop removes that. The first four matrix runs (h01 on all four setups) ran with windows on screen and are kept; nothing the model saw differs.


**The matrix ran.** 30 tasks × 4 setups × 3 repeats on Haiku 5.5 at low effort: 360 runs, 0 voids, $2.77, about 4½ hours of machine time (it was stopped once by Claude Code when the workstation ran short of memory from unrelated work, and resumed where it stopped).

| Setup | Pass | Tokens per run | Tokens per pass | × no-MCP | Cost per run | Wall per run | Turns |
|---|---|---|---|---|---|---|---|
| No MCP | 80/90 | 23,757 | 26,727 | 1.0 | $0.0039 | 32 s | 3.2 |
| ahujasid | 81/90 | 70,536 | 78,374 | 2.9 | $0.0055 | 33 s | 4.7 |
| Blender Lab | 82/90 | 79,573 | 87,337 | 3.3 | $0.0062 | 37 s | 4.4 |
| Meshwire (Python on) | 80/90 | 306,545 | 344,864 | 12.9 | $0.0151 | 39 s | 4.3 |

- **Accuracy is a tie.** 80–82 of 90 on every setup, and the same in each group (hard-surface 33–35/39, revisions 21–22/24, layout 13–15/15, multi-step 10–11/12). On this model and suite, a plugin doesn't buy correctness; it only changes the bill.
- **Where the tokens go.** Tool definitions per turn: 440 (no MCP), about 6,400 (Lab, plus its 2,000-token instructions), about 7,700 (ahujasid), about 62,000 (Meshwire). As a share of input: 90% for Meshwire, 56% for ahujasid, 38% for Lab. With no MCP the largest share is replayed thinking (35%), then the agent's own code (23%) and tool results (20%). Images are negligible: agents almost never asked for a screenshot (14,000 image tokens across all 90 ahujasid runs, none elsewhere).
- **Tokens and dollars tell different-sized stories.** Meshwire is 12.9× no-MCP in tokens but 3.9× in cost, because resent tool definitions are cached and cache reads are cheap. The headline metric (raw or cost-weighted) is still an open owner decision; the report should show both.
- **Revisions cost the most** on every setup (median tokens per run: no MCP 23k, ahujasid 72k, Lab 126k, Meshwire 410k), against 9k–135k for layouts. Reading the existing model is expensive, which is where a structured scene summary should pay off in Phase 3.
- **Wall time is close** (32–39 s per run, excluding the 25–40 s of GUI start-up a user pays once).

**Checking the checks.** Before trusting the failures, the patterns that looked systematic were opened in Blender. On the radial display, three setups failed with identical numbers. The cause was the same wrong model each time: the label flat was trimmed at 15 mm at one end and left 1.4 mm short at the other, so the face is tilted a few degrees. On the hole revision, the 0.2% volume tolerance looked over-tight, but the failing plates had their outer edges drifting by up to 0.4 mm from the approved outline, which the client note said must not change. Both are real defects. Other failures are what Phase 1 saw: models built 1,000× too large, parts left floating, overlapping solids joined without a boolean.

**One judgement for the owner.** Two runs (cream tube on ahujasid, rib revision on Meshwire) ended on the first turn having spent the whole 16,000-token output budget on thinking, with no tool call. They're scored as fails: the cap is the same for every setup, and spending it without acting is the model's behaviour. A harness that let the model continue after hitting the cap would score them differently.

**Phase 3 bar, now concrete.** The best baseline is no MCP at all, at 26,727 tokens per passed task. Half of that is about 13,400. Its biggest line items, replayed thinking and the agent's own code, are where the harness has to save, not tool definitions.

**Headline metric decided (owner, 2026-11-17):** tokens per passed task. Cost is reported alongside, since caching makes dollars understate the gap (Meshwire 12.9× in tokens, 3.9× in cost).

**Where the time goes.** Wall time is 32–39 s per run on every setup, and about 85% of it is the model generating: 27–34 s of model time against 0.3–4 s of tool time. Output streams at a steady ~220 tokens a second on every setup, so time tracks output tokens, and thinking is 56–67% of output. Input size barely shows up in time because resent tool definitions are cached: a 13× token gap becomes only about 20% more time (Meshwire's extra is mostly more thinking, 67% of output, and a slow first turn at 19 s). The one tool cost worth noting is no-MCP's: each call starts a fresh headless Blender, about 1.7 s, or 3.8 s a run. Two Blender Lab calls to its CLI-execution tool hit a 120 s timeout. GUI start-up (25–40 s) is outside these numbers. For Phase 3 this means the same levers cut tokens and time: less thinking per step, fewer turns, and a Blender that stays running between calls.

**Making the baseline a yardstick (owner's go, 2026-11-17).** Four gaps closed before Phase 3:

- **The no-touch check now measures the gap.** It also fails parts whose surfaces rest on each other (smallest vertex-to-surface distance under 0.02 mm), the case the overlap test missed. On the stacked-box task it now catches all six touching pairs instead of two. Every one of the 310 recorded runs on the 14 affected tasks was re-scored; no verdict changed, so the gap never affected a result.
- **Passes audited, not just fails.** One randomly chosen pass per task (30 models) rendered beside its reference. All 30 are geometrically right. The one that looked wrong, a soap bar whose top read as a funnel, measures exactly to spec; the agent had smooth-shaded every face, flat ones included, which is a display setting. The audit also found a review-tool bug: given relative paths, Blender wrote the renders to a folder at the drive root instead of beside each run. Paths are now resolved first.
- **Noise floor measured** and written into `docs/eval-method.md`. Tokens vary widely run to run (within-task spread 0.51 on a log scale), so against the 3-run baseline a harness change has to save about 15–19% to be told from noise. The Phase 3 target of half is far outside that; small single-variable tweaks aren't, and will be grouped.
- **Accuracy is a guardrail, not a claim (owner).** No harder tasks: the current pass rate is the reference, and a drop below about 82% (two standard errors under no-MCP's 88.9%) means something broke.
- **A held-out set** of 8 tasks in `heldout/`, written now, run once for the final claim.

**Owner review of the pass audit (2026-11-17):** no discernible difference between the 30 audited passes and their references. The verdicts stand.

**Phase 2 closed (owner, 2026-11-17).** The two runs that spent the whole output budget thinking stay fails. The baseline report and blog post are deferred until Phase 3 has efficiencies to write about; the journal, case study and `docs/eval-method.md` are the record to draft from.

**Phase 3 ground rules set (owner, 2026-11-17)**, before any harness work: the target is half of no-MCP's tokens per passed task (about 13,400) at a pass rate of 82% or more; model settings stay fixed for the headline, and thinking changes are a separate arm applied to the baseline too; the harness's validation tools stay generic and never see a task's checks; $20 standing spend for iterations. Recorded in `docs/eval-method.md`.

