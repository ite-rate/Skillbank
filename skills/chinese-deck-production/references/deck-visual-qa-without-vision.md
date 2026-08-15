# Deck visual QA without a vision tool (source-PDF geometry)

Trigger: user hands rendered slide JPGs (or a deck) and asks to "find issues"
(overlaps, overflow, footer collisions, tight gaps, misalignment, low
contrast, placeholder text). No vision tool available → do NOT eyeball or
hand-wave. The renders are almost always exports of a PDF in the same folder
(答辩PPT_N页.pdf). Use the PDF as exact ground truth: 960x540pt page =
13.33x7.5in, so 0.3in gap = 21.6pt.

## Step 0 — verify JPG ↔ PDF correspondence first (mandatory)
Geometry conclusions only transfer to the JPGs if they render the same PDF.
- Mean abs pixel diff vs a fitz render at the JPG's scale (JPEG gives ~20-60;
  ~0 means identical).
- Color sampling at known points: slide bg, card fill, footer navy
  (e.g. bg (247,248,250) and navy (15,26,44) matched exactly).
- Edge-profile match: scan a row for luminance jumps; card-left/accent-bar
  edges must appear at the scaled PDF coordinates.
If the JPG is a DIFFERENT export (different renderer), layout conclusions
still hold — only colors/AA shift.

## Step 1 — dump one page fully before writing checks
Drawings (fills, rects) + text spans with bboxes. Learn the deck's anatomy:
full-bleed bg rects (often white UNDER a colored full-bleed), cards (white
fill, >50x25pt), accent bars (width<12, full card height), header chips,
footer bar (bottom-most full-width navy, height~30), colored inner chips.
Everything downstream keys off this classification.

## Step 2 — merge CJK per-character spans into visual lines
CJK PDFs emit ONE span PER CHARACTER with slightly padded bboxes (y0 can
jitter 2-2.6pt per glyph). Checks:
- Overlap detection on raw spans → floods of false positives.
- "RAGGED-BASELINE" (y0 variance 1.8-2.6pt within a line) → ALWAYS an
  extraction artifact. Never report it.
Merge by: same y-center within 3pt AND x-contiguous (<6pt gap), then run
overlap checks on the merged visual lines only.

## Step 3 — verify suspect overlaps with ink profiling before reporting
bbox intersections of 1-3pt height are glyph-padding artifacts. Render the
region at zoom 4 (fitz clip=Rect), count dark pixels per row via numpy; a
clean ink gap between lines (e.g. 3.4pt) = no real collision. Only report
overlaps with ink actually interleaving. (Worked example: slide 9 '预警'
bbox overlapped line above by 1.9pt — ink profile showed clean separation.)

## Step 4 — resolve background color by PIXEL SAMPLING, not rect lists
Guess-bg-from-rect-fills fails on: dark full-bleed pages (white-on-navy is
17:1, not ~1.06), navy bands/chips, orange chips inside white cards. Render
the page once (zoom 2), sample the pixel at each text line's center →
correct WCAG contrast every time. Flag <3.0 (any size) and <4.5 for
sz<14pt; 3.7-4.4 = "borderline" (report as minor).

## Step 5 — footer/card classification gotchas
- Footer = bottom-most rect with y0>0.85H, height<60, width>0.9W. NOT "any
  navy rect" — content slides carry navy chips/cards that are not the footer
  (slide 11 had 5 navy benefit chips at y=439; footer was at 509.8).
- Chip containment checks need BOTH x- and y-overlap (x-range alone fires on
  every card text below the header chip).
- Card membership for overflow checks: center-point of the line inside the
  card, never "bbox intersects card" (that fires on every neighboring card).

## Step 6 — placeholder scan on raw text
`page.get_text("text")` then regex for 待补充/待确认/待定/【待/（待/需补充/？？/TODO.
Covers leftover rubric notes (评审口径/得分档 sentences) too — those are
working notes accidentally left ON slides; flag them.

## Reporting rules
- Group per-slide, dedupe, give pt/in values and exact text + coords.
- Distinguish real findings vs borderline (sub-AA by <0.3) vs artifacts —
  and say so. A report full of false positives is as bad as a missed bug.
- Always name the verification method (ink profile, pixel sample) next to
  any finding that needed it.
- Save a findings .md in the deck folder; keep the checker script so the
  user can re-run after fixes.

## Reusable artifacts
- `scripts/slide_render_qa.py` — hardened checker implementing steps 2-6
  (usage: `python3 slide_render_qa.py deck.pdf`).
- PyMuPDF note: rendering a page may print "MuPDF error: ... structure tree"
  to stderr — harmless, filter with `2>&1 | grep -v "MuPDF error"`.
