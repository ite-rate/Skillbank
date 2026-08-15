# Office Open XML Technical Reference for PowerPoint

**Important: Read this entire document before starting.** Critical XML schema rules and formatting requirements are covered throughout. Incorrect implementation can create invalid PPTX files that PowerPoint cannot open.

## Technical Guidelines

### Schema Compliance
- **Element ordering in `<p:txBody>`**: `<a:bodyPr>`, `<a:lstStyle>`, `<a:p>`
- **Whitespace**: Add `xml:space='preserve'` to `<a:t>` elements with leading/trailing spaces
- **Unicode**: Escape characters in ASCII content: `"` becomes `&#8220;`
- **Images**: Add to `ppt/media/`, reference in slide XML, set dimensions to fit slide bounds
- **Relationships**: Update `ppt/slides/_rels/slideN.xml.rels` for each slide's resources
- **Dirty attribute**: Add `dirty="0"` to `<a:rPr>` and `<a:endParaRPr>` elements to indicate clean state

## Presentation Structure

### Basic Slide Structure
```xml
<!-- ppt/slides/slide1.xml -->
<p:sld>
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>...</p:nvGrpSpPr>
      <p:grpSpPr>...</p:grpSpPr>
      <!-- Shapes go here -->
    </p:spTree>
  </p:cSld>
</p:sld>
```

### Text Box / Shape with Text
```xml
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="2" name="Title"/>
    <p:cNvSpPr>
      <a:spLocks noGrp="1"/>
    </p:cNvSpPr>
    <p:nvPr>
      <p:ph type="ctrTitle"/>
    </p:nvPr>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="838200" y="365125"/>
      <a:ext cx="7772400" cy="1470025"/>
    </a:xfrm>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p>
      <a:r>
        <a:t>Slide Title</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### Text Formatting
```xml
<!-- Bold -->
<a:r>
  <a:rPr b="1"/>
  <a:t>Bold Text</a:t>
</a:r>

<!-- Italic -->
<a:r>
  <a:rPr i="1"/>
  <a:t>Italic Text</a:t>
</a:r>

<!-- Underline -->
<a:r>
  <a:rPr u="sng"/>
  <a:t>Underlined</a:t>
</a:r>

<!-- Highlight -->
<a:r>
  <a:rPr>
    <a:highlight>
      <a:srgbClr val="FFFF00"/>
    </a:highlight>
  </a:rPr>
  <a:t>Highlighted Text</a:t>
</a:r>

<!-- Font and Size -->
<a:r>
  <a:rPr sz="2400" typeface="Arial">
    <a:solidFill>
      <a:srgbClr val="FF0000"/>
    </a:solidFill>
  </a:rPr>
  <a:t>Colored Arial 24pt</a:t>
</a:r>

<!-- Complete formatting example -->
<a:r>
  <a:rPr lang="en-US" sz="1400" b="1" dirty="0">
    <a:solidFill>
      <a:srgbClr val="FAFAFA"/>
    </a:solidFill>
  </a:rPr>
  <a:t>Formatted text</a:t>
</a:r>
```

### Lists
```xml
<!-- Bullet list -->
<a:p>
  <a:pPr lvl="0">
    <a:buChar char="•"/>
  </a:pPr>
  <a:r>
    <a:t>First bullet point</a:t>
  </a:r>
</a:p>

<!-- Numbered list -->
<a:p>
  <a:pPr lvl="0">
    <a:buAutoNum type="arabicPeriod"/>
  </a:pPr>
  <a:r>
    <a:t>First numbered item</a:t>
  </a:r>
</a:p>

<!-- Second level indent -->
<a:p>
  <a:pPr lvl="1">
    <a:buChar char="•"/>
  </a:pPr>
  <a:r>
    <a:t>Indented bullet</a:t>
  </a:r>
</a:p>
```

### Shapes
```xml
<!-- Rectangle -->
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="3" name="Rectangle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm>
      <a:off x="1000000" y="1000000"/>
      <a:ext cx="3000000" cy="2000000"/>
    </a:xfrm>
    <a:prstGeom prst="rect">
      <a:avLst/>
    </a:prstGeom>
    <a:solidFill>
      <a:srgbClr val="FF0000"/>
    </a:solidFill>
    <a:ln w="25400">
      <a:solidFill>
        <a:srgbClr val="000000"/>
      </a:solidFill>
    </a:ln>
  </p:spPr>
