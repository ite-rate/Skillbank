---
name: pdf-tele
description: 'Full-spectrum PDF skill: visually polished document generation via token-driven design system (15 doc types, HTML/CSS cover + ReportLab body), plus reading, merging, splitting, form filling, watermarking, encryption, and OCR. CREATE: "make a PDF", "generate report", "beautiful document", "cover page", "client-ready", "polished PDF", "write a proposal". READ: "extract text from PDF", "read this PDF", "what''s in this document". MANIPULATE: "merge PDFs", "split pages", "rotate", "add watermark", "encrypt". FILL: "fill in this form", "complete form fields". REFORMAT: "reformat this document", "apply our style", "convert markdown to PDF".'
level: manual
native_agent: TeleAgent
description_zh: 支持读取、编辑和处理PDF文件，可用于提取文字和表格、合并与拆分页面、旋转与加水印、生成新PDF、填写表单以及对扫描件进行 OCR 识别，适合日常文档整理与内容提取。
name_zh: PDF助手
license: Proprietary + MIT (PDF skill components)
---

# PDF Skill — Full-Spectrum Document Processing

**Three tasks. One design system. Tokens flow from content analysis through every renderer.**

## Route Table

| User intent | Route | Engine |
|---|---|---|
| Generate a visually polished PDF | **CREATE** | `pdf_palette.py` → `pdf_cover.py` → `pdf_render_cover.js` (or Canvas fallback `pdf_cover_canvas.py`) → `pdf_render_body.py` → `pdf_merge.py` |
| Fill form fields in an existing PDF | **FILL** | `pdf_fill_inspect.py` → `pdf_fill_write.py` |
| Reformat / restyle an existing document | **REFORMAT** | `pdf_reformat_parse.py` → full CREATE pipeline |
| Read / extract text, tables from PDF | **READ** | `pdfplumber` / `paddleocr-doc-parsing` |
| Merge, split, rotate, watermark, encrypt | **MANIPULATE** | `pypdf` / `qpdf` / fallback scripts |
## Template Compliance Policy

When a user provides a PDF template for generating a new PDF, faithfully replicate its format — page dimensions, margins, fonts, colors, header/footer structure, and section layout. Do NOT substitute or improvise design elements.

If following the template makes it impossible to fulfill the user's requirements, describe the specific conflict and obtain explicit consent before deviating. Do NOT silently deviate.

**Example:** "您的需求需要在页面顶部添加一个额外的信息栏，但模版的页边距设置不允许在该位置放置内容。是否允许调整页边距？"

## Content Extraction Strategy

**Rule:** when in doubt between CREATE and REFORMAT, ask whether the user has an existing document. If yes → REFORMAT. If no → CREATE.

---

## Route A: CREATE (visually polished PDF generation)

Read `design/design.md` before any CREATE or REFORMAT work.
For Chinese text, use the operating system's built-in Chinese fonts.

### Quick Start

```bash
# Check dependencies
bash scripts/make.sh check

# Generate a polished PDF
bash scripts/make.sh run \
  --title "Q3 Strategy Review" --type proposal \
  --subtitle "Channel growth and AI enablement" \
  --date "October 2025" \
  --accent "#2D5F8A" \
  --content content.json --out report.pdf
```

`make.sh run --content` accepts either:
- `content.json`: the body schema consumed directly by `pdf_render_body.py`
- `.md`, `.markdown`, `.txt`, or `.pdf`: automatically parsed through `pdf_reformat_parse.py` into temporary `content.json`

All CREATE pipeline scripts accept `--out`; `--output` is also accepted as an alias.

PDF metadata is written by default. `/Author` defaults to `TeleAgent`; `/Title`
comes from `--title`; `/Subject` comes from `--subtitle` when available. Agents
do not need to force metadata arguments in normal usage, but may pass
`--author` or `--subject` explicitly when a user asks for a custom value.

### Document Types

`report` · `proposal` · `resume` · `portfolio` · `academic` · `general` · `minimal` · `stripe` · `diagonal` · `frame` · `editorial` · `magazine` · `darkroom` · `terminal` · `poster`

### Pipeline

1. **`pdf_palette.py`** — metadata → `tokens.json` (colors, fonts, spacing, cover pattern)
2. **`pdf_cover.py`** — `tokens.json` → `cover.html` (one of 13 cover patterns)
3. **`pdf_render_cover.js`** — `cover.html` → `cover.pdf` (Playwright/Chromium, **optional**)
   - **Canvas fallback**: `pdf_cover_canvas.py` — `tokens.json` → `cover.pdf` (ReportLab Canvas, no Node/Chromium deps)
   - `make.sh` auto-selects: Playwright if available, Canvas fallback otherwise
