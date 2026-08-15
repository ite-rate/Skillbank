---
name: scanned-pdf-ocr
description: Extract text from scanned/image-based PDFs that have no text layer. Covers detecting whether a PDF is scanned, extracting embedded images, running tesseract OCR (including Chinese), and handling tiled image layouts.
level: manual
native_agent: Hermes
---

# Scanned PDF OCR Extraction

Extract text from scanned/image-based PDFs that have no text layer. Covers detecting whether a PDF is scanned, extracting embedded images, running tesseract OCR (including Chinese), and handling tiled image layouts.

## When to use

- User sends a PDF and `fitz.open(f)[page].get_text()` returns empty or near-empty strings
- PDF contains embedded JPEG/PNG images but no selectable text layer
- PDF is a scanned document (government, corporate, legal docs commonly arrive this way)
- User asks you to "read this PDF" or "extract the text from this document"

## Detection: is the PDF scanned?

```python
import fitz
doc = fitz.open(pdf_path)
page = doc[0]
text = page.get_text()
images = page.get_images(full=True)

if len(text.strip()) < 10 and len(images) > 0:
    # Scanned PDF — content is in embedded images, not a text layer
    pass  # proceed with OCR pipeline below
elif len(text.strip()) > 50:
    # Has a text layer — just use get_text(), no OCR needed
    pass  # return text directly
```

## OCR Pipeline

### Step 1: Install Chinese language support (if needed)

```bash
# Check if chi_sim is already available
tesseract --list-langs 2>&1 | grep chi_sim

# If not found, install the language pack
brew install tesseract-lang
# Verify
tesseract --list-langs 2>&1 | grep chi_sim  # should show chi_sim, chi_sim_vert, chi_tra, chi_tra_vert
```

For English-only OCR, the base `tesseract` brew package is sufficient.

### Step 2: Extract embedded images and run OCR

**Key insight**: Scanned PDFs often store page content as multiple tiled JPEG images (e.g., a 2048x2048 main tile + thin strip tiles). Extract each image separately via `doc.extract_image(xref)`, save to `/tmp/`, and OCR them.

**Critical tesseract workaround**: On macOS, tesseract fails to open files when invoked with paths outside its working directory — it reports "image file not found" even though the file exists. **Always run tesseract with `cwd='/tmp'` and use relative paths** (filenames only, no directory prefix).

```python
import fitz, subprocess, os

doc = fitz.open(pdf_path)
tmpdir = '/tmp/pdf_ocr'
os.makedirs(tmpdir, exist_ok=True)

full_text = []
for page_num in range(len(doc)):
    page = doc[page_num]
    images = page.get_images(full=True)
    page_texts = []
    for img_idx, img in enumerate(images):
        xref = img[0]
        base_image = doc.extract_image(xref)
        img_bytes = base_image['image']
        # Skip tiny decorative images (<5KB)
        if len(img_bytes) < 5000:
            continue
        # Use simple ASCII filename — tesseract has path issues with complex paths
        img_path = f'{tmpdir}/p{page_num+1:03d}_{img_idx}.jpg'
        with open(img_path, 'wb') as out:
            out.write(img_bytes)
        # CRITICAL: run tesseract with cwd='/tmp' and relative path
        rel_path = os.path.relpath(img_path, '/tmp')
        result = subprocess.run(
            ['tesseract', rel_path, 'stdout', '-l', 'chi_sim', '--psm', '6'],
            capture_output=True, timeout=60,
            cwd='/tmp'  # MUST be /tmp — tesseract path resolution breaks otherwise
        )
        text = result.stdout.decode('utf-8', errors='replace').strip()
        if text:
            page_texts.append(text)
    combined = '\n'.join(page_texts)
    full_text.append(f'--- Page {page_num+1} ---\n{combined}')

doc.close()
output = '\n\n'.join(full_text)
```

### Step 3: Handle empty OCR results

If tesseract returns 0 chars for all pages despite images having content:

1. **Verify the image actually has content** (not blank):
```python
from PIL import Image
import numpy as np
arr = np.array(Image.open(img_path).convert('L'))
print(f'Min={arr.min()}, Max={arr.max()}, Mean={arr.mean():.1f}')
# If mean > 250 and max < 255, image is all-white/blank
# If min < 50, there is dark text content — OCR should work
```

2. **Check tesseract is running from /tmp** — this is the #1 cause of empty results on macOS. The error looks like `Error in fopenReadStream: failed to open locally` or `image file not found`.

