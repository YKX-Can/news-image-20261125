#!/usr/bin/env python3
"""make.fun news-image entry: renders a one-image summary of 2026-11-25 world news.

Pure Python 3 standard library. Reads two data files shipped in this repo:
  - glyphs.json : pre-rasterized font glyphs (alpha bitmaps + metrics)
  - news.json   : the day's stories (compiled from public reports of 2026-11-25)
Writes the image to /output/entry.png (falls back to ./output/entry.png).
Deterministic: same inputs always produce byte-identical output.
"""
import base64
import json
import os
import struct
import zlib

W, H = 1024, 1024

# ---------- palette ----------
PAPER = (246, 241, 231)
INK = (18, 32, 54)
INK_SOFT = (52, 68, 92)
CARD = (255, 255, 255)
BORDER = (216, 205, 178)
RED = (178, 52, 40)
GOLD = (214, 144, 43)
HERO_BG = (18, 32, 54)
HERO_SUB = (198, 210, 226)
CHIP_COLORS = {
    "SPACE": (49, 81, 127),
    "SPORT": (46, 125, 79),
    "ASIA": (122, 78, 140),
    "MIDDLE": (160, 58, 46),
    "SECURITY": (74, 78, 87),
    "BUSINESS": (31, 110, 106),
    "TECH": (150, 102, 15),
}

# ---------- framebuffer ----------
fb = bytearray(W * H * 3)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = color[0]
        fb[i + 1] = color[1]
        fb[i + 2] = color[2]


def blend_px(x, y, color, a):
    if 0 <= x < W and 0 <= y < H and a > 0:
        i = (y * W + x) * 3
        if a >= 255:
            fb[i] = color[0]
            fb[i + 1] = color[1]
            fb[i + 2] = color[2]
        else:
            inv = 255 - a
            fb[i] = (color[0] * a + fb[i] * inv) // 255
            fb[i + 1] = (color[1] * a + fb[i + 1] * inv) // 255
            fb[i + 2] = (color[2] * a + fb[i + 2] * inv) // 255


def fill_rect(x, y, w, h, color):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        fb[i:i + len(row)] = row


def rect_outline(x, y, w, h, color, t=2):
    fill_rect(x, y, w, t, color)
    fill_rect(x, y + h - t, w, t, color)
    fill_rect(x, y, t, h, color)
    fill_rect(x + w - t, y, t, h, color)


def fill_circle(cx, cy, r, color):
    r2 = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        dx = int((r2 - dy * dy) ** 0.5)
        fill_rect(cx - dx, yy, dx * 2 + 1, 1, color)


def fill_triangle(x0, y0, x1, y1, x2, y2, color):
    minx, maxx = max(0, min(x0, x1, x2)), min(W - 1, max(x0, x1, x2))
    miny, maxy = max(0, min(y0, y1, y2)), min(H - 1, max(y0, y1, y2))
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            w0 = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
            w1 = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
            w2 = 1 - w0 - w1
            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                set_px(xx, yy, color)


def fill_ellipse(cx, cy, rx, ry, color):
    for yy in range(cy - ry, cy + ry + 1):
        dy = (yy - cy) / ry
        dx = int(rx * (1 - dy * dy) ** 0.5)
        fill_rect(cx - dx, yy, dx * 2 + 1, 1, color)


def thick_line(x0, y0, x1, y1, color, t=3):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(1, t // 2)
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        fill_circle(x, y, r, color)


# ---------- text ----------
_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "glyphs.json"), "r") as f:
    GLYPHS = json.load(f)
_glyph_cache = {}


def glyph(font_key, ch):
    key = (font_key, ch)
    g = _glyph_cache.get(key)
    if g is None:
        entry = GLYPHS[font_key]["glyphs"].get(ch)
        if entry is None:
            entry = GLYPHS[font_key]["glyphs"]["?"]
        w, h, adv, xo, yo, enc = entry
        raw = zlib.decompress(base64.b85decode(enc.encode())) if enc else b""
        g = (w, h, adv, xo, yo, raw)
        _glyph_cache[key] = g
    return g


def text_width(font_key, s):
    total = 0.0
    for ch in s:
        total += glyph(font_key, ch)[2]
    return total


def draw_text(x, y_top, s, font_key, color):
    pen = float(x)
    for ch in s:
        w, h, adv, xo, yo, raw = glyph(font_key, ch)
        if w and h and raw:
            gx, gy = int(round(pen)) + xo, y_top + yo
            for row in range(h):
                base = row * w
                yy = gy + row
                if yy < 0 or yy >= H:
                    continue
                for col in range(w):
                    a = raw[base + col]
                    if a:
                        blend_px(gx + col, yy, color, a)
        pen += adv
    return pen


def draw_text_center(cx, y_top, s, font_key, color):
    w = text_width(font_key, s)
    draw_text(int(cx - w / 2), y_top, s, font_key, color)


