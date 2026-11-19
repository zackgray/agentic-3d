# Landscape, 2026-11-16

What exists for agentic 3D modeling as of the project's start. Claims from vendor blogs and aggregators are marked as such; verify against the repos before relying on a figure.

## Blender MCP servers

- **Blender Lab MCP Server** (official, experimental, Blender 5.1+). Installed by the Claude Blender connector. Warns that model-written code runs without guards.
- **ahujasid/mcp-for-blender** (formerly blender-mcp). The best-known community server: Blender addon plus Python MCP server; scene manipulation, viewport screenshots, arbitrary Python.
- **RFingAdam/mcp-blender**: ~218 tools (modeling, materials, sculpting, animation, AI 3D generation), with a render-analyze-refine loop.
- **PoBruno/mcp-blender-agent**: ~216 typed tools, built for validated operations instead of improvised Python.
- **djeada/blender-mcp-server** (27 tools, Python execution, async jobs), **kleer001/blender-mcp**, **loonghao/dcc-mcp-blender**, **hotspoons/blender-agent**.

Two designs: run-any-code plus screenshot, or a large menu of typed operations. Few close the loop with real render critique. None we found treats token cost as a design goal.

## How the three baselines reach Blender (checked 2026-11-17, from source)

- **Blender Lab** (pinned main `dbbf836`, GPL-3.0+): MCP over stdio to a server process, raw TCP to a Blender extension. The only one with a supported headless mode, but its screenshot tools need a window, so the rig runs it in GUI Blender to keep its whole tool list working. Needs Blender's online-mode flag or it refuses to start. 26 tools, mostly "run Python" plus docs search and scene summaries; ships about 4,100 tokens of instructions the client is meant to pass to the model.
- **ahujasid/mcp-for-blender** (pinned `b6a2ce3`, no tags, MIT): single-file add-on, refuses to start headless. 10 tools visible to a plain client, including `look`, which returns a rendered image. Anonymous usage telemetry is on by default; the rig turns it and the update check off. The PyPI name `blender-mcp` now belongs to a different server than this one, so a stray `uvx blender-mcp` silently runs the wrong thing.
- **Meshwire** (RFingAdam, formerly mcp-blender, pinned tag v0.5.0, AGPL-3.0+): 225 typed tools, token-authenticated socket, GUI only (commands run on Blender timers). Its run-any-Python tool is refused until a user switches on "Allow Python"; the rig leaves it off, its default. Chosen over PoBruno/mcp-blender-agent (216 tools), which has no releases and no commits since July.
- All three return results as text except Lab's screenshots and ahujasid's `look`, which return images inline.

## Cinema 4D and Octane

- Maxon shipped a built-in MCP server in Cinema 4D 2026.4 (2026-09-30): free, off by default, tool groups can be restricted, actions go through the undo history. Doesn't run in command-line rendering.
- Community: kumoproductions/mcp-cinema4d, ttiimmaacc/cinema4d-mcp.
- Octane: no official MCP server found. One community bridge (nobulart/octane-mcp) targets Octane X through Lua. Octane scripting is mainly Lua; its C4D material nodes are poorly documented for code.

## Research systems

- **LL3M** (arXiv 2508.08228): multi-agent Blender code generation; planning, retrieval over Blender API docs (BlenderRAG), coding, debugging, visual self-critique, user feedback.
- **BlenderAlchemy**: a vision model iteratively refines procedural programs and materials.
- **BlenderLLM**: Qwen2.5-Coder-7B fine-tuned on BlendNet (12k instruction-script pairs). Apache-2.0.
- **BlenderRAG** (arXiv 2605.00632): retrieval-augmented Blender code synthesis.

## CAD-as-code benchmarks

- **CadQueryEval** (May 2026): 25 tasks; the top frontier model scored 0.80, most models 0.20–0.64.
- **BenchCAD** (arXiv 2605.10865): 17,900 verified CadQuery programs, 106 industrial part families, scored by voxel IoU from four views.
- **Text2CAD-Bench** (arXiv 2605.18430): CadQuery beats command-sequence representations; cites fine-tuning on 170K text–CadQuery pairs improving with scale.
- **CadBench** (arXiv 2605.10873), **CADWorld** (arXiv 2609.16251, long-horizon computer-use CAD), **CADENA** (arXiv 2608.00799).
- No Blender-specific benchmark found. That gap is part of what this project fills.

## Open fine-tunes

- **3DCodeVerse** LoRAs for Qwen3.6-27B and Qwen3.8-27B (Blender Python, CadQuery, OpenSCAD, GLSL, three.js). No evaluation numbers on the cards: test before training our own.
- **CadQuery-Qwen3.5-4B-LoRA** (community), with a notebook and reported results not yet checked.

## Generative meshes

- **TRELLIS 2** (MIT): image-to-3D, ~16–24 GB VRAM.
- **Hunyuan3D 2**: geometry plus texture, ~16 GB; check its license before commercial use.
- **TripoSR**: fast, 6–8 GB. **Modly**: a local desktop front end for several of these.

## Sources

- https://dev.to/_903a3934b362f0afe2a8/blender-mcp-servers-for-ai-agents-october-2026-which-ones-control-the-scene-and-which-one-3ica
- https://voyager.so/blog/blender-mcp
- https://www.strayspark.studio/blog/blender-mcp-ai-assisted-3d-modeling-step-by-step-2026
- https://www.cgchannel.com/2026/09/maxon-releases-cinema-4d-2026-4-with-a-new-mcp-server/
- https://help.maxon.net/c4d/2026/en-us/Content/html/What_is_an_MCP_Server.html
- https://glama.ai/mcp/servers/nobulart/octane-mcp
- https://www.alphaxiv.org/abs/2508.08228
- https://github.com/FreedomIntelligence/BlenderLLM
- https://arxiv.org/pdf/2605.00632
- https://github.com/danwahl/cadqueryeval
- https://arxiv.org/pdf/2605.10865
- https://arxiv.org/html/2605.18430v1
- https://arxiv.org/html/2605.10873v2
- https://arxiv.org/pdf/2609.16251
- https://huggingface.co/3dcodeverse/3dcodeverse-qwen3.6-27b-lora
- https://huggingface.co/mc9901708/CadQuery-Qwen3.5-4B-LoRA
- https://tspi.at/2026/05/01/opensource3dassets.html
