# The World Today — one-image news summary for 2026-11-25

Entry for the make.fun bounty **“Sum up 25 November's world news in one image”**
(https://make.fun/bounty/news-image-20261125).

## What it does

`main.py` is a **pure Python 3 standard-library** program. It renders a
1024×1024 PNG newspaper front page that summarizes the world news of
**Wednesday, November 25, 2026**, and writes it to `/output/entry.png`
(falling back to `./output/entry.png` when `/output` is not writable).

The front page carries nine stories chosen for breadth across regions and
fields, all of which occurred or were first reported on 2026-11-25:

- **Space / China** — Shenzhou-24 crewed spaceship lifts off from Jiuquan
- **Sport / Americas** — FIFA confirms four hosts for the 2031 Women's World Cup, expanded to 48 teams
- **Asia / Infrastructure** — Vietnam's $67B high-speed rail moves ahead
- **Middle East** — Iran court orders the US to pay $290 billion
- **Security / Asia-Pacific** — Russian bombers fly 10 hours over the Sea of Japan
- **Business / China–US** — Boeing wins its first big China order in nine years (50 × 737-8 for Xiamen Airlines)
- **Tech / Standards** — China leads 78 new global AI standards
- Plus a ticker: PBOC's 800B + 500B yuan liquidity combo, and China's fuel price cut

## How it works

No third-party packages, no network, no system fonts at runtime:

- `news.json` — the day's stories (headline, category, one-line detail),
  compiled from public reports of 2026-11-25.
- `glyphs.json` — pre-rasterized font glyphs (alpha bitmaps + metrics for
  printable ASCII, two weights × six sizes). `extract_glyphs.py` is the
  build-time tool that generated it from DejaVu Sans; it is **not** used
  at runtime.
- `main.py` — a small software renderer: framebuffer, shapes, alpha-blended
  text, word wrap, and a deterministic PNG writer (fixed zlib level, no
  timestamps). Two runs produce byte-identical output
  (verified: SHA-256 `372881aae7048d59cc292969d996078406a6d4886c82c82f1ce2d108eec70901`,
  103,990 bytes, 1024×1024).

## Run it

```bash
python3 main.py        # writes /output/entry.png
```

## License

MIT. Font glyphs derive from DejaVu Sans (DejaVu Fonts License, public domain–style).
