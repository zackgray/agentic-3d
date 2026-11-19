"""The owner's review sheet: every run's final model from four views, beside the task's reference
model, its verdict, failed checks and cost. Local only; agents never see it. Free (no model calls).

    python -m rig.review                 # every run under runs/
    python -m rig.review runs/2026*p04*  # a subset

Writes runs/_review/index.html. Renders are cached next to each run (runs/<id>/review/).
"""
import glob
import html
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from .blender import blender_path, run_script
from .task import load_task
from .verify_checks import build

ROOT = Path(__file__).resolve().parent.parent
RUNS, OUT = ROOT / "runs", ROOT / "runs" / "_review"
VIEWS = ("three_quarter", "front", "side", "top")


def render(exe, blend: Path, out: Path) -> None:
    if (out / "top.png").is_file() or (out / "EMPTY").is_file() or not blend.is_file():
        return
    proc = run_script(exe, "review_render.py", [str(out)], blend=blend, timeout=300)
    if proc.returncode != 0:
        print(f"render failed for {blend}: {proc.stderr[-500:]}")


def reference(exe, task_id: str) -> Path:
    out = RUNS / "_reference" / task_id
    if not (out / "top.png").is_file():
        out.mkdir(parents=True, exist_ok=True)
        blend = build(exe, load_task(ROOT / "tasks" / task_id), "good", out)
        render(exe, blend, out)
    return out


def failed_summary(rec: dict) -> str:
    bits = []
    for c in rec.get("checks", {}).get("checks", []):
        if c["passed"]:
            continue
        d = c["detail"]
        if "probes" in d:
            bad = [f"{p['name']}: {p['hit_mm']} vs {p['expected_mm']} mm" for p in d["probes"] if not p["passed"]]
            bits.append(f"<b>{c['check']}</b> — " + html.escape("; ".join(bad)))
        else:
            bits.append(f"<b>{c['check']}</b> — {html.escape(json.dumps(d))[:240]}")
    return "<br>".join(bits) or "—"


def imgs(folder: Path) -> str:
    if (folder / "EMPTY").is_file():
        return '<div class="empty">no mesh objects</div>'
    return "".join(f'<img src="{os.path.relpath(folder / (v + ".png"), OUT).replace(os.sep, "/")}" title="{v}">'
                   for v in VIEWS if (folder / (v + ".png")).is_file())


CSS = """
:root{--bg:#fafaf8;--fg:#1d1d1b;--mut:#6b6b66;--line:#e2e1dc;--card:#fff;--pass:#1f7a3f;--fail:#b3261e;--void:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--mut:#a3a29c;--line:#30302d;--card:#1f1f1d;--pass:#5fc27e;--fail:#ff8a80;--void:#e0c050}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:24px 16px;max-width:1500px;margin:auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:32px 0 8px}p.mut,.mut{color:var(--mut)}
.row{display:grid;grid-template-columns:220px 1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px;margin:8px 0}
.row img{width:150px;height:150px;border-radius:4px;margin:0 6px 6px 0;background:#3a3a3a}
.v{font-weight:700;text-transform:uppercase}.pass{color:var(--pass)}.fail{color:var(--fail)}.void{color:var(--void)}
.empty{padding:20px;color:var(--mut)}.fails{font-size:12px;margin-top:6px}
@media (max-width:700px){.row{grid-template-columns:1fr}.row img{width:30%;height:auto}}
"""


def main(argv=None) -> int:
    patterns = (argv if argv is not None else sys.argv[1:]) or [str(RUNS / "*")]
    # resolved: Blender reads a relative output path against the drive root, not the working directory
    dirs = sorted({Path(p).resolve() for pat in patterns for p in glob.glob(pat)
                   if (Path(p) / "result.json").is_file() and not Path(p).name.startswith("_")})
    exe = blender_path()
    by_task = defaultdict(list)
    for d in dirs:
        rec = json.loads((d / "result.json").read_text(encoding="utf-8"))
        render(exe, d / "scene.blend", d / "review")
        by_task[rec["task"]].append((d, rec))
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
             f"<title>Run review</title><style>{CSS}</style><h1>Run review</h1>"
             f"<p class=mut>{len(dirs)} runs. Each model from three-quarter, front, side and top; colours "
             f"tell objects apart. Does each verdict match what you see?</p>"]
    for task_id in sorted(by_task):
        ref = reference(exe, task_id)
        parts.append(f"<h2>{html.escape(task_id)}</h2><div class=row><div><b>Reference</b>"
                     f"<div class=mut>what a pass looks like</div></div><div>{imgs(ref)}</div></div>")
        for d, rec in sorted(by_task[task_id], key=lambda x: (x[1]["setup"], x[1]["run_id"])):
            m, v = rec.get("metrics", {}), rec.get("verdict") or "void"
            stats = (f"{m.get('turns', '?')} turns · {m.get('total_tokens', '?'):,} tokens · ${m.get('cost_usd', '?')}"
                     if m else "")
            note = html.escape(rec.get("void_reason", "")) if v == "void" else failed_summary(rec)
            parts.append(f"<div class=row><div><b>{html.escape(rec['setup'])}</b> <span class='v {v}'>{v}</span>"
                         f"<div class=mut>{stats}</div><div class=mut>{html.escape(d.name[:15])}</div>"
                         f"<div class=fails>{note}</div></div><div>{imgs(d / 'review')}</div></div>")
    (OUT / "index.html").write_text("\n".join(parts), encoding="utf-8")
    print(f"review sheet: {OUT / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