def wrap(s, font_key, max_w):
    words = s.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if text_width(font_key, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def chip_color(chip_text):
    for key, color in CHIP_COLORS.items():
        if chip_text.startswith(key):
            return color
    return INK_SOFT


def draw_chip(x, y, text, color, font_key="bold17"):
    w = int(text_width(font_key, text)) + 22
    fill_rect(x, y, w, 26, color)
    draw_text(x + 11, y + 4, text, font_key, (255, 255, 255))
    return w


# ---------- scene ----------
def draw_rocket(cx, cy):
    # stars (all inside the hero card)
    for sx, sy, r in [(688, 246, 3), (948, 238, 2), (700, 330, 2),
                      (952, 352, 3), (742, 392, 2), (905, 415, 2)]:
        fill_circle(sx, sy, r, (240, 220, 160))
    # flame
    fill_triangle(cx - 16, cy + 78, cx + 16, cy + 78, cx, cy + 118, GOLD)
    fill_triangle(cx - 9, cy + 78, cx + 9, cy + 78, cx, cy + 96, RED)
    # fins
    fill_triangle(cx - 20, cy + 30, cx - 48, cy + 82, cx - 20, cy + 82, RED)
    fill_triangle(cx + 20, cy + 30, cx + 48, cy + 82, cx + 20, cy + 82, RED)
    # body
    fill_rect(cx - 20, cy - 55, 40, 137, (238, 240, 244))
    fill_ellipse(cx, cy - 55, 20, 34, (238, 240, 244))
    fill_ellipse(cx, cy - 78, 12, 16, RED)
    # window
    fill_circle(cx, cy - 18, 10, (49, 81, 127))
    fill_circle(cx, cy - 18, 6, (150, 190, 230))
    # band
    fill_rect(cx - 20, cy + 52, 40, 8, GOLD)


def main():
    with open(os.path.join(_here, "news.json"), "r") as f:
        news = json.load(f)

    fill_rect(0, 0, W, H, PAPER)
    M = 46  # margin

    # header
    draw_text(M, 34, "ONE DAY | ONE IMAGE | THE WHOLE STORY", "bold17", RED)
    draw_text(M, 58, "THE WORLD TODAY", "bold68", INK)
    draw_text(M, 138, news["date_line"], "bold26", INK)
    fill_rect(M, 178, W - 2 * M, 4, INK)
    fill_rect(M, 186, W - 2 * M, 1, BORDER)

    # hero card
    hy, hh = 202, 244
    fill_rect(M, hy, W - 2 * M, hh, HERO_BG)
    fill_rect(M, hy, 6, hh, GOLD)
    draw_rocket(W - M - 118, hy + 100)
    tx = M + 30
    draw_chip(tx, hy + 24, news["hero"]["chip"], GOLD)
    lines = wrap(news["hero"]["headline"], "bold34", 600)
    ly = hy + 64
    for ln in lines[:2]:
        draw_text(tx, ly, ln, "bold34", (250, 248, 242))
        ly += 44
    dlines = wrap(news["hero"]["detail"], "reg21", 596)
    ly += 4
    for ln in dlines[:3]:
        draw_text(tx, ly, ln, "reg21", HERO_SUB)
        ly += 29

    # story grid: 2 cols x 3 rows
    stories = news["stories"][:6]
    gx, gy = M, hy + hh + 14
    cw = (W - 2 * M - 14) // 2
    ch_h, gap = 148, 12
    for idx, st in enumerate(stories):
        col, row = idx % 2, idx // 2
        x = gx + col * (cw + gap)
        y = gy + row * (ch_h + gap)
        fill_rect(x, y, cw, ch_h, CARD)
        rect_outline(x, y, cw, ch_h, BORDER, 1)
        fill_rect(x, y, cw, 4, chip_color(st["chip"]))
        draw_chip(x + 14, y + 13, st["chip"], chip_color(st["chip"]))
        hlines = wrap(st["headline"], "bold21", cw - 28)
        ly = y + 46
        for ln in hlines[:2]:
            draw_text(x + 14, ly, ln, "bold21", INK)
            ly += 26
        dlines = wrap(st["detail"], "reg17", cw - 28)
        for ln in dlines[:2]:
            draw_text(x + 14, ly + 3, ln, "reg17", INK_SOFT)
            ly += 22

    # ticker
    ty = gy + 3 * ch_h + 2 * gap + 12
    fill_rect(M, ty, W - 2 * M, 48, INK)
    tlines = wrap(news["ticker"], "reg17", W - 2 * M - 32)
    ly = ty + 7
    for ln in tlines[:2]:
        draw_text_center(W // 2, ly, ln, "reg17", (240, 234, 218))
        ly += 22

    # footer
    draw_text_center(W // 2, ty + 60, "Compiled from public reports of November 25, 2026. Every event occurred or was first reported on this date.", "reg17", INK_SOFT)

    # ---------- write PNG ----------
    raw = bytearray()
    row_bytes = W * 3
    for yy in range(H):
        raw.append(0)
        raw += fb[yy * row_bytes:(yy + 1) * row_bytes]

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    out_dir = "/output"
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
        with open(out_path, "wb") as f:
            f.write(png)
    except OSError:
        out_dir = os.path.join(_here, "output")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
        with open(out_path, "wb") as f:
            f.write(png)
    print("wrote", out_path, len(png), "bytes")


if __name__ == "__main__":
    main()
