# OCR Script for Scanned PDFs — Quick Reference

## Minimal working example

```python
import fitz, subprocess, os

pdf_path = '/path/to/scanned.pdf'
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
        if len(img_bytes) < 5000:
            continue
        img_path = f'{tmpdir}/p{page_num+1:03d}_{img_idx}.jpg'
        with open(img_path, 'wb') as out:
            out.write(img_bytes)
        rel_path = os.path.relpath(img_path, '/tmp')
        result = subprocess.run(
            ['tesseract', rel_path, 'stdout', '-l', 'chi_sim', '--psm', '6'],
            capture_output=True, timeout=60,
            cwd='/tmp'
        )
        text = result.stdout.decode('utf-8', errors='replace').strip()
        if text:
            page_texts.append(text)
    combined = '\n'.join(page_texts)
    full_text.append(f'--- Page {page_num+1} ---\n{combined}')
    print(f'Page {page_num+1}: {len(combined)} chars', flush=True)

doc.close()
output = '\n\n'.join(full_text)
```

## Quick checks

### Is the PDF scanned?
```python
import fitz
doc = fitz.open(pdf_path)
page = doc[0]
text = page.get_text()
images = page.get_images(full=True)
print(f'Text length: {len(text.strip())}, Images: {len(images)}')
# If text is empty but images exist → scanned PDF, needs OCR
```

### Does the image have content?
```python
from PIL import Image
import numpy as np
arr = np.array(Image.open(img_path).convert('L'))
print(f'Min={arr.min()}, Max={arr.max()}, Mean={arr.mean():.1f}')
# min < 50 → has dark text content
# mean > 250 → mostly white/blank
```

## Common document types that are scanned

- Government documents (红头文件, 通知, 政策文件)
- Corporate internal documents with seals/stamps
- Legal documents (contracts, court filings)
- Older archived documents
- Documents that were printed, signed, then re-scanned

## When NOT to use this skill

- PDF has a text layer (get_text() returns content) → just use fitz directly
- User sends a .docx, .xlsx, or other format → use read_file (auto-extracted)
- User sends an image file directly → use vision tools or tesseract directly on the image