</p:sp>

<!-- Rounded Rectangle -->
<p:sp>
  <p:spPr>
    <a:prstGeom prst="roundRect">
      <a:avLst/>
    </a:prstGeom>
  </p:spPr>
</p:sp>

<!-- Circle/Ellipse -->
<p:sp>
  <p:spPr>
    <a:prstGeom prst="ellipse">
      <a:avLst/>
    </a:prstGeom>
  </p:spPr>
</p:sp>
```

### Images
```xml
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="4" name="Picture">
      <a:hlinkClick r:id="" action="ppaction://media"/>
    </p:cNvPr>
    <p:cNvPicPr>
      <a:picLocks noChangeAspect="1"/>
    </p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="rId2"/>
    <a:stretch>
      <a:fillRect/>
    </a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm>
      <a:off x="1000000" y="1000000"/>
      <a:ext cx="3000000" cy="2000000"/>
    </a:xfrm>
    <a:prstGeom prst="rect">
      <a:avLst/>
    </a:prstGeom>
  </p:spPr>
</p:pic>
```

### Tables
```xml
<p:graphicFrame>
  <p:nvGraphicFramePr>
    <p:cNvPr id="5" name="Table"/>
    <p:cNvGraphicFramePr>
      <a:graphicFrameLocks noGrp="1"/>
    </p:cNvGraphicFramePr>
    <p:nvPr/>
  </p:nvGraphicFramePr>
  <p:xfrm>
    <a:off x="1000000" y="1000000"/>
    <a:ext cx="6000000" cy="2000000"/>
  </p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">
      <a:tbl>
        <a:tblGrid>
          <a:gridCol w="3000000"/>
          <a:gridCol w="3000000"/>
        </a:tblGrid>
        <a:tr h="500000">
          <a:tc>
            <a:txBody>
              <a:bodyPr/>
              <a:lstStyle/>
              <a:p>
                <a:r>
                  <a:t>Cell 1</a:t>
                </a:r>
              </a:p>
            </a:txBody>
          </a:tc>
          <a:tc>
            <a:txBody>
              <a:bodyPr/>
              <a:lstStyle/>
              <a:p>
                <a:r>
                  <a:t>Cell 2</a:t>
                </a:r>
              </a:p>
            </a:txBody>
          </a:tc>
        </a:tr>
      </a:tbl>
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

### Slide Layouts

```xml
<!-- Title Slide Layout -->
<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="ctrTitle"/>
    </p:nvPr>
  </p:nvSpPr>
  <!-- Title content -->
</p:sp>

<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="subTitle" idx="1"/>
    </p:nvPr>
  </p:nvSpPr>
  <!-- Subtitle content -->
</p:sp>

<!-- Content Slide Layout -->
<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="title"/>
    </p:nvPr>
  </p:nvSpPr>
  <!-- Slide title -->
</p:sp>

<p:sp>
  <p:nvSpPr>
    <p:nvPr>
      <p:ph type="body" idx="1"/>
    </p:nvPr>
  </p:nvSpPr>
  <!-- Content body -->
</p:sp>
```

## File Updates

When adding content, update these files:

**`ppt/_rels/presentation.xml.rels`:**
```xml
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
```

**`ppt/slides/_rels/slide1.xml.rels`:**
```xml
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/>
```

**`[Content_Types].xml`:**
```xml
<Default Extension="png" ContentType="image/png"/>
<Default Extension="jpg" ContentType="image/jpeg"/>
<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
```

**`ppt/presentation.xml`:**
```xml
<p:sldIdLst>
  <p:sldId id="256" r:id="rId1"/>
  <p:sldId id="257" r:id="rId2"/>
</p:sldIdLst>
```

**`docProps/app.xml`:** Update slide count and statistics
```xml
<Slides>2</Slides>
<Paragraphs>10</Paragraphs>
<Words>50</Words>
```

## Slide Operations

### Adding a New Slide
When adding a slide to the end of the presentation:

