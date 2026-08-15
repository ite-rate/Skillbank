#!/usr/bin/env python3
"""
cover_canvas.py — Render cover.pdf from tokens.json via ReportLab Canvas.

This is the Playwright-free fallback for environments (especially cloud Linux)
where Node.js / Chromium / Playwright are not installed.  It draws in the same
794×1123 design space as the HTML→Playwright path, then scales to an A4 PDF so
merge.py and downstream steps are agnostic to which renderer was used.

CJK font handling is delegated to pdf_render_body.py's registration logic —
the same _CJK_FONT_CANDIDATES list and _patch_cjk_tokens() function are reused
so that Chinese / Japanese / Korean titles render as real glyphs, not boxes.

Usage:
    python3 cover_canvas.py --tokens tokens.json --out cover.pdf
    python3 cover_canvas.py --tokens tokens.json --output cover.pdf

Exit codes: 0 success, 1 bad args/missing file, 3 render error
"""

import argparse
import json
import os
import sys
import textwrap

# ── ReportLab dependency bootstrap (same pattern as render_body.py) ────────────
import importlib.util
if importlib.util.find_spec("reportlab") is None:
    import subprocess
    cmd = [sys.executable, "-m", "pip", "install", "-q", "reportlab"]
    try:
        subprocess.check_call(cmd[:4] + ["--break-system-packages"] + cmd[4:])
    except subprocess.CalledProcessError:
        subprocess.check_call(cmd)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics

# ── Import CJK helpers from render_body.py (same directory) ───────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
try:
    from pdf_render_body import (
        _CJK_FONT_CANDIDATES,
        _try_register_ttf,
        _patch_cjk_tokens,
        _has_cjk,
    )
except Exception:
    # If import fails for any reason, define no-op stubs so the script still
    # runs (without CJK support) instead of crashing.
    _CJK_FONT_CANDIDATES = []
    def _try_register_ttf(name, path):  # noqa: E704
        return False
    def _patch_cjk_tokens(tokens, regular, bold):  # noqa: E704
        pass
    def _has_cjk(text):  # noqa: E704
        return False


# ══════════════════════════════════════════════════════════════════════════════
# CJK font setup for cover
# ══════════════════════════════════════════════════════════════════════════════

_CJK_REG_ALIAS  = "CJKFont"
_CJK_BOLD_ALIAS = "CJKFontBold"


def _setup_cover_cjk(tokens: dict) -> None:
    """Detect CJK and patch tokens with a CJK-capable font for cover rendering.

    Mirrors the logic in render_body.py's _ensure_cjk_fonts() but tailored
    for the cover (no content.json — we only check title/author/subtitle).
    """
    title_text = tokens.get("title", "")
    author     = tokens.get("author", "")
    subtitle   = tokens.get("subtitle", "")
    doc_type   = tokens.get("doc_type", "")

    if not _has_cjk(title_text + " " + author + " " + subtitle + " " + doc_type):
        return

    for reg_path, bold_path in _CJK_FONT_CANDIDATES:
        if not _try_register_ttf(_CJK_REG_ALIAS, reg_path):
            continue
        effective_bold = bold_path if (bold_path and os.path.exists(bold_path)) else reg_path
        if not _try_register_ttf(_CJK_BOLD_ALIAS, effective_bold):
            _try_register_ttf(_CJK_BOLD_ALIAS, reg_path)
        _patch_cjk_tokens(tokens, _CJK_REG_ALIAS, _CJK_BOLD_ALIAS)
        tokens["cjk_font_path"] = reg_path
        print(f"[INFO] CJK font registered for cover: {reg_path}", file=sys.stderr)
        return

    # Fallback: ReportLab built-in CID font
    try:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        _patch_cjk_tokens(tokens, "STSong-Light", "STSong-Light")
        print("[INFO] CJK fallback: STSong-Light (CID font)", file=sys.stderr)
    except Exception:
        print("[WARN] No CJK font available — cover may show boxes.", file=sys.stderr)


# ══════════════════════════════════════════════════════════════════════════════
# Drawing helpers
# ══════════════════════════════════════════════════════════════════════════════

# Design-space dimensions — matches HTML cover coordinates (794px × 1123px).
# The actual PDF page is A4 points; render() scales this design space to A4 so
# fallback covers merge cleanly with the ReportLab body pages.
PAGE_W = 794
PAGE_H = 1123


