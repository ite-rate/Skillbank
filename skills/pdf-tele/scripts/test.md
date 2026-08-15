# pdf skill fallback scripts - quick test

Goal: verify the degraded-mode scripts work and produce expected outputs.

## Prerequisites

At minimum, install these pip packages for fallback scripts:

- `pypdfium2`
- `pypdf` (package name is often `pypdf`)
- `pdfplumber`
- `Pillow`

Example:

```bash
pip install pypdfium2 pypdf pdfplumber Pillow
```

## Prepare a sample PDF

Use any small PDF you have locally:

- `sample_native.pdf` (text-based PDF)

If you need to generate a tiny PDF quickly (optional):

```bash
python - <<'PY'
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

for name in ["sample1.pdf", "sample2.pdf"]:
    c = canvas.Canvas(name, pagesize=letter)
    c.drawString(72, 720, f"Hello from {name}")
    c.drawString(72, 700, "pdf skill test")
    c.showPage()
    c.save()
print("Generated sample1.pdf and sample2.pdf")
PY
```

## Test 1: convert_pdf_to_images degraded fallback

This is deterministic: it forces degraded mode regardless of poppler being installed.

```bash
python scripts/convert_pdf_to_images.py sample_native.pdf ./out_images --force-fallback --dpi 150 --format png
```

Checks:
- Console includes `[DEGRADED MODE]`
- `./out_images/page_1.png` exists (and more pages if your PDF has them)

## Test 2: fallback_pdf_to_images script directly

```bash
python scripts/fallback_pdf_to_images.py sample_native.pdf --outdir ./out_images2 --dpi 150 --format png
```

Checks:
- Console includes `[DEGRADED MODE]`
- Images are generated as `page_1.png`, `page_2.png`, ...

## Test 3: fallback_text_extract

```bash
python scripts/fallback_text_extract.py sample_native.pdf --out ./out_text.md --tables
```

Checks:
- Console includes `[DEGRADED MODE]`
- `./out_text.md` is created and contains `## Page 1`

## Test 4: fallback_pdf_ops

Merge:

```bash
python scripts/fallback_pdf_ops.py merge sample1.pdf sample2.pdf --out merged.pdf
```

Split into pages:

```bash
python scripts/fallback_pdf_ops.py split merged.pdf --outdir ./out_pages
```

Rotate:

```bash
python scripts/fallback_pdf_ops.py rotate merged.pdf --out rotated.pdf --degrees 90
```

Checks:
- Output PDFs exist
- Console includes `[DEGRADED MODE]`

