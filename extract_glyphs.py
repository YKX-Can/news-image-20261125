# Build-time tool (NOT part of the entry): rasterizes DejaVu Sans glyphs into a
# compact data file that the stdlib-only main.py consumes at runtime.
# Per glyph: [ink_w, ink_h, advance, ink_xoff, ink_yoff, b85(zlib(alpha bytes))]
# Offsets are relative to the pen anchor (left edge, ascender line), PIL 'la' anchor.
import json, zlib, base64
from PIL import ImageFont

FONTS = {
    "reg": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
SIZES = [17, 21, 26, 34, 46, 68]
CHARS = [chr(c) for c in range(32, 127)]

out = {}
for fname, path in FONTS.items():
    for size in SIZES:
        font = ImageFont.truetype(path, size)
        glyphs = {}
        for ch in CHARS:
            mask = font.getmask(ch)
            w, h = mask.size
            adv = font.getlength(ch)
            x0, y0, x1, y1 = font.getbbox(ch)
            raw = bytes(mask)
            enc = base64.b85encode(zlib.compress(raw, 9)).decode()
            glyphs[ch] = [w, h, round(adv, 2), x0, y0, enc]
        asc, desc = font.getmetrics()
        out[f"{fname}{size}"] = {"ascent": asc, "descent": desc, "glyphs": glyphs}
        print("done", fname, size)
with open("/home/hatch/workspace/news-image-20261125/glyphs.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))
print("written")