4. **`pdf_render_body.py`** — `tokens.json` + `content.json` → `body.pdf` (ReportLab)
5. **`pdf_merge.py`** — `cover.pdf` + `body.pdf` → `final.pdf` + QA report; writes `/Title`, `/Author`, `/Subject` PDF metadata for browser/PDF-reader tabs. Explicit `--title/--author/--subject` wins; otherwise it inherits metadata from cover/body, then uses the output filename as the title fallback and `TeleAgent` as the author fallback.

Manual pipeline from Markdown:

```bash
python3 scripts/pdf_reformat_parse.py \
  --input source.md --out content.json

python3 scripts/pdf_palette.py \
  --title "增长报告" --subtitle "全渠道增长与AI赋能" \
  --type report --date "2026-07-01" \
  --content content.json --out tokens.json

python3 scripts/pdf_cover.py --tokens tokens.json --out cover.html

# Use one renderer:
node scripts/pdf_render_cover.js --input cover.html --out cover.pdf
# or, when Playwright/Chromium is unavailable:
python3 scripts/pdf_cover_canvas.py --tokens tokens.json --out cover.pdf

python3 scripts/pdf_render_body.py --tokens tokens.json --content content.json --out body.pdf
python3 scripts/pdf_merge.py \
  --cover cover.pdf --body body.pdf --out final.pdf
```

### content.json Block Types

`pdf_render_body.py --content` does **not** accept raw Markdown. It requires a JSON array of structured blocks:

```json
[
  {"type": "h1", "text": "Executive Summary"},
  {"type": "body", "text": "This paragraph becomes styled body text."},
  {"type": "bullet", "text": "A bullet point"}
]
```

To use Markdown manually, convert first:

```bash
python3 scripts/pdf_reformat_parse.py --input source.md --out content.json
```

| Block | Key fields |
|---|---|
| `h1` | `text` |
| `h2` | `text` |
| `h3` | `text` |
| `body` | `text` (supports `<b>` `<i>`) |
| `bullet` | `text` |
| `numbered` | `text` |
| `callout` | `text` |
| `table` | `headers`, `rows`, `col_widths`?, `caption`? |
| `image` / `figure` | `path`/`src`, `caption`? |
| `code` | `text`, `language`? |
| `math` | `text` (LaTeX), `label`?, `caption`? |
| `chart` | `chart_type`, `labels`, `datasets`, `title`?, `caption`? |
| `flowchart` | `nodes`, `edges`, `caption`? |
| `bibliography` | `items` [{id, text}], `title`? |
| `divider` | — |
| `pagebreak` | — |
| `spacer` | `pt` (default 12) |

### Accent Color Selection

Pick from the document's semantic context. Muted, desaturated tones work best.

| Context | Suggested accent |
|---|---|
| Legal / finance | Deep navy `#1C3A5E`, slate `#3D4C5E` |
| Healthcare | Teal-green `#2A6B5A` |
| Technology | Steel blue `#2D5F8A` |
| Creative | Burgundy `#6B2A35` |
| Academic | Deep teal `#2A5A6B` |
| Corporate | Slate `#3D4A5A` |

### Fallback: Playwright unavailable

If Node.js or Playwright/Chromium is not available, the **Canvas fallback** script
`pdf_cover_canvas.py` generates the cover directly via the ReportLab Canvas API —
no Node.js, Chromium, or external network access required.

`make.sh run` auto-detects Playwright availability and selects the renderer:
- Playwright available → `pdf_render_cover.js` (full HTML/CSS cover, 13 patterns)
- Playwright unavailable → `pdf_cover_canvas.py` (Canvas cover, 5 dedicated patterns + generic fallback)

The Canvas renderer reuses `pdf_render_body.py`'s CJK font registration logic,
so Chinese/Japanese/Korean titles render correctly without any extra configuration.

---

## Route B: FILL (form field completion)

```bash
# Step 1: inspect
python scripts/pdf_fill_inspect.py --input form.pdf

# Step 2: fill
python scripts/pdf_fill_write.py --input form.pdf --out filled.pdf \
  --values '{"FirstName": "Jane", "Agree": "true", "Country": "US"}'
```

| Field type | Value format |
|---|---|
| `text` | Any string |
| `checkbox` | `"true"` or `"false"` |
| `dropdown` | Must match a choice value from inspect output |
| `radio` | Must match a radio value |

