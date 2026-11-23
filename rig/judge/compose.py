"""Pillow work: four views into one 2x2 sheet, and clean re-encodes. Every PNG written goes through
strip.strip_png, and a fresh Image is built from pixels only, so no source metadata can ride along."""
import io
from pathlib import Path

from PIL import Image, ImageDraw

from . import VIEWS
from .strip import strip_png, text_chunks

BACKGROUND = (230, 230, 230)
GAP = 8


def _flat(path: Path) -> Image.Image:
    """The image's pixels on a light grey ground, as a new RGB image carrying no info dict."""
    with Image.open(path) as src:
        rgba = src.convert("RGBA")
    ground = Image.new("RGB", rgba.size, BACKGROUND)
    ground.paste(rgba, mask=rgba.split()[3])
    return ground


def missing_views(folder: Path) -> list[str]:
    return [v for v in VIEWS if not (Path(folder) / (v + ".png")).is_file()]


def composite(folder: Path) -> Image.Image:
    """front, side on top; three_quarter, top below. Cells take the first view's size."""
    tiles = [_flat(Path(folder) / (v + ".png")) for v in VIEWS]
    w, h = tiles[0].size
    sheet = Image.new("RGB", (2 * w + GAP, 2 * h + GAP), (60, 60, 60))
    draw = ImageDraw.Draw(sheet)
    for i, (name, tile) in enumerate(zip(VIEWS, tiles)):
        if tile.size != (w, h):
            tile.thumbnail((w, h))
            cell = Image.new("RGB", (w, h), BACKGROUND)
            cell.paste(tile, ((w - tile.width) // 2, (h - tile.height) // 2))
            tile = cell
        x, y = (i % 2) * (w + GAP), (i // 2) * (h + GAP)
        sheet.paste(tile, (x, y))
        draw.text((x + 6, y + 4), name.replace("_", " "), fill=(90, 90, 90))
    return sheet


def write_png(image: Image.Image, target: Path) -> None:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    data = strip_png(buf.getvalue())
    left = text_chunks(data)
    if left:
        raise ValueError("metadata survived stripping in %s: %s" % (target.name, left))
    Path(target).write_bytes(data)


def write_photo(src: Path, target: Path) -> None:
    write_png(_flat(src), target)