1. **Create the slide file** (`ppt/slides/slideN.xml`)
2. **Update `[Content_Types].xml`**: Add Override for the new slide
3. **Update `ppt/_rels/presentation.xml.rels`**: Add relationship for the new slide
4. **Update `ppt/presentation.xml`**: Add slide ID to `<p:sldIdLst>`
5. **Create slide relationships** (`ppt/slides/_rels/slideN.xml.rels`) if needed
6. **Update `docProps/app.xml`**: Increment slide count and update statistics (if present)

### Duplicating a Slide
1. Copy the source slide XML file with a new name
2. Update all IDs in the new slide to be unique
3. Follow the "Adding a New Slide" steps above
4. **CRITICAL**: Remove or update any notes slide references in `_rels` files
5. Remove references to unused media files

### Reordering Slides
1. **Update `ppt/presentation.xml`**: Reorder `<p:sldId>` elements in `<p:sldIdLst>`
2. The order of `<p:sldId>` elements determines slide order
3. Keep slide IDs and relationship IDs unchanged

Example:
```xml
<!-- Original order -->
<p:sldIdLst>
  <p:sldId id="256" r:id="rId2"/>
  <p:sldId id="257" r:id="rId3"/>
  <p:sldId id="258" r:id="rId4"/>
</p:sldIdLst>

<!-- After moving slide 3 to position 2 -->
<p:sldIdLst>
  <p:sldId id="256" r:id="rId2"/>
  <p:sldId id="258" r:id="rId4"/>
  <p:sldId id="257" r:id="rId3"/>
</p:sldIdLst>
```

### Deleting a Slide
1. **Remove from `ppt/presentation.xml`**: Delete the `<p:sldId>` entry
2. **Remove from `ppt/_rels/presentation.xml.rels`**: Delete the relationship
3. **Remove from `[Content_Types].xml`**: Delete the Override entry
4. **Delete files**: Remove `ppt/slides/slideN.xml` and `ppt/slides/_rels/slideN.xml.rels`
5. **Update `docProps/app.xml`**: Decrement slide count and update statistics
6. **Clean up unused media**: Remove orphaned images from `ppt/media/`

Note: Don't renumber remaining slides - keep their original IDs and filenames.


## Common Errors to Avoid

- **Encodings**: Escape unicode characters in ASCII content: `"` becomes `&#8220;`
- **Images**: Add to `ppt/media/` and update relationship files
- **Lists**: Omit bullets from list headers
- **IDs**: Use valid hexadecimal values for UUIDs
- **Themes**: Check all themes in `theme` directory for colors

## Validation Checklist for Template-Based Presentations

### Before Packing, Always:
- **Clean unused resources**: Remove unreferenced media, fonts, and notes directories
- **Fix Content_Types.xml**: Declare ALL slides, layouts, and themes present in the package
- **Fix relationship IDs**: 
   - Remove font embed references if not using embedded fonts
- **Remove broken references**: Check all `_rels` files for references to deleted resources

### Common Template Duplication Pitfalls:
- Multiple slides referencing the same notes slide after duplication
- Image/media references from template slides that no longer exist
- Font embedding references when fonts aren't included
- Missing slideLayout declarations for layouts 12-25
- docProps directory may not unpack - this is optional

## Group Shape Coordinate System（组形状坐标系）

PPT中的 `<p:grpSp>`（Group Shape）包含自己的坐标系。理解这一点对精确编辑甘特图等嵌套结构至关重要。

### 坐标变换原理

```xml
<p:grpSp>
  <p:grpSpPr>
    <a:xfrm>
      <!-- 父坐标系：组的实际位置和大小（相对于slide） -->
      <a:off x="432846" y="2345316"/>    <!-- 组的左上角在slide上的位置 -->
      <a:ext cx="11326308" cy="4200668"/> <!-- 组的实际宽高 -->
      <!-- 子坐标系：子shape使用的坐标范围 -->
      <a:chOff x="454017" y="2396975"/>  <!-- 子坐标原点（通常接近off） -->
      <a:chExt cx="10388794" cy="4200668"/> <!-- 子坐标系的宽高范围 -->
    </a:xfrm>
  </p:grpSpPr>
  <!-- 子shape的坐标是相对于chOff/chExt的 -->
  <p:sp>...</p:sp>
</p:grpSp>
```

### 关键规则

