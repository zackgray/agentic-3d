"""Builds the README figures from recorded runs. Free: Blender locally, no model calls.

    python -m rig.figures chart     # docs/images/tokens-per-pass.svg (figures from the journals)
    python -m rig.figures gallery   # docs/images/heldout4-h7.png: h7's passing models on heldout4

The chart's numbers are the measured results quoted in docs/journal*.md, not recomputed here;
the gallery renders the first passing h7 run of each heldout4 task with the review renderer.
"""
import json
import sys
from pathlib import Path

from .blender import blender_path, run_script

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "docs" / "images"

# Development suite, 30 tasks x 3 runs, Claude Haiku 5.5 at low effort: tokens per passed task.
DEV = [
    ("Meshwire MCP (Python on)", 344_864, "80/90", "existing"),
    ("Blender Lab MCP", 87_337, "82/90", "existing"),
    ("ahujasid blender-mcp", 78_374, "81/90", "existing"),
    ("No MCP (agent writes scripts)", 26_727, "80/90", "existing"),
    ("This harness, h6", 9_912, "81/90", "harness"),
    ("This harness, h7", 6_489, "86/90", "harness"),
]
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
FILL = {"existing": "#8a8984", "harness": "#2a78d6"}


def chart() -> Path:
    w, left, right, top, row, bar = 860, 250, 150, 64, 40, 22
    h = top + row * len(DEV) + 52
    scale = (w - left - right) / max(v for _, v, _, _ in DEV)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           f'<rect width="{w}" height="{h}" rx="8" fill="{SURFACE}"/>',
           f'<text x="24" y="30" font-size="17" font-weight="600" fill="{INK}">Tokens per passed task, '
           f'30 modelling tasks x 3 runs</text>',
           f'<text x="24" y="50" font-size="13" fill="{MUTED}">Claude Haiku 5.5, low effort. '
           f'Lower is better; pass counts on the right.</text>']
    for tick in range(0, 350_001, 50_000):
        x = left + tick * scale
        out.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{top + row * len(DEV) - 10}" '
                   f'stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{x:.1f}" y="{top + row * len(DEV) + 8}" font-size="11" fill="{MUTED}" '
                   f'text-anchor="middle">{tick // 1000}k</text>')
    for i, (name, value, passes, kind) in enumerate(DEV):
        y = top + i * row
        wbar = max(value * scale, 3)
        out.append(f'<text x="{left - 12}" y="{y + bar / 2 + 5}" font-size="13" fill="{INK}" '
                   f'text-anchor="end">{name}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{wbar:.1f}" height="{bar}" rx="4" fill="{FILL[kind]}">'
                   f'<title>{name}: {value:,} tokens per passed task, {passes} passed</title></rect>')
        out.append(f'<text x="{left + wbar + 8:.1f}" y="{y + bar / 2 + 5}" font-size="13" fill="{INK}">'
                   f'{value:,}</text>')
        out.append(f'<text x="{w - 24}" y="{y + bar / 2 + 5}" font-size="13" fill="{MUTED}" '
                   f'text-anchor="end">{passes}</text>')
    ly = h - 16
    for j, (kind, label) in enumerate((("existing", "Existing setups"), ("harness", "This harness"))):
        x = left + j * 160
        out.append(f'<rect x="{x}" y="{ly - 10}" width="12" height="12" rx="2" fill="{FILL[kind]}"/>')
        out.append(f'<text x="{x + 18}" y="{ly}" font-size="12" fill="{MUTED}">{label}</text>')
    out.append("</svg>")
    IMAGES.mkdir(parents=True, exist_ok=True)
    path = IMAGES / "tokens-per-pass.svg"
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def gallery() -> Path:
    from PIL import Image, ImageDraw, ImageFont
    exe = blender_path()
    tiles = []
    for task in sorted((ROOT / "heldout4").glob("w0*")):
        runs = sorted((ROOT / "runs").glob(f"*_{task.name}_harness_*"))
        run = next((r for r in runs if json.loads((r / "result.json").read_text(encoding="utf-8"))
                    ["verdict"] == "pass"), None)
        if run is None:
            continue
        out = run / "review"
        if not (out / "three_quarter.png").is_file():
            run_script(exe, "review_render.py", [str(out)], blend=run / "scene.blend", timeout=300)
        tiles.append((task.name.split("-", 1)[1].replace("-", " "), Image.open(out / "three_quarter.png")))
    size, cols, label = 320, 4, 30
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, rows * (size + label)), SURFACE)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("segoeui.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for k, (name, img) in enumerate(tiles):
        x, y = (k % cols) * size, (k // cols) * (size + label)
        sheet.paste(img.convert("RGB").resize((size, size)), (x, y))
        draw.text((x + 10, y + size + 4), name, fill=INK, font=font)
    path = IMAGES / "heldout4-h7.png"
    sheet.save(path, optimize=True)
    return path


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "chart"
    print({"chart": chart, "gallery": gallery}[what]())