3. **Try PSM modes**: default `--psm 6` works for most documents. Alternatives: `3` (auto), `4` (single column), `11` (sparse text), `12` (sparse + OSD).

4. **Preprocessing** (rarely needed, but available):
```python
from PIL import Image, ImageEnhance
img = Image.open(img_path)
gray = img.convert('L')
enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
enhanced.save(enhanced_path)
```

## Pitfalls

- **tesseract cwd bug**: On macOS (homebrew tesseract 5.x), tesseract cannot open files via absolute paths from certain working directories. Always set `cwd='/tmp'` in subprocess.run and pass relative filenames. This is not documented in tesseract's man page and took significant debugging to discover.
- **page.get_pixmap() renders white**: When a PDF's content is in embedded images (not in the page content stream), `get_pixmap()` produces a white page. Don't waste time on pixmap-based OCR — extract the embedded images directly.
- **Tiled images**: Some PDFs split each page into 4+ image tiles (e.g., 2048x2048 + 19x2048 + 2048x876 + 19x876). OCR each tile separately and concatenate. Skip tiles smaller than ~5KB (decorative strips).
- **OCR quality**: tesseract on Chinese scanned docs produces ~80-90% accurate text. Watch for: misread characters in dense tables, page numbers mixed into body text, broken formatting. Always note in your summary that text was OCR-extracted and may contain minor errors.
- **Large PDFs**: 30+ page scanned PDFs take 2-5 minutes to OCR. Use `background=True` with `notify_on_complete=True` for the OCR batch.
- **subprocess decode error**: Use `result.stdout.decode('utf-8', errors='replace')` not `text=True` in subprocess.run — tesseract can emit non-UTF-8 bytes that cause UnicodeDecodeError with `text=True`.

## Verification

After OCR, verify you got meaningful content:
```python
total_chars = sum(len(t) for t in full_text)
if total_chars < 100:
    print("WARNING: OCR returned very little text — check tesseract cwd, language pack, and image content")
```

## Image/Screenshot OCR (non-PDF)

When the user sends a screenshot or image file (JPG/PNG) in chat and asks you to analyze text content — KPI tables, contracts, specs, etc. — use the same tesseract pipeline with additional preprocessing for small images.

### Technique: Upscale + Quadrant Split

Small chat images (e.g., 1039×544) produce poor OCR directly. Two techniques dramatically improve results:

1. **Upscale 2-3x with PIL LANCZOS** before OCR:
```python
from PIL import Image
img = Image.open(image_path)
img_2x = img.resize((img.size[0]*3, img.size[1]*3), Image.LANCZOS)
img_2x.save(upscaled_path)
```

2. **Split into quadrants** for dense tables — OCR each quadrant separately, then concatenate. This gives tesseract more pixel area per character and reduces column confusion:
```python
w, h = img.size
for i, (name, box) in enumerate([
    ('q1', (0, 0, w//2, h//2)),
    ('q2', (w//2, 0, w, h//2)),
    ('q3', (0, h//2, w//2, h)),
    ('q4', (w//2, h//2, w, h)),
]):
    crop = img.crop(box)
    crop_3x = crop.resize((crop.size[0]*3, crop.size[1]*3), Image.LANCZOS)
    crop_3x.save(f'/Users/ss/ocr_{name}.png')
```

3. **Run tesseract with `chi_sim+eng` and `--psm 4`** (single column) for mixed Chinese-English tabular content:
```bash
tesseract /Users/ss/ocr_q1.png stdout -l chi_sim+eng --psm 4
```

### PSM mode selection for images

| PSM | Use case |
|-----|----------|
| `4`  | Single column — best for tables, forms, KPI docs |
| `6`  | Uniform block — good for paragraphs |
| `3`  | Auto — fallback when 4/6 produce garbage |
| `11` | Sparse text — for images with lots of whitespace |

### When OCR isn't enough

OCR on dense Chinese tables typically gets 70-85% accuracy. Gaps in recognition mean you must **infer structure** from partial text — identify the table headers, match weight percentages, and reconstruct the document logic. Always tell the user the text was OCR-extracted and may contain minor errors.

If OCR quality is too poor even after upscaling, use `browser_navigate` to open the image file and `browser_console` with `document.body.innerText` as an alternative extraction path — sometimes the browser's rendering pipeline picks up text that tesseract misses (rare, but worth trying for images with embedded text layers).

## Reference files

- `references/ocr-script.py` — minimal working OCR script, quick checks, and common scanned document types