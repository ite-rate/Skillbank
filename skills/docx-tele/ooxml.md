# Office Open XML 技术参考

**重要：开始前请完整阅读本文档。** 本文档包含：
- [技术准则](#技术准则) - Schema 合规规则和验证要求
- [文档内容模式](#文档内容模式) - 标题、列表、表格、格式等 XML 模式
- [文档库（Python）](#文档库python) - 推荐的 OOXML 操作方式，可自动完成基础设施配置
- [修订痕迹（Redlining）](#修订痕迹redlining) - 实现修订痕迹的 XML 模式
- **[OMML 数学公式](ooml-math-guide.md)** — 按需加载：LaTeX 公式转 OMML 注入 docx，含元素速查和代码模板

## 技术准则

### Schema 合规
- **`<w:pPr>` 中的元素顺序**：`<w:pStyle>`、`<w:numPr>`、`<w:spacing>`、`<w:ind>`、`<w:jc>`
- **空白字符**：如果 `<w:t>` 元素前后包含空格，添加 `xml:space='preserve'`
- **Unicode**：ASCII 内容中的字符需要转义：`"` 变为 `&#8220;`
  - **字符编码参考**：弯引号 `""` 变为 `&#8220;&#8221;`，撇号 `'` 变为 `&#8217;`，长破折号 `—` 变为 `&#8212;`
- **修订痕迹**：在 `<w:r>` 元素外使用带 `w:author="TeleAgent"` 的 `<w:del>` 和 `<w:ins>` 标签
  - **关键**：`<w:ins>` 用 `</w:ins>` 关闭，`<w:del>` 用 `</w:del>` 关闭，不要混用
  - **RSID 必须是 8 位十六进制**：使用类似 `00AB1234` 的值（仅包含 0-9、A-F）
  - **trackRevisions 位置**：在 settings.xml 的 `<w:proofState>` 之后添加 `<w:trackRevisions/>`
- **图片**：添加到 `word/media/`，在 `document.xml` 中引用，并设置尺寸以避免溢出

## 文档内容模式

### 基本结构
```xml
<w:p>
  <w:r><w:t>Text content</w:t></w:r>
</w:p>
```

### 标题与样式
```xml
<w:p>
  <w:pPr>
    <w:pStyle w:val="Title"/>
    <w:jc w:val="center"/>
  </w:pPr>
  <w:r><w:t>document_impl Title</w:t></w:r>
</w:p>

<w:p>
  <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
  <w:r><w:t>Section Heading</w:t></w:r>
</w:p>
```

### 文本格式
```xml
<!-- Bold -->
<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t>Bold</w:t></w:r>
<!-- Italic -->
<w:r><w:rPr><w:i/><w:iCs/></w:rPr><w:t>Italic</w:t></w:r>
<!-- Underline -->
<w:r><w:rPr><w:u w:val="single"/></w:rPr><w:t>Underlined</w:t></w:r>
<!-- Highlight -->
<w:r><w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>Highlighted</w:t></w:r>
```

### 列表
```xml
<!-- Numbered list -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="ListParagraph"/>
    <w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>
    <w:spacing w:before="240"/>
  </w:pPr>
  <w:r><w:t>First item</w:t></w:r>
</w:p>

<!-- Restart numbered list at 1 - use different numId -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="ListParagraph"/>
    <w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr>
    <w:spacing w:before="240"/>
  </w:pPr>
  <w:r><w:t>New list item 1</w:t></w:r>
</w:p>

<!-- Bullet list (level 2) -->
<w:p>
  <w:pPr>
    <w:pStyle w:val="ListParagraph"/>
    <w:numPr><w:ilvl w:val="1"/><w:numId w:val="1"/></w:numPr>
    <w:spacing w:before="240"/>
    <w:ind w:left="900"/>
  </w:pPr>
  <w:r><w:t>Bullet item</w:t></w:r>
</w:p>
```

### 表格
```xml
<w:tbl>
  <w:tblPr>
    <w:tblStyle w:val="TableGrid"/>
    <w:tblW w:w="0" w:type="auto"/>
  </w:tblPr>
  <w:tblGrid>
    <w:gridCol w:w="4675"/><w:gridCol w:w="4675"/>
  </w:tblGrid>
  <w:tr>
    <w:tc>
      <w:tcPr><w:tcW w:w="4675" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>Cell 1</w:t></w:r></w:p>
    </w:tc>
    <w:tc>
      <w:tcPr><w:tcW w:w="4675" w:type="dxa"/></w:tcPr>
      <w:p><w:r><w:t>Cell 2</w:t></w:r></w:p>
    </w:tc>
  </w:tr>
</w:tbl>
```

### 布局
```xml
<!-- Page break before new section (common pattern) -->
<w:p>
  <w:r>
    <w:br w:type="page"/>
  </w:r>
</w:p>
<w:p>
  <w:pPr>
    <w:pStyle w:val="Heading1"/>
  </w:pPr>
  <w:r>
    <w:t>New Section Title</w:t>
  </w:r>
</w:p>

<!-- Centered paragraph -->
<w:p>
  <w:pPr>
    <w:spacing w:before="240" w:after="0"/>
    <w:jc w:val="center"/>
  </w:pPr>
  <w:r><w:t>Centered text</w:t></w:r>
</w:p>

<!-- Font change - paragraph level (applies to all runs) -->
<w:p>
  <w:pPr>
    <w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/></w:rPr>
  </w:pPr>
  <w:r><w:t>Monospace text</w:t></w:r>
</w:p>

<!-- Font change - run level (specific to this text) -->
<w:p>
  <w:r>
    <w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/></w:rPr>
    <w:t>This text is Courier New</w:t>
  </w:r>
  <w:r><w:t> and this text uses default font</w:t></w:r>
</w:p>
```

## 文件更新

添加内容时，请更新这些文件：

**`word/_rels/document.xml.rels`:**
```xml
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>
```

**`[Content_Types].xml`:**
```xml
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
```

### 图片
**关键**：计算尺寸以防止页面溢出，并保持宽高比。

```xml
<!-- Minimal required structure -->
<w:p>
  <w:r>
    <w:drawing>
      <wp:inline>
        <wp:extent cx="2743200" cy="1828800"/>
        <wp:docPr id="1" name="Picture 1"/>
        <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:nvPicPr>
                <pic:cNvPr id="0" name="image1.png"/>
                <pic:cNvPicPr/>
              </pic:nvPicPr>
              <pic:blipFill>
                <a:blip r:embed="rId5"/>
                <!-- Add for stretch fill with aspect ratio preservation -->
                <a:stretch>
                  <a:fillRect/>
                </a:stretch>
              </pic:blipFill>
              <pic:spPr>
                <a:xfrm>
                  <a:ext cx="2743200" cy="1828800"/>
                </a:xfrm>
                <a:prstGeom prst="rect"/>
              </pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>
```

### 链接（Hyperlinks）

**重要**：所有超链接（内部和外部）都要求在 styles.xml 中定义 Hyperlink 样式。没有该样式时，链接会显示为普通文本，而不是蓝色带下划线的可点击链接。

**外部链接：**
```xml
<!-- In document.xml -->
<w:hyperlink r:id="rId5">
  <w:r>
    <w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>
    <w:t>Link Text</w:t>
  </w:r>
</w:hyperlink>

<!-- In word/_rels/document.xml.rels -->
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" 
              Target="https://www.example.com/" TargetMode="External"/>
```

**内部链接：**

```xml
<!-- Link to bookmark -->
<w:hyperlink w:anchor="myBookmark">
  <w:r>
    <w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>
    <w:t>Link Text</w:t>
  </w:r>
</w:hyperlink>

<!-- Bookmark target -->
<w:bookmarkStart w:id="0" w:name="myBookmark"/>
<w:r><w:t>Target content</w:t></w:r>
<w:bookmarkEnd w:id="0"/>
```

**超链接样式（styles.xml 中必需）：**
```xml
<w:style w:type="character" w:styleId="Hyperlink">
  <w:name w:val="Hyperlink"/>
  <w:basedOn w:val="DefaultParagraphFont"/>
  <w:uiPriority w:val="99"/>
  <w:unhideWhenUsed/>
  <w:rPr>
    <w:color w:val="467886" w:themeColor="hyperlink"/>
    <w:u w:val="single"/>
  </w:rPr>
</w:style>
```

## 文档库（Python）

所有修订痕迹和批注都使用 `scripts/document_workflow.py` 中的 document_impl 类。它会自动处理基础设施配置（people.xml、RSID、settings.xml、批注文件、关系、内容类型）。只有在库不支持的复杂场景中，才直接操作 XML。

**处理 Unicode 和实体：**
- **搜索**：实体写法和 Unicode 字符都可使用；`contains="&#8220;Company"` 和 `contains="\u201cCompany"` 能找到同一段文本
- **替换**：可使用实体（`&#8220;`）或 Unicode（`\u201c`）；两者都可工作，并会根据文件编码适当转换（ascii → 实体，utf-8 → Unicode）

### 初始化

**查找 docx skill 根目录**（包含 `scripts/` 和 `ooxml/` 的目录）：
```bash
# Search for document_workflow.py to locate the skill root
# Note: /mnt/skills is used here as an example; check your context for the actual location
find /mnt/skills -name "document_workflow.py" -path "*/docx/scripts/*" 2>/dev/null | head -1
# Example output: /mnt/skills/docx/scripts/document_workflow.py
# Skill root is: /mnt/skills/docx
```

**运行脚本时将 PYTHONPATH** 设置为 docx skill 根目录：
```bash
PYTHONPATH=/mnt/skills/docx python your_script.py
```
在 Windows PowerShell 中：
```powershell
$env:PYTHONPATH="C:\path\to\docx"; $env:PYTHONUTF8="1"; python your_script.py
```

**在你的脚本中**，从 skill 根目录导入：
```python
from scripts.document_workflow import document_impl, docx_xml_editor_impl

# Basic initialization (automatically creates temp copy and sets up infrastructure)
doc = document_impl('unpacked')

# Customize author and initials
doc = document_impl('unpacked', author="John Doe", initials="JD")

# Enable track revisions mode
doc = document_impl('unpacked', track_revisions=True)

# Specify custom RSID (auto-generated if not provided)
doc = document_impl('unpacked', rsid="07DC5ECB")
```

### 创建修订痕迹

**关键**：只标记实际变化的文本。所有未变化文本都应保留在 `<w:del>`/`<w:ins>` 标签之外。把未变化文本也标成修订会显得不专业，并增加审阅难度。

**属性处理**：document_impl 类会自动向新元素注入属性（w:id、w:date、w:rsidR、w:rsidDel、w16du:dateUtc、xml:space）。保留原文中未变化文本时，应复制带有既有属性的原始 `<w:r>` 元素，以保持文档完整性。

**方法选择指南**：
- **给普通文本添加自己的修改**：使用带 `<w:del>`/`<w:ins>` 标签的 `replace_node_impl()`；如果要删除整个 `<w:r>` 或 `<w:p>` 元素，可使用 `suggest_deletion_impl()`
- **局部修改其他作者的修订**：使用 `replace_node_impl()`，将你的修改嵌套在对方的 `<w:ins>`/`<w:del>` 内
- **完整拒绝其他作者的插入**：对 `<w:ins>` 元素使用 `revert_insertion_impl()`（不要用 `suggest_deletion_impl()`）
- **完整拒绝其他作者的删除**：对 `<w:del>` 元素使用 `revert_deletion_impl()`，通过修订痕迹恢复被删除内容

```python
# Minimal edit - change one word: "The report is monthly" → "The report is quarterly"
# Original: <w:r w:rsidR="00AB12CD"><w:rPr><w:rFonts w:ascii="Calibri"/></w:rPr><w:t>The report is monthly</w:t></w:r>
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="The report is monthly")
rpr = tags[0].toxml() if (tags := node.getElementsByTagName("w:rPr")) else ""
replacement = f'<w:r w:rsidR="00AB12CD">{rpr}<w:t>The report is </w:t></w:r><w:del><w:r>{rpr}<w:delText>monthly</w:delText></w:r></w:del><w:ins><w:r>{rpr}<w:t>quarterly</w:t></w:r></w:ins>'
doc["word/document.xml"].replace_node_impl(node, replacement)

# Minimal edit - change number: "within 30 days" → "within 45 days"
# Original: <w:r w:rsidR="00XYZ789"><w:rPr><w:rFonts w:ascii="Calibri"/></w:rPr><w:t>within 30 days</w:t></w:r>
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="within 30 days")
rpr = tags[0].toxml() if (tags := node.getElementsByTagName("w:rPr")) else ""
replacement = f'<w:r w:rsidR="00XYZ789">{rpr}<w:t>within </w:t></w:r><w:del><w:r>{rpr}<w:delText>30</w:delText></w:r></w:del><w:ins><w:r>{rpr}<w:t>45</w:t></w:r></w:ins><w:r w:rsidR="00XYZ789">{rpr}<w:t> days</w:t></w:r>'
doc["word/document.xml"].replace_node_impl(node, replacement)

# Complete replacement - preserve formatting even when replacing all text
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="apple")
rpr = tags[0].toxml() if (tags := node.getElementsByTagName("w:rPr")) else ""
replacement = f'<w:del><w:r>{rpr}<w:delText>apple</w:delText></w:r></w:del><w:ins><w:r>{rpr}<w:t>banana orange</w:t></w:r></w:ins>'
doc["word/document.xml"].replace_node_impl(node, replacement)

# Insert new content (no attributes needed - auto-injected)
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="existing text")
doc["word/document.xml"].insert_after_impl(node, '<w:ins><w:r><w:t>new text</w:t></w:r></w:ins>')

# Partially delete another author's insertion
# Original: <w:ins w:author="Jane Smith" w:date="..."><w:r><w:t>quarterly financial report</w:t></w:r></w:ins>
# Goal: Delete only "financial" to make it "quarterly report"
node = doc["word/document.xml"].get_node_impl(tag="w:ins", attrs={"w:id": "5"})
# IMPORTANT: Preserve w:author="Jane Smith" on the outer <w:ins> to maintain authorship
replacement = '''<w:ins w:author="Jane Smith" w:date="2025-01-15T10:00:00Z">
  <w:r><w:t>quarterly </w:t></w:r>
  <w:del><w:r><w:delText>financial </w:delText></w:r></w:del>
  <w:r><w:t>report</w:t></w:r>
</w:ins>'''
doc["word/document.xml"].replace_node_impl(node, replacement)

# Change part of another author's insertion
# Original: <w:ins w:author="Jane Smith"><w:r><w:t>in silence, safe and sound</w:t></w:r></w:ins>
# Goal: Change "safe and sound" to "soft and unbound"
node = doc["word/document.xml"].get_node_impl(tag="w:ins", attrs={"w:id": "8"})
replacement = f'''<w:ins w:author="Jane Smith" w:date="2025-01-15T10:00:00Z">
  <w:r><w:t>in silence, </w:t></w:r>
</w:ins>
<w:ins>
  <w:r><w:t>soft and unbound</w:t></w:r>
</w:ins>
<w:ins w:author="Jane Smith" w:date="2025-01-15T10:00:00Z">
  <w:del><w:r><w:delText>safe and sound</w:delText></w:r></w:del>
</w:ins>'''
doc["word/document.xml"].replace_node_impl(node, replacement)

# Delete entire run (use only when deleting all content; use replace_node_impl for partial deletions)
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="text to delete")
doc["word/document.xml"].suggest_deletion_impl(node)

# Delete entire paragraph (in-place, handles both regular and numbered list paragraphs)
para = doc["word/document.xml"].get_node_impl(tag="w:p", contains="paragraph to delete")
doc["word/document.xml"].suggest_deletion_impl(para)

# Add new numbered list item
target_para = doc["word/document.xml"].get_node_impl(tag="w:p", contains="existing list item")
pPr = tags[0].toxml() if (tags := target_para.getElementsByTagName("w:pPr")) else ""
new_item = f'<w:p>{pPr}<w:r><w:t>New item</w:t></w:r></w:p>'
tracked_para = docx_xml_editor_impl.suggest_paragraph_impl(new_item)
doc["word/document.xml"].insert_after_impl(target_para, tracked_para)
# Optional: add spacing paragraph before content for better visual separation
# spacing = docx_xml_editor_impl.suggest_paragraph_impl('<w:p><w:pPr><w:pStyle w:val="ListParagraph"/></w:pPr></w:p>')
# doc["word/document.xml"].insert_after_impl(target_para, spacing + tracked_para)
```

### 添加批注

```python
# Add comment spanning two existing tracked changes
# Note: w:id is auto-generated. Only search by w:id if you know it from XML inspection
start_node = doc["word/document.xml"].get_node_impl(tag="w:del", attrs={"w:id": "1"})
end_node = doc["word/document.xml"].get_node_impl(tag="w:ins", attrs={"w:id": "2"})
doc.add_comment_impl(start=start_node, end=end_node, text="Explanation of this change")

# Add comment on a paragraph
para = doc["word/document.xml"].get_node_impl(tag="w:p", contains="paragraph text")
doc.add_comment_impl(start=para, end=para, text="Comment on this paragraph")

# Add comment on newly created tracked change
# First create the tracked change
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="old")
new_nodes = doc["word/document.xml"].replace_node_impl(
    node,
    '<w:del><w:r><w:delText>old</w:delText></w:r></w:del><w:ins><w:r><w:t>new</w:t></w:r></w:ins>'
)
# Then add comment on the newly created elements
# new_nodes[0] is the <w:del>, new_nodes[1] is the <w:ins>
doc.add_comment_impl(start=new_nodes[0], end=new_nodes[1], text="Changed old to new per requirements")

# Reply to existing comment
doc.reply_to_comment_impl(parent_comment_id=0, text="I agree with this change")
```

### 拒绝修订痕迹

**重要**：使用 `revert_insertion_impl()` 拒绝插入，使用 `revert_deletion_impl()` 通过修订痕迹恢复删除。`suggest_deletion_impl()` 只用于普通的未标记内容。

```python
# Reject insertion (wraps it in deletion)
# Use this when another author inserted text that you want to delete
ins = doc["word/document.xml"].get_node_impl(tag="w:ins", attrs={"w:id": "5"})
nodes = doc["word/document.xml"].revert_insertion_impl(ins)  # Returns [ins]

# Reject deletion (creates insertion to restore deleted content)
# Use this when another author deleted text that you want to restore
del_elem = doc["word/document.xml"].get_node_impl(tag="w:del", attrs={"w:id": "3"})
nodes = doc["word/document.xml"].revert_deletion_impl(del_elem)  # Returns [del_elem, new_ins]

# Reject all insertions in a paragraph
para = doc["word/document.xml"].get_node_impl(tag="w:p", contains="paragraph text")
nodes = doc["word/document.xml"].revert_insertion_impl(para)  # Returns [para]

# Reject all deletions in a paragraph
para = doc["word/document.xml"].get_node_impl(tag="w:p", contains="paragraph text")
nodes = doc["word/document.xml"].revert_deletion_impl(para)  # Returns [para]
```

### 插入图片

**关键**：document_impl 类操作的是 `doc.unpacked_path` 下的临时副本。始终把图片复制到这个临时目录，不要复制到原始解包目录。

```python
from PIL import Image
import shutil, os

# Initialize document first
doc = document_impl('unpacked')

# Copy image and calculate full-width dimensions with aspect ratio
media_dir = os.path.join(doc.unpacked_path, 'word/media')
os.makedirs(media_dir, exist_ok=True)
shutil.copy('image.png', os.path.join(media_dir, 'image1.png'))
img = Image.open(os.path.join(media_dir, 'image1.png'))
width_emus = int(6.5 * 914400)  # 6.5" usable width, 914400 EMUs/inch
height_emus = int(width_emus * img.size[1] / img.size[0])

# Add relationship and content type
rels_editor = doc['word/_rels/document.xml.rels']
next_rid = rels_editor.get_next_rid_impl()
rels_editor.append_to_impl(rels_editor.dom.documentElement,
    f'<Relationship Id="{next_rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>')
doc['[Content_Types].xml'].append_to_impl(doc['[Content_Types].xml'].dom.documentElement,
    '<Default Extension="png" ContentType="image/png"/>')

# Insert image
node = doc["word/document.xml"].get_node_impl(tag="w:p", line_number=100)
doc["word/document.xml"].insert_after_impl(node, f'''<w:p>
  <w:r>
    <w:drawing>
      <wp:inline distT="0" distB="0" distL="0" distR="0">
        <wp:extent cx="{width_emus}" cy="{height_emus}"/>
        <wp:docPr id="1" name="Picture 1"/>
        <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
          <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
            <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:nvPicPr><pic:cNvPr id="1" name="image1.png"/><pic:cNvPicPr/></pic:nvPicPr>
              <pic:blipFill><a:blip r:embed="{next_rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
              <pic:spPr><a:xfrm><a:ext cx="{width_emus}" cy="{height_emus}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
            </pic:pic>
          </a:graphicData>
        </a:graphic>
      </wp:inline>
    </w:drawing>
  </w:r>
</w:p>''')
```

### 获取节点

```python
# By text content
node = doc["word/document.xml"].get_node_impl(tag="w:p", contains="specific text")

# By line range
para = doc["word/document.xml"].get_node_impl(tag="w:p", line_number=range(100, 150))

# By attributes
node = doc["word/document.xml"].get_node_impl(tag="w:del", attrs={"w:id": "1"})

# By exact line number (must be line number where tag opens)
para = doc["word/document.xml"].get_node_impl(tag="w:p", line_number=42)

# Combine filters
node = doc["word/document.xml"].get_node_impl(tag="w:r", line_number=range(40, 60), contains="text")

# Disambiguate when text appears multiple times - add line_number range
node = doc["word/document.xml"].get_node_impl(tag="w:r", contains="Section", line_number=range(2400, 2500))
```

### 保存

```python
# Save with automatic validation (copies back to original directory)
doc.save_impl()  # Validates by default, raises error if validation fails

# Save to different location
doc.save_impl('modified-unpacked')

# Skip validation (debugging only - needing this in production indicates XML issues)
doc.save_impl(validate_impl=False)
```

### 直接 DOM 操作

对于库未覆盖的复杂场景：

```python
# Access any XML file
editor = doc["word/document.xml"]
editor = doc["word/comments.xml"]

# Direct DOM access (defusedxml.minidom.document_impl)
node = doc["word/document.xml"].get_node_impl(tag="w:p", line_number=5)
parent = node.parentNode
parent.removeChild(node)
parent.appendChild(node)  # Move to end

# General document manipulation (without tracked changes)
old_node = doc["word/document.xml"].get_node_impl(tag="w:p", contains="original text")
doc["word/document.xml"].replace_node_impl(old_node, "<w:p><w:r><w:t>replacement text</w:t></w:r></w:p>")

# Multiple insertions - use return value to maintain order
node = doc["word/document.xml"].get_node_impl(tag="w:r", line_number=100)
nodes = doc["word/document.xml"].insert_after_impl(node, "<w:r><w:t>A</w:t></w:r>")
nodes = doc["word/document.xml"].insert_after_impl(nodes[-1], "<w:r><w:t>B</w:t></w:r>")
nodes = doc["word/document.xml"].insert_after_impl(nodes[-1], "<w:r><w:t>C</w:t></w:r>")
# Results in: original_node, A, B, C
```

## 修订痕迹（Redlining）

**所有修订痕迹都使用上方的 document_impl 类。** 下方模式仅供构造替换 XML 字符串时参考。

### 验证规则
验证器会检查：在回退 TeleAgent 的修改后，文档文本是否与原文一致。这意味着：
- **不要修改其他作者 `<w:ins>` 或 `<w:del>` 标签内的文本**
- **删除其他作者的插入时，始终使用嵌套删除**
- **每一处编辑都必须用 `<w:ins>` 或 `<w:del>` 正确标记**

### 修订痕迹模式

**关键规则**：
1. 不要修改其他作者修订痕迹内部的内容。始终使用嵌套删除。
2. **XML 结构**：始终把 `<w:del>` 和 `<w:ins>` 放在段落层级，并让它们包含完整的 `<w:r>` 元素。不要嵌套在 `<w:r>` 元素内部，否则会产生无效 XML，破坏文档处理。

**文本插入：**
```xml
<w:ins w:id="1" w:author="TeleAgent" w:date="2025-07-30T23:05:00Z" w16du:dateUtc="2025-07-31T06:05:00Z">
  <w:r w:rsidR="00792858">
    <w:t>inserted text</w:t>
  </w:r>
</w:ins>
```

**文本删除：**
```xml
<w:del w:id="2" w:author="TeleAgent" w:date="2025-07-30T23:05:00Z" w16du:dateUtc="2025-07-31T06:05:00Z">
  <w:r w:rsidDel="00792858">
    <w:delText>deleted text</w:delText>
  </w:r>
</w:del>
```

**删除其他作者的插入（必须使用嵌套结构）：**
```xml
<!-- Nest deletion inside the original insertion -->
<w:ins w:author="Jane Smith" w:id="16">
  <w:del w:author="TeleAgent" w:id="40">
    <w:r><w:delText>monthly</w:delText></w:r>
  </w:del>
</w:ins>
<w:ins w:author="TeleAgent" w:id="41">
  <w:r><w:t>weekly</w:t></w:r>
</w:ins>
```

**恢复其他作者的删除：**
```xml
<!-- Leave their deletion unchanged, add new insertion after it -->
<w:del w:author="Jane Smith" w:id="50">
  <w:r><w:delText>within 30 days</w:delText></w:r>
</w:del>
<w:ins w:author="TeleAgent" w:id="51">
  <w:r><w:t>within 30 days</w:t></w:r>
</w:ins>
```
