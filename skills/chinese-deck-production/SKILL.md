---
name: chinese-deck-production
description: 'Use for Chinese .pptx decks: de-AI text, pptxgenjs, QA.'
level: manual
native_agent: Hermes
license: MIT
---

# Chinese Deck Production (pptxgenjs)

## When to use
- User hands a 内容详案 / 逐页计划 (markdown plan, often LLM-generated) and asks to "把PPT做一下" / build the deck
- User hands a **source-material zip** (汇报材料/项目建议书 docx+pptx+pdf) and says "聚焦XX和YY，写N页PPT" — the focused-pages variant (see Material-zip variant below)
- Any Chinese business deck: 答辩 (competition defense), product intro, sales/report decks
- Complements the packaged `powerpoint` skill: use it for the general .pptx capability; this skill adds the proven end-to-end workflow for Chinese dense-content decks (de-AI → generate → QA) plus pptxgenjs pitfalls not in that skill.

## Material-zip variant (素材包 → 聚焦N页)
1. **Extract the zip with Chinese-filename handling** — macOS `unzip -O gbk` is NOT supported (prints usage and exits). Use Python zipfile: decode names `n.encode('cp437').decode('gbk')` and SKIP entries ending in `/` (writing a directory entry as a file raises IsADirectoryError). Full snippet in `references/material-zip-to-focused-pages.md`.
2. **Extract text per format**: docx → `textutil -convert txt -stdout`; pptx → python-pptx (remember: `has_text_frame` misses tables — also check `has_table`); pdf → pdftotext/markitdown.
3. **Mine the theme's data from the materials, never invent**: pull concrete numbers/plans/policies (e.g. 重点单位数量、行业场景数、分阶段时间表、定价/套餐模式、保险条款). Note the source doc next to each claim in the deck code comment. If the materials lack a number, keep a 【待补充】 placeholder instead of fabricating.
4. **Rewrite pages by patching the deck script**: read the top of the existing build_deck.js first to learn its helpers (header/card/chip/bullets/ph/footer, the C color palette, W/H/M constants), then patch whole IIFE blocks. **Slide order = block order = footer number**, so swapping two blocks reorders pages AND renumbers footers in one edit. Two pages, one edit each: `patch` mode=replace with the full old block as old_string.
5. **Rebuild + QA** (same as main workflow): `NODE_PATH=$(npm root -g) node build_deck.js`, structural check, and verify page content with python-pptx — including table cells (see QA stack). A stale keyword check from replaced content will legitimately MISS — treat as expected, not a failure.

## Scoring-rubric alignment (大赛答辩 variant)
When the user says "往大赛得分上面靠" or sends the 评分标准:
1. **Read the rubric first** — if it arrives as a screenshot and vision is unavailable, OCR it: `sips -Z 2880` upscale, then `tesseract img -l chi_sim --psm 6` (iterate psm 3/4/6/11; rubrics are tables). Recipe in `references/rubric-scoring-alignment.md`.
2. **Map each page to ONE scoring dimension** and design content to hit the TOP band's evidence list. Proven mapping (数据要素大赛): 市场潜力 8-10分 ← 定位条 + 三级市场(本地落地→全省复制→全国可推广) + 需求三证据(政策/事故/合规); 推广可行性 12-15分 ← 标准化可复制方案 + 已形成行业标准资质 + 组织资金保障.
3. Every claim traceable to source materials (numbers, policies, 保险条款) — never invent evidence for a scored dimension.
4. Never print score bands on the slides; the design earns them silently.
5. **双口径补短板 (dual-caliber mitigation)** — when 申报书 has objective weaknesses (客户仅1家 / 0专利0软著 / 收入小 / 未形成标准), run TWO labeled calibers side by side instead of merging or inflating: 产品体系口径 (mature product line's accumulated assets, e.g. 火眼 2012→千余家案例 = "5个以上成熟案例") vs 项目口径 (this project's own facts: 最新标杆案例 + 在谈/意向客户清单 + 单点经济账). Label each card/chip with its caliber ("产品体系口径"/"项目口径") and print a neutral one-line 口径说明 at the page bottom. Never let a product-line claim read as project fact.
6. **Score tags are OK when the outline asks for them** ("评分规则即目录"): a top-right tag "对应：创新及先进性 · 25分" helps judges locate score points while flipping pages. BUT strip internal score-chasing notes (冲「业务模式较大创新」档 / 注明口径 / 页页标注清楚…) — strategy notes from the outline's 思路 section must NOT reach the slides; rewrite as neutral audience-facing wording. Grep QA for them (see QA stack).

## Standalone focused-page delivery ("只给我这两页")
When the user asks for N pages only: copy the helper functions (C/FONT/header/footer/block/chip/bullets) into a small standalone script (e.g. build_p13_14.js) and emit a separate N-slide pptx. Keep the ORIGINAL master-deck footer numbers (e.g. "13 / 16") so the pages slot back in unchanged. Optionally patch the same IIFE blocks into the master build script to keep the full deck in sync.