See `forms.md` for advanced form handling (annotations-based workflow).

---

## Route C: REFORMAT (apply design to existing document)

```bash
bash scripts/make.sh reformat \
  --input source.md --title "My Report" --type report --out output.pdf
```

Supported input: `.md` `.txt` `.pdf` `.json`

---

## Route D: READ (content extraction)

### Decision Tree

**Step 1: Detect document type**
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    sample = "".join(page.extract_text() or "" for page in pdf.pages[:3])
    is_scanned = len(sample.strip()) < 50
```

- Text extraction yields content → **native PDF** → `pdfplumber`
- Empty or garbled text → **scanned/complex** → `paddleocr-doc-parsing`

**Step 2a: Native PDF**
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()
```

**Exceptions** (treat as Step 2b): multi-column layout, dense merged-cell tables, embedded formulas, non-Latin scripts.

**Step 2b: Scanned / complex document**
```bash
python <paddleocr-skill-path>/scripts/vl_caller.py --file-path "file.pdf" --pretty
```

---

## Route E: MANIPULATE (merge, split, rotate, watermark, encrypt)

### Merge
```python
from pypdf import PdfWriter, PdfReader
writer = PdfWriter()
for f in ["doc1.pdf", "doc2.pdf"]:
    for page in PdfReader(f).pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as out:
    writer.write(out)
```

### Split
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter(); writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as out:
        writer.write(out)
```

### Rotate
```python
page = reader.pages[0]; page.rotate(90); writer.add_page(page)
```

### Watermark
```python
watermark = PdfReader("watermark.pdf").pages[0]
for page in reader.pages:
    page.merge_page(watermark); writer.add_page(page)
```

### Encrypt
```python
writer.encrypt("userpassword", "ownerpassword")
```

### Extract Metadata
```python
meta = reader.metadata
print(meta.title, meta.author, meta.subject)
```

### CLI tools (if available)

| Tool | Fallback |
|---|---|
| `pdftotext` | `python scripts/fallback_text_extract.py` |
| `qpdf` | `python scripts/fallback_pdf_ops.py` |
| `pdftk` | `python scripts/fallback_pdf_ops.py` |
| `pdfimages` | `python scripts/fallback_pdf_to_images.py` |

---

## Quick Reference

| Task | Best Tool |
|---|---|
| Create polished PDF | PDF CREATE pipeline |
| Extract text | `pdfplumber` |
| Extract tables | `pdfplumber.extract_tables()` |
| OCR scanned PDF | `paddleocr-doc-parsing` |
| Merge PDFs | `pypdf` |
| Split PDFs | `pypdf` |
| Fill forms | `pdf_fill_inspect.py` + `pdf_fill_write.py` |
| Rotate / watermark / encrypt | `pypdf` |
| Reformat document | PDF REFORMAT pipeline |

---

## Dependencies

### Python packages
- `pypdf` · `pdfplumber` · `reportlab` · `Pillow` · `pypdfium2` · `matplotlib`

### Node.js (optional, for HTML cover rendering)
- `playwright` + Chromium
- If unavailable, the Canvas fallback (`pdf_cover_canvas.py`) is used automatically — no Node.js needed

### CJK fonts (required for Chinese/Japanese/Korean content)
- **macOS**: built-in (PingFang) — no action needed
- **Windows**: built-in (Microsoft YaHei) — no action needed
- **Linux**: install manually — `sudo apt-get install fonts-noto-cjk` (Debian/Ubuntu) or `sudo dnf install google-noto-sans-cjk-fonts` (Fedora/RHEL)
- `make.sh fix` auto-installs CJK fonts on Linux via apt/dnf/yum

### System CLI tools (optional)
- `poppler-utils` · `qpdf` · `pdftk`

### Windows install hints
- `poppler-utils`: `winget install oschwartz10612.Poppler`
- `qpdf`: `winget install qpdf.qpdf`
- If CLI install fails: use `scripts/fallback_*.py` scripts

---

## Mandatory policy: installation and fallback constraints

- If a required dependency is missing, attempt installation first.
- If installation fails, use the predefined degraded-mode scripts.
- Do NOT invent alternate pipelines unless both steps were attempted and insufficient.
- For CREATE route: `make.sh` auto-selects Playwright or Canvas fallback for cover rendering. No manual intervention needed.

---

## Next Steps

- For form filling with annotations: see `forms.md`
- For advanced features and JS libraries: see `reference.md`
- For design system details: read `design/design.md` before any CREATE/REFORMAT work
