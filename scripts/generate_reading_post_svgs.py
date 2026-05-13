#!/usr/bin/env python3
"""Generate minimalist paginated SVG reading cards from assets/reading-post/source.md."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "reading-post" / "source.md"
OUT_DIR = ROOT / "assets" / "reading-post"

WIDTH = 1242
HEIGHT = 2208
MARGIN_X = 108
MARGIN_TOP = 120
MARGIN_BOTTOM = 120
FONT_SIZE = 34
LINE_HEIGHT = 56
PARA_GAP = 22
MAX_WEIGHT = 30.0

FONT_FAMILY = "'Noto Serif CJK SC', 'Source Han Serif SC', 'Songti SC', 'SimSun', serif"


def char_weight(ch: str) -> float:
    if ch == " ":
        return 0.45
    if ch == "\t":
        return 1.8
    if ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        return 0.58
    if ch in ".,:;!?()[]{}<>+-=/\\|_'\"`~":
        return 0.35
    return 1.0


def wrap_line(line: str) -> list[str]:
    if not line:
        return [""]
    chunks: list[str] = []
    current = ""
    weight = 0.0
    for ch in line:
        w = char_weight(ch)
        if current and weight + w > MAX_WEIGHT:
            chunks.append(current.rstrip())
            current = ch.lstrip()
            weight = char_weight(current) if current else 0.0
        else:
            current += ch
            weight += w
    if current or not chunks:
        chunks.append(current.rstrip())
    return chunks


def paragraph_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    for para in re.split(r"\n\s*\n", text.rstrip("\n")):
        lines: list[str] = []
        for raw_line in para.splitlines():
            lines.extend(wrap_line(raw_line))
        blocks.append(lines)
    return blocks


def paginate(blocks: list[list[str]]) -> list[list[tuple[str, bool]]]:
    max_lines = int((HEIGHT - MARGIN_TOP - MARGIN_BOTTOM) / LINE_HEIGHT)
    pages: list[list[tuple[str, bool]]] = []
    page: list[tuple[str, bool]] = []
    used = 0

    def new_page() -> None:
        nonlocal page, used
        if page:
            pages.append(page)
        page = []
        used = 0

    for block_index, block in enumerate(blocks):
        needed = len(block) + (1 if page else 0)
        if page and needed <= max_lines - used:
            page.append(("", True))
            used += 1
        elif page and len(block) <= max_lines:
            new_page()

        for i, line in enumerate(block):
            if used >= max_lines:
                new_page()
            page.append((line, False))
            used += 1
        if block_index == len(blocks) - 1:
            new_page()
    return pages


def svg_page(lines: list[tuple[str, bool]], index: int, total: int) -> str:
    text_nodes = []
    y = MARGIN_TOP
    for line, is_gap in lines:
        if is_gap:
            y += PARA_GAP
            continue
        text_nodes.append(
            f'<text x="{MARGIN_X}" y="{y}" class="body" xml:space="preserve">{html.escape(line)}</text>'
        )
        y += LINE_HEIGHT
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <defs>
    <filter id="paperShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="14" stdDeviation="22" flood-color="#d9d0c4" flood-opacity="0.28"/>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="#f6f0e8"/>
  <rect x="54" y="54" width="1134" height="2100" rx="46" fill="#fffdf8" filter="url(#paperShadow)"/>
  <rect x="82" y="82" width="1078" height="2044" rx="34" fill="none" stroke="#eadfce" stroke-width="2"/>
  <style>
    .body {{ font-family: {FONT_FAMILY}; font-size: {FONT_SIZE}px; fill: #302820; letter-spacing: 0.8px; }}
  </style>
  {chr(10).join(text_nodes)}
</svg>
'''


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    blocks = paragraph_blocks(text)
    pages = paginate(blocks)
    for old in OUT_DIR.glob("page-*.svg"):
        old.unlink()
    for i, lines in enumerate(pages, start=1):
        (OUT_DIR / f"page-{i:02d}.svg").write_text(svg_page(lines, i, len(pages)), encoding="utf-8")
    print(f"Generated {len(pages)} SVG pages in {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