## Workflow
1. **去AI味 before generating.** If the plan reads AI-ish (repetitive openers, stacked emphasis words), run the `humanizer` skill on it first and return the polished plan. Deck copy derived from AI-flavored plans carries the tells into the room. This user explicitly wants this step.
2. **Generate with pptxgenjs** (global npm pkg; on macOS always prefix `NODE_PATH=$(npm root -g)`). Pure shapes+text, no react-icons/sharp dependency — icons may not be installed globally and Chinese decks don't need them.
3. **QA (mandatory).** Content check → structural check → visual render if available. Never declare success on content QA alone if structure was never validated.

## Chinese AI-tells to strip from source plans (humanizer, Chinese specifics)
- Same sentence opener repeated per page (e.g. every page "页面目标：让评委…") — vary openers; some pages drop the subject entirely
- "执行者可自行组织表述 / 调整排版" repeated 5+ times — keep at most 2, varied wording, delete the rest
- Stacked emphasis: 彻底理解 / 必须讲透 / 立身之本 / 定调页 / 魂 / 焕发新生 — keep at most ONE real punch line (the core page deserves it), demote the rest
- Stiff labels: 上下文→背景, 视觉方向建议→视觉方向
- PRESERVE verbatim: all numbers/facts, 【待补充：xxx】 markers, and the user's own slogans (human by origin — "不是数据的搬运工…" stays)

## Deck conventions (Chinese, dense-content)
- Font: `微软雅黑` everywhere — renders correctly in WPS/PowerPoint (LibreOffice falls back for QA renders; fine)
- Canvas: LAYOUT_WIDE (13.33 × 7.5 in). Compact = body 9.5-11pt, titles 22-26pt, cards with 0.06" left accent bar, footer navy bar with 8pt page number
- Every dense body text box: `fit: "shrink"` — auto-shrinks instead of overflowing
- Placeholders: ROUNDED_RECTANGLE, light fill FBFCFD, `line: { color: "A6AEB9", width: 1, dashType: "dash" }`, 8.5pt gray centered "待补充：xxx" — visible but unobtrusive
- Sandwich structure: dark cover + closing (top/bottom accent bars), light content slides (F7F8FA)

### User style preference (2026-08, OVERRIDES the compact defaults above): 方正极简
User rejected rounded+multicolor+small-font decks as "太丑了" / "花里胡哨". Default to this for new decks and restyles:
- **方正**: RECTANGLE only — no rounded corners, no shadows, no gradients. Blocks = white rects + 1pt gray (D9DDE2) border.
- **少颜色**: 黑白灰 base (bg F2F3F5, ink 1A2530, gray 6B7280) + ONE desaturated accent (red C93A32) used only for small square markers, hero numbers, bottom underline; navy 0F1B2D only for footer/emphasis bars.
- **字体大**: header title 28pt + thin rule under; block titles 15-17pt; body bullets 10.5-13.5pt; hero numbers 30pt (number run + gray 15pt unit run). Trim copy so big fonts fit — fewer, punchier bullets.
- Header pattern: 0.16×0.16 red square + gray tag (charSpacing 3) + 28pt title + 0.014" line rule at y≈1.42.
- Bottom close: summary line 14pt bold centered at y≈6.5 (h 0.42) + thin red underline strip (h 0.045) at y≈6.95.
- ⚠️ **Footer-overlap pitfall**: footer navy bar starts at y=7.05; content placed at y≥7.0 renders ON TOP of it. Keep content above 7.0; QA-flag shapes with `top < 7.0 and top+height > 7.02 and height > 0.4`.

## Page compression (22页大纲 → N 页)
When the user says "压缩到N页" for a 答辩 outline: merge along the rubric, never across it.
1. **Merge siblings, keep the spine**: related pages merge (痛点+归因+政策契合 → 1页; 三大能力 → 1页; 成效+前后对比 → 1页; 商业模式+效益 → 1页), but the 数据要素价值主线/核心叙事 page stays its own page; cover + thanks always stay.
2. **One memory point per page survives compression**: the merged page's title states the single conclusion; sub-points that repeat other pages get dropped.
3. **Proven 22→14 mapping** (数据要素大赛 deck): cover; 一页速览(6数字+定位句); 痛点+数据归因+政策; 四层一体架构; 数据主线(核心页); 三大关键能力; 模式创新+知识产权(双口径); 数据集+数据飞轮+治理四规范; 标杆案例成效账本+前后对比; 产品成熟度+复制管道(双口径); 商业价值(三层收入/定价/经济账/社会效益); 市场潜力+三路径+标准计划; 团队保障+三年路线图+结语; 致谢.
4. Compression doubles the risk of 叠字: merged phrases collide into doubled chars ("5–10 秒" + "秒级预警" → "5–10 秒秒级"). QA must grep for doubled CJK chars after any compression edit.

