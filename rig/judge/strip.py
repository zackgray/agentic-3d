"""PNG metadata removal without touching pixels. Blender writes the .blend file's local path into a
tEXt chunk; the page's images must carry no text, time or EXIF chunks at all."""
import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
KEEP = {b"IHDR", b"PLTE", b"tRNS", b"IDAT", b"IEND"}  # everything needed to decode; all else goes
TEXT = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"}


def chunks(data: bytes):
    """Yield (type, payload) for every chunk of a PNG."""
    if data[:8] != SIGNATURE:
        raise ValueError("not a PNG")
    pos = 8
    while pos < len(data):
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + size]
        pos += 12 + size


def strip_png(data: bytes) -> bytes:
    out = [SIGNATURE]
    for kind, payload in chunks(data):
        if kind in KEEP:
            crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
            out.append(struct.pack(">I4s", len(payload), kind) + payload + struct.pack(">I", crc))
    return b"".join(out)


def text_chunks(data: bytes) -> list[str]:
    """The metadata chunk types left in a PNG (empty when it is clean)."""
    return [kind.decode("ascii") for kind, _ in chunks(data) if kind in TEXT or kind not in KEEP]