def _draw_dot_grid(c, x0, y0, cols, rows, gap, r, color, opacity):
    """Draw a dot-grid pattern using circles (mimics the SVG dot-grid)."""
    from reportlab.lib.colors import Color
    r_val = int(color[1:3], 16) / 255
    g_val = int(color[3:5], 16) / 255
    b_val = int(color[5:7], 16) / 255
    c.setFillColor(Color(r_val, g_val, b_val, alpha=opacity))
    for row in range(rows):
        for col in range(cols):
            cx = x0 + col * gap
            cy = PAGE_H - (y0 + row * gap)
            c.circle(cx, cy, r, fill=1, stroke=0)


def _wrap_text(c, text, font, size, max_width):
    """Split text into lines that fit max_width, using simpleSplit."""
    return simpleSplit(text, font, size, max_width)


def _draw_paragraph(c, text, x, y, font, size, max_width, leading, color):
    """Draw a multi-line paragraph at (x, y baseline of first line).

    Returns the y coordinate after the last line drawn.
    """
    c.setFillColor(HexColor(color))
    c.setFont(font, size)
    lines = _wrap_text(c, text, font, size, max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


# ══════════════════════════════════════════════════════════════════════════════
# Pattern implementations (Canvas equivalents of HTML patterns)
# ══════════════════════════════════════════════════════════════════════════════

def _pattern_fullbleed(c, t):
    """Full-bleed dark background with accent strip, dot-grid, centered title."""
    bg       = HexColor(t["cover_bg"])
    accent   = t["accent"]
    text_l   = t["text_light"]
    muted    = t["muted"]
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    subtitle = t.get("subtitle", "")
    author   = t.get("author", "")
    date     = t.get("date", "")
    doc_type = t.get("doc_type", "Document").upper()

    # Background
    c.setFillColor(bg)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Top-right accent strip
    c.setFillColor(HexColor(accent))
    c.rect(PAGE_W * 0.65, PAGE_H - 4, PAGE_W * 0.35, 4, fill=1, stroke=0)

    # Left vertical accent bar (gradient approximated by 3 segments)
    c.setFillColor(HexColor(accent))
    bar_h = PAGE_H * 0.6
    bar_top = PAGE_H * 0.82
    for i, alpha in enumerate([1.0, 0.6, 0.2]):
        seg_h = bar_h / 3
        from reportlab.lib.colors import Color
        r_val = int(accent[1:3], 16) / 255
        g_val = int(accent[3:5], 16) / 255
        b_val = int(accent[5:7], 16) / 255
        c.setFillColor(Color(r_val, g_val, b_val, alpha=alpha))
        c.rect(48, bar_top - seg_h * (i + 1), 3, seg_h, fill=1, stroke=0)

    # Dot grid
    _draw_dot_grid(c, 500, 40, 10, 20, 24, 1.8, accent, 0.12)

    # Content — vertically centered
    content_x = 68
    max_w = PAGE_W - 68 - 60
    # Estimate total height for centering
    title_lines = _wrap_text(c, title, font_d, 42, max_w)
    block_h = len(title_lines) * 44 + 40  # title leading + rule + spacing
    if subtitle:
        sub_lines = _wrap_text(c, subtitle, font_b, 11, max_w - 20)
        block_h += len(sub_lines) * 16 + 20
    y = PAGE_H / 2 + block_h / 2

    # Label
    c.setFillColor(HexColor(accent))
    c.setFont(font_b, 8)
    c.drawString(content_x, y, f"{doc_type}  ·  {date}")
    y -= 28

    # Title
    c.setFillColor(HexColor(text_l))
    c.setFont(font_d, 42)
    for line in title_lines:
        c.drawString(content_x, y, line)
        y -= 44

    # Accent rule
    c.setFillColor(HexColor(accent))
    c.rect(content_x, y - 8, max_w * 0.52, 1.5, fill=1, stroke=0)
    y -= 28

    # Subtitle
    if subtitle:
        y = _draw_paragraph(c, subtitle, content_x, y, font_b, 11, max_w - 20, 16, muted)

    # Footer
    c.setFillColor(HexColor(text_l))
    c.setFont(font_b, 9)
    c.setFillAlpha(0.5)
    c.drawString(68, 35, author)
    c.drawRightString(PAGE_W - 60, 35, date)
    c.setFillAlpha(1.0)


def _pattern_split(c, t):
    """Split panel: dark left, light right with dot-grid."""
    bg       = HexColor(t["cover_bg"])
    page_bg  = HexColor(t["page_bg"])
    accent   = t["accent"]
    text_l   = t["text_light"]
    muted    = t["muted"]
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    subtitle = t.get("subtitle", "")
    author   = t.get("author", "")
    date     = t.get("date", "")
    doc_type = t.get("doc_type", "").upper()

    # Left panel background
    c.setFillColor(bg)
    c.rect(0, 0, 330, PAGE_H, fill=1, stroke=0)

    # Right panel background
    c.setFillColor(page_bg)
    c.rect(330, 0, PAGE_W - 330, PAGE_H, fill=1, stroke=0)

    # Top accent bar on left
    c.setFillColor(HexColor(accent))
    c.rect(0, PAGE_H - 4, 330, 4, fill=1, stroke=0)

    # Divider
    c.setFillColor(HexColor(accent))
    c.rect(329, 0, 3, PAGE_H, fill=1, stroke=0)

    # Dot grid on right panel
    _draw_dot_grid(c, 360, 120, 10, 18, 22, 2, "#CCCCCC", 0.25)

    # Left panel content — centered vertically
    left_x = 44
    left_w = 330 - 44 - 44
    title_lines = _wrap_text(c, title, font_d, 28, left_w)
    block_h = len(title_lines) * 32 + 40
    if subtitle:
        sub_lines = _wrap_text(c, subtitle, font_b, 10, left_w)
        block_h += len(sub_lines) * 14 + 20
    block_h += 30  # author + date
    y = PAGE_H / 2 + block_h / 2

    c.setFillColor(HexColor(text_l))
    c.setFont(font_d, 28)
    for line in title_lines:
        c.drawString(left_x, y, line)
        y -= 32

    # Rule
    c.setFillColor(HexColor(accent))
    c.rect(left_x, y - 6, left_w * 0.55, 1.5, fill=1, stroke=0)
    y -= 20

    if subtitle:
        y = _draw_paragraph(c, subtitle, left_x, y, font_b, 10, left_w, 14, muted)

    c.setFillColor(HexColor(text_l))
    c.setFont(font_b, 10)
    c.drawString(left_x, y, author)
    y -= 14
    c.setFillColor(HexColor(muted))
    c.drawString(left_x, y, date)

    # Right label
    c.setFillColor(HexColor(muted))
    c.setFont(font_b, 8)
    c.drawRightString(PAGE_W - 44, 60, doc_type)


def _pattern_typographic(c, t):
    """Oversized display type on light background, first word in accent."""
    page_bg  = HexColor(t["page_bg"])
    accent   = t["accent"]
    dark     = t["dark"]
    muted    = t["muted"]
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    author   = t.get("author", "")
    date     = t.get("date", "")
    subtitle = t.get("subtitle", "")

    c.setFillColor(page_bg)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    words = title.split()
    first = words[0] if words else ""
    rest  = " ".join(words[1:]) if len(words) > 1 else ""

    max_w = PAGE_W - 120
    content_x = 60

    # Estimate height
    lines_first = _wrap_text(c, first, font_d, 48, max_w)
    lines_rest  = _wrap_text(c, rest, font_d, 48, max_w) if rest else []
    total_lines = len(lines_first) + len(lines_rest)
    block_h = total_lines * 52 + 60
    if subtitle:
        sub_lines = _wrap_text(c, subtitle, font_b, 11, max_w)
        block_h += len(sub_lines) * 16 + 12
    y = PAGE_H / 2 + block_h / 2

    # First word in accent
    c.setFillColor(HexColor(accent))
    c.setFont(font_d, 48)
    for line in lines_first:
        c.drawString(content_x, y, line)
        y -= 52

    # Rest in dark
    c.setFillColor(HexColor(dark))
    c.setFont(font_d, 48)
    for line in lines_rest:
        c.drawString(content_x, y, line)
        y -= 52

    # Rule
    y -= 10
    c.setFillColor(HexColor(accent))
    c.rect(content_x, y, max_w, 1.5, fill=1, stroke=0)
    y -= 24

    # Author / date row
    c.setFillColor(HexColor(dark))
    c.setFont(font_b, 11)
    c.drawString(content_x, y, author)
    c.setFillColor(HexColor(muted))
    c.drawRightString(PAGE_W - 60, y, date)
    y -= 16

    if subtitle:
        _draw_paragraph(c, subtitle, content_x, y, font_b, 11, max_w, 16, muted)


def _pattern_minimal(c, t):
    """Minimal: white bg, 8px left accent bar, oversized light-weight title."""
    page_bg  = HexColor(t["page_bg"])
    accent   = t["accent"]
    dark     = t.get("dark", "#111111")
    muted    = t.get("muted", "#999999")
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    author   = t.get("author", "")
    date     = t.get("date", "")
    subtitle = t.get("subtitle", "")
    doc_type = t.get("doc_type", "").upper()

    c.setFillColor(page_bg)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Left accent bar
    c.setFillColor(HexColor(accent))
    c.rect(0, 0, 8, PAGE_H, fill=1, stroke=0)

    content_x = 64
    max_w = PAGE_W - 64 - 64

    title_lines = _wrap_text(c, title, font_d, 56, max_w)
    block_h = len(title_lines) * 60 + 80
    if subtitle:
        sub_lines = _wrap_text(c, subtitle, font_b, 11, max_w)
        block_h += len(sub_lines) * 18 + 20
    block_h += 30
    y = PAGE_H / 2 + block_h / 2

    # Eyebrow
    c.setFillColor(HexColor(accent))
    c.setFont(font_b, 8)
    c.drawString(content_x, y, doc_type)
    y -= 36

    # Title
    c.setFillColor(HexColor(dark))
    c.setFont(font_d, 56)
    for line in title_lines:
        c.drawString(content_x, y, line)
        y -= 60

    # Thin rule
    c.setFillColor(HexColor(dark))
    c.setFillAlpha(0.2)
    c.rect(content_x, y - 8, 56, 1, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    y -= 30

    if subtitle:
        y = _draw_paragraph(c, subtitle, content_x, y, font_b, 11, max_w, 18, muted)

    # Meta
    meta = author + ("  ·  " + date if date else "")
    c.setFillColor(HexColor(muted))
    c.setFont(font_b, 9)
    c.drawString(content_x, y, meta)


def _pattern_stripe(c, t):
    """Three bold horizontal bands: accent top, dark middle, light bottom."""
    accent   = t["accent"]
    dark     = t.get("cover_bg", "#1E222A")
    light    = t.get("page_bg", "#F8F8F7")
    text_l   = t.get("text_light", "#FFFFFF")
    muted    = t.get("muted", "#888888")
    body_d   = t.get("dark", "#0E1117")
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    author   = t.get("author", "")
    date     = t.get("date", "")
    subtitle = t.get("subtitle", "")
    doc_type = t.get("doc_type", "").upper()

    top_h = 200
    mid_h = 580
    bot_y = top_h + mid_h  # 780

    # Top band
    c.setFillColor(HexColor(accent))
    c.rect(0, PAGE_H - top_h, PAGE_W, top_h, fill=1, stroke=0)

    # Mid band
    c.setFillColor(HexColor(dark))
    c.rect(0, PAGE_H - top_h - mid_h, PAGE_W, mid_h, fill=1, stroke=0)

    # Bottom band
    c.setFillColor(HexColor(light))
    c.rect(0, 0, PAGE_W, bot_y, fill=1, stroke=0)

    # Separator line
    c.setFillColor(HexColor(accent))
    c.rect(0, bot_y, PAGE_W, 2, fill=1, stroke=0)

    # Top band — eyebrow
    c.setFillColor(HexColor(dark))
    c.setFillAlpha(0.85)
    c.setFont(font_d, 10)
    c.drawString(64, PAGE_H - top_h + 24, doc_type)
    c.setFillAlpha(1.0)

    # Mid band — title (centered)
    max_w = PAGE_W - 128
    title_lines = _wrap_text(c, title, font_d, 48, max_w)
    total_h = len(title_lines) * 50
    y = PAGE_H - top_h - (mid_h - total_h) / 2
    c.setFillColor(HexColor(text_l))
    c.setFont(font_d, 48)
    for line in title_lines:
        c.drawString(64, y, line)
        y -= 50

    # Bottom band — author / date / subtitle
    bot_content_y = bot_y - 60
    c.setFillColor(HexColor(body_d))
    c.setFont(font_b, 12)
    c.drawString(64, bot_content_y, author)
    bot_content_y -= 16
    c.setFillColor(HexColor(muted))
    c.setFont(font_b, 10)
    c.drawString(64, bot_content_y, date)
    bot_content_y -= 20
    if subtitle:
        _draw_paragraph(c, subtitle, 64, bot_content_y, font_b, 11,
                        PAGE_W - 128, 16, muted)


def _pattern_generic(c, t):
    """Generic fallback for patterns without a dedicated Canvas implementation.

    Renders a clean dark-background cover with accent bar, centered title,
    subtitle, and author/date footer.  Works for any token set.
    """
    bg       = HexColor(t["cover_bg"])
    accent   = t["accent"]
    text_l   = t["text_light"]
    muted    = t["muted"]
    font_d   = t["font_display_rl"]
    font_b   = t["font_body_rl"]
    title    = t["title"]
    subtitle = t.get("subtitle", "")
    author   = t.get("author", "")
    date     = t.get("date", "")
    doc_type = t.get("doc_type", "Document").upper()

    # Background
    c.setFillColor(bg)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Top accent strip
    c.setFillColor(HexColor(accent))
    c.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)

    # Content
    content_x = 68
    max_w = PAGE_W - 68 - 60

    title_lines = _wrap_text(c, title, font_d, 40, max_w)
    block_h = len(title_lines) * 42 + 50
    if subtitle:
        sub_lines = _wrap_text(c, subtitle, font_b, 12, max_w)
        block_h += len(sub_lines) * 18 + 20
    y = PAGE_H / 2 + block_h / 2

    # Label
    c.setFillColor(HexColor(accent))
    c.setFont(font_b, 8)
    c.drawString(content_x, y, f"{doc_type}  ·  {date}")
    y -= 30

    # Title
    c.setFillColor(HexColor(text_l))
    c.setFont(font_d, 40)
    for line in title_lines:
        c.drawString(content_x, y, line)
        y -= 42

    # Rule
    c.setFillColor(HexColor(accent))
    c.rect(content_x, y - 6, 52, 2, fill=1, stroke=0)
    y -= 26

    if subtitle:
        y = _draw_paragraph(c, subtitle, content_x, y, font_b, 12, max_w, 18, muted)

    # Footer
    c.setFillColor(HexColor(text_l))
    c.setFillAlpha(0.5)
    c.setFont(font_b, 9)
    c.drawString(68, 35, author)
    c.drawRightString(PAGE_W - 60, 35, date)
    c.setFillAlpha(1.0)


# ══════════════════════════════════════════════════════════════════════════════
# Dispatch
# ══════════════════════════════════════════════════════════════════════════════

PATTERNS = {
    "fullbleed":   _pattern_fullbleed,
    "split":       _pattern_split,
    "typographic": _pattern_typographic,
    "minimal":     _pattern_minimal,
    "stripe":      _pattern_stripe,
}


def render(tokens: dict, out_path: str) -> None:
    """Render a cover PDF from tokens using ReportLab Canvas."""
    # Make a copy so we don't mutate the caller's dict
    t = dict(tokens)
    _setup_cover_cjk(t)

    pattern = t.get("cover_pattern", "fullbleed")
    fn = PATTERNS.get(pattern, _pattern_generic)

    c = canvas.Canvas(out_path, pagesize=A4)
    title = str(t.get("title") or "").strip()
    author = str(t.get("author") or "").strip()
    subject = str(t.get("subtitle") or t.get("doc_type") or "").strip()
    if title:
        c.setTitle(title)
    if author:
        c.setAuthor(author)
    if subject:
        c.setSubject(subject)
    c.setCreator("TeleAgent PDF skill")
    try:
        c.saveState()
        c.scale(A4[0] / PAGE_W, A4[1] / PAGE_H)
        fn(c, t)
        c.restoreState()
        c.showPage()
        c.save()
    except Exception as e:
        c.save()
        raise RuntimeError(f"Canvas render error: {e}") from e


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Render cover PDF from tokens.json via ReportLab Canvas (Playwright-free fallback)"
    )
    parser.add_argument("--tokens", default="tokens.json")
    parser.add_argument("--out", "--output", dest="out", default="cover.pdf")
    args = parser.parse_args()

    if not os.path.exists(args.tokens):
        print(json.dumps({"status": "error",
                          "error": f"File not found: {args.tokens}"}),
              file=sys.stderr)
        sys.exit(1)

    with open(args.tokens, encoding="utf-8") as f:
        tokens = json.load(f)

    try:
        render(tokens, args.out)
        size = os.path.getsize(args.out)
        if size < 500:
            print(json.dumps({
                "status": "error",
                "error": "Output PDF is suspiciously small — cover may be blank",
            }), file=sys.stderr)
            sys.exit(3)
        print(json.dumps({
            "status":  "ok",
            "out":     args.out,
            "size_kb": size // 1024,
            "renderer": "canvas",
            "pattern": tokens.get("cover_pattern", "fullbleed"),
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}),
              file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