## Pitfalls (pptxgenjs 4.x)
- ⚠️ **Grid right-margin math**: for n cards of width w with gap g starting at x0, verify `x0 + (n-1)*(w+g) + w ≤ W - M` with ≥0.05in slack (content width = 13.333 − 2×0.5 = 12.333). 3×3.94+2×0.26 = 12.34 silently overflows the right margin. Shrink w or g when it fails; keep all grids left-aligned at x0 = M+0.05 so rows line up across the page.
- ⚠️ **Internal notes leak onto slides**: outline 思路/备注/清单 sections (冲XX档, 注明口径, 双口径并列页页标注清楚, 评审笔记) are WORKING NOTES, not slide content. Rewrite as neutral audience-facing text before generating; grep the finished deck for them in QA.
- ⚠️ **叠字 from merged text**: compression merges phrases into doubled chars (秒秒级). Grep extracted text for doubled CJK chars after any compression edit.
- **Amber/teal on white fails WCAG**: amber E8A13C on white = 2.19:1 (below 3:1 even for large text); teal 0E8A7A = 4.0-4.26 borderline. For text on white cards use darkened variants: amber C7781D (≥3:1), teal 0C7769 (~4.6:1). Keep bright amber/teal only on navy backgrounds.
- ⚠️ **Nested rich-text arrays DO NOT WORK.** `{ text: [{text:'a',options:{bold:true}}, {text:'b'}], options:{bullet:true} }` silently renders literal `[object Object]` into the slide XML. Use flat array items `{ text: 'string', options: { bullet: true, breakLine: true, paraSpaceAfter: 3 } }` or plain strings. If bold labels matter, use a separate colored text box — don't fight the API.
- No `#` in hex colors (corrupts file); fresh option object per shape (pptxgenjs mutates in place); avoid `lineSpacing` with bullets → use `paraSpaceAfter`; `rectRadius` only on ROUNDED_RECTANGLE.
- A single-pass render is never correct. Budget a fix-and-reverify cycle.

## QA stack (in order of reliability)
1. **Content:** `markitdown deck.pptx` — verify slide count, key strings, and CRITICALLY `grep "object Object"` to catch rich-text corruption (this caught a real bug). Also grep for: internal working-note leaks (`冲「.*」档|注明口径|页页标注|评审笔记`) and 叠字 doubled CJK chars (`grep -oE "([一-龥])\\1"` — e.g. 秒秒级 from merged text); both are real bugs this workflow has produced.
2. **Structure:** `python3 scripts/qa_deck.py deck.pptx [expected_pages]` (python-pptx) — catches corrupted files, out-of-canvas shapes, empty slides. When pages use `addTable`, ALSO verify the table cells: `shape.has_table` → `shape.table.rows/cells` (plain `has_text_frame` iteration silently skips tables entirely).
3. **Visual:** `soffice --headless --convert-to pdf` + `pdftoppm`. If soffice produces no output and sits at 0% CPU, don't block the delivery on it — fall back to 1+2, tell the user honestly that pixel-level QA was skipped, and ask them to eyeball the dense pages.
4. **Visual QA on existing renders WITHOUT a vision tool** (user hands slide JPGs and asks "find issues"): the JPGs are exports of the deck PDF — verify correspondence, then run `python3 scripts/slide_render_qa.py deck.pdf` (PyMuPDF geometry + pixel-sampled contrast + placeholder scan). Full methodology and the CJK false-positive pitfalls (per-char span fragmentation, ink-profile verification, footer/chip classification) in `references/deck-visual-qa-without-vision.md`. Verified-issue-only reporting: never ship a report full of glyph-padding artifacts.

## Support files
- `scripts/qa_deck.py` — python-pptx structural QA (slide count, shape bounds, per-slide dump)
- `scripts/slide_render_qa.py` — vision-free visual QA of slide renders from the source PDF (overlaps, overflow, footer collisions, card gaps <0.3in, alignment, pixel-sampled WCAG contrast, placeholders)
- `references/deck-visual-qa-without-vision.md` — methodology + CJK false-positive pitfalls (per-char span merging, ink-profile verification, footer/chip classification, bg pixel-sampling), JPG↔PDF correspondence check
- `references/defense-deck-blueprint.md` — reusable per-slide layout recipes from a proven 16-page 答辩 deck (pain cards, architecture stack, flow+return arrow, cert wall, before/after, dual case columns, timeline, pricing tiers)
- `references/dual-caliber-and-page-compression.md` — 双口径补短板 strategy table + proven 22页大纲→14页 mapping (数据要素大赛 worked example), compression rules, pre-empted QA findings (叠字/内部笔记/网格右缘溢出/对比度)
- `references/material-zip-to-focused-pages.md` — Chinese zip extraction snippet (macOS), per-format text extraction, focused-page rewrite recipe with in-place IIFE-block patching, table-cell verification
- `references/rubric-scoring-alignment.md` — 大赛评分标准 → 页面设计映射 (worked example: 市场潜力/推广可行性), 方正极简版式坐标, 截图评分表 tesseract OCR fallback, 页脚重叠坑的修复与 QA 断言
