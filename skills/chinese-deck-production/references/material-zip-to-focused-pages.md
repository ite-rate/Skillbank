# Material Zip → Focused Deck Pages (素材包 → 聚焦N页)

Worked example: 火眼汇报材料 (15 files: docx/pptx/pdf) → user asked for 2 pages on 市场空间 + 营销路径, rewritten in-place in an existing 16-page 答辩 deck (build_deck.js).

## 1. Extract Chinese-named zip on macOS

`unzip -O gbk` does NOT exist on macOS Info-ZIP (prints usage). Use Python:

```python
import zipfile, os
with zipfile.ZipFile(path) as z:
    for n in z.namelist():
        try:
            fixed = n.encode('cp437').decode('gbk')   # fix mojibake names
        except Exception:
            fixed = n
        dest = os.path.join(out, fixed)
        if n.endswith('/'):          # MUST skip directory entries
            os.makedirs(dest, exist_ok=True)
            continue                 # writing them as files → IsADirectoryError
        os.makedirs(os.path.dirname(dest) or out, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(z.read(n))
```

## 2. Per-format text extraction

- docx → `textutil -convert txt -stdout file.docx` (built into macOS, handles .docx; loop over all files)
- pptx → python-pptx: iterate shapes; `has_text_frame` for text boxes; **tables are GraphicFrames — check `has_table` separately**:

```python
from pptx import Presentation
p = Presentation(deck)
for i, slide in enumerate(p.slides, 1):
    for shape in slide.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip():
            print(shape.text_frame.text)
        if shape.has_table:
            for row in shape.table.rows:
                print(" | ".join(c.text.strip()[:24] for c in row.cells))
```

- pdf → pdftotext or markitdown.

## 3. Mine theme data (example: market + go-to-market)

Pull ONLY what the materials actually say. For 市场空间/营销路径 the high-value fields were:
- 存量客户基数 (安阳 147 家消防重点单位), 场景数 (十大应用场景), 覆盖范围 (九小场所/老旧小区)
- 政策依据 (省厅 2026 通知、市"十四五"消防规划、"十五五"事前预防转型)
- 推进时间表 (2026.9 九小核心区 → 2026.12 重点企业园区 → 2027 全域)
- 商业模式分型 (九小"套餐让利·免费赋能" vs 重点单位"按需定制·按需计费")
- 保障/背书 (专班、7×24 运维、人保承保 财产险2000万/人身险20万)
No number was fabricated; every figure traced to a doc in the zip.

## 4. Rewrite pages in an existing deck (build_deck.js)

- First read the script header: helper signatures (header/card/chip/bullets/ph/footer), `C` palette, W/H/M/CW constants. Write new blocks ONLY with existing helpers — keeps style uniform.
- Each page is one IIFE block ending in `})();`. Replace whole blocks with `patch` mode=replace (old_string = entire old block).
- **Block order == slide order == footer number.** Swapping two blocks (e.g. 市场空间 before 营销路径) reorders slides AND renumbers footers automatically — no separate renumber pass.
- Layout math: compute card widths from CW (`sw = (CW - 3*gap)/4`), y-positions stacked so sections never collide (e.g. big-numbers 1.4–2.65, table 3.25–5.35, policy bar 5.7–6.65, footer 7.08). Dense boxes get `fit: "shrink"`.

## 5. Rebuild + verify

```
cd <deck dir> && NODE_PATH=$(npm root -g) node build_deck.js
python3 qa_check.py          # structural + keyword checks
```
- Keyword checker may MISS strings from replaced content — expected after a rewrite, don't chase it.
- Confirm final page count unchanged, then dump the two new pages (text + table cells) to verify content landed.
- Still cannot auto-render visually (LibreOffice headless hangs on this machine): tell the user which pages are densest and ask them to eyeball, exactly like the base workflow.