1. **子shape的 `(x, y)` 是组内局部坐标**，不是幻灯片绝对坐标
2. **幻灯片绝对坐标** = `off` + `(child_x - chOff)` × `(ext / chExt)`
   - 简化版（当 `off ≈ chOff` 且 `ext ≈ chExt` 时）：绝对坐标 ≈ off + child_x - chOff
3. **python-pptx 的 `shape.left/top` 返回的是组内局部坐标**，不是slide绝对坐标
4. **inventory.py 报告的 overflow 是基于局部坐标的**，对于group内的shape可能不准确

### 实战建议

- 编辑甘特图时，如果需要让浮动shape精确对齐到表格行，直接在XML中操作坐标（使用OOXML workflow）
- 浮动shape的 `y` 坐标应与对应表格行的 `y` 坐标匹配（考虑行高和垂直偏移）
- 浮动shape的 `x` 和 `cx`（宽度）应根据任务对应的列范围计算

## 从模板中提取品牌图片（Brand Image Extraction）

当需要从参考模板中提取Logo、背景图等品牌元素用于新PPT时，按以下流程操作：

### Step 1: Unpack模板

```bash
python ooxml/scripts/unpack.py template.pptx template-unpacked
```

### Step 2: 列出并识别媒体文件

```bash
ls -la template-unpacked/ppt/media/
```

### Step 3: 在XML中定位图片引用

图片可能在以下位置：
- `ppt/slides/slideN.xml` — 幻灯片中的图片
- `ppt/slideMasters/slideMasterN.xml` — Slide Master中的背景/Logo
- `ppt/slideLayouts/slideLayoutN.xml` — Slide Layout中的装饰元素

```bash
# 查找所有图片引用（r:embed="rIdX" 指向图片）
grep -r 'r:embed.*image' template-unpacked/ppt/slides/
grep -r 'r:embed.*image' template-unpacked/ppt/slideMasters/
grep -r 'r:embed.*image' template-unpacked/ppt/slideLayouts/

# 查找图片的具体位置和尺寸
# 图片以 <p:pic> 元素存在，其中 <a:off> 是位置，<a:ext> 是尺寸
grep -A5 '<p:pic>' template-unpacked/ppt/slides/slide1.xml
```

### Step 4: 从relationship文件确定图片文件名

图片引用通过relationship ID（如 `rId2`）映射到实际文件：

```bash
# 查看幻灯片的relationship文件
cat template-unpacked/ppt/slides/_rels/slide1.xml.rels
```

输出示例：
```xml
<Relationship Id="rId1" Type="...slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="...image" Target="../media/image1.png"/>
<Relationship Id="rId3" Type="...image" Target="../media/image2.png"/>
```

### Step 5: 提取图片位置和尺寸

从slide XML中提取图片的精确位置（用于在新PPT中复用）：

```xml
<!-- 图片在 <p:pic> 元素中 -->
<p:pic>
  <p:spPr>
    <a:xfrm>
      <a:off x="914400" y="228600"/>   <!-- 位置：x=1.0in, y=0.25in -->
      <a:ext cx="1005840" cy="480060"/> <!-- 尺寸：w=1.1in, h=0.525in -->
    </a:xfrm>
  </p:spPr>
  <p:blipFill>
    <a:blip r:embed="rId2"/>           <!-- 指向 image1.png -->
  </p:blipFill>
</p:pic>
```

### Step 6: 在新PPT中复用

将提取的图片复制到工作目录，使用PptxGenJS添加：

```javascript
// 将提取的图片添加到新PPT的每页
slide.addImage({
    path: 'template-unpacked/ppt/media/image1.png',
    x: 1.0,     // 与模板相同的位置（英寸）
    y: 0.25,
    w: 1.1,     // 与模板相同的尺寸
    h: 0.525
});
```

### 注意事项

- **透明背景的Logo**（PNG格式）可以直接复用
- **JPEG背景图**可能有白色背景，注意与新PPT背景色的配合
- **Slide Master中的背景图**通常通过 `<p:bg>` 元素引用，不要与幻灯片中的图片混淆
- 如果模板的Slide Master定义了背景色/渐变，需要在新PPT中通过 `slide.background` 属性设置
- **图片的z-order很重要**：背景图应最先添加（底层），Logo应在内容之上