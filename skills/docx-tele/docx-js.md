# docx-js 高级参考

使用 JavaScript/TypeScript 生成 .docx 文件。

**按需使用**：此文件是高级工具书，不是默认必读材料。仅当 `md_to_js.py` 和 `md-to-js-edit-guide.md` 无法覆盖需求，或者生成/编辑 JS 出错且无法定位原因时，才查阅本文件。

**检索优先**：优先使用 `rg` 或关键词检索定位相关片段，例如 `ImageRun`、`Table`、`TableOfContents`、`Header`、`Footer`、`section`、`PageOrientation`、`VerticalMergeType`、`bookmark`。不要从头到尾完整加载。

## 安装准备
默认假设 `docx` 已全局安装。
如果尚未安装：`npm install -g docx`

```javascript
const { document_impl, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Media, 
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink, 
        InternalHyperlink, TableOfContents, HeadingLevel, BorderStyle, WidthType, TabStopType, 
        TabStopPosition, UnderlineType, ShadingType, VerticalAlign, SymbolRun, PageNumber,
        FootnoteReferenceRun, Footnote, PageBreak } = require('docx');

// Create & Save
const doc = new document_impl({ sections: [{ children: [/* content */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer)); // Node.js
Packer.toBlob(doc).then(blob => { /* download logic */ }); // Browser
```

## 文本与格式
```javascript
// IMPORTANT: Never use \n for line breaks - always use separate Paragraph elements
// ❌ WRONG: new TextRun("Line 1\nLine 2")
// ✅ CORRECT: new Paragraph({ children: [new TextRun("Line 1")] }), new Paragraph({ children: [new TextRun("Line 2")] })

// Basic text with all formatting options
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 200, after: 200 },
  indent: { left: 720, right: 720 },
  children: [
    new TextRun({ text: "Bold", bold: true }),
    new TextRun({ text: "Italic", italics: true }),
    new TextRun({ text: "Underlined", underline: { type: UnderlineType.DOUBLE, color: "FF0000" } }),
    new TextRun({ text: "Colored", color: "FF0000", size: 28, font: "Arial" }), // Arial default
    new TextRun({ text: "Highlighted", highlight: "yellow" }),
    new TextRun({ text: "Strikethrough", strike: true }),
    new TextRun({ text: "x2", superScript: true }),
    new TextRun({ text: "H2O", subScript: true }),
    new TextRun({ text: "SMALL CAPS", smallCaps: true }),
    new SymbolRun({ char: "2022", font: "Symbol" }), // Bullet •
    new SymbolRun({ char: "00A9", font: "Arial" })   // Copyright © - Arial for symbols
  ]
})
```

## 样式与专业排版

```javascript
const doc = new document_impl({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } }, // 12pt default
    paragraphStyles: [
      // document_impl title style - override built-in Title style
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: "000000", font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
      // IMPORTANT: Override built-in heading styles by using their exact IDs
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "000000", font: "Arial" }, // 16pt
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } }, // Required for TOC
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: "000000", font: "Arial" }, // 14pt
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 } },
      // Custom styles use your own IDs
      { id: "myStyle", name: "My Style", basedOn: "Normal",
        run: { size: 28, bold: true, color: "000000" },
        paragraph: { spacing: { after: 120 }, alignment: AlignmentType.CENTER } }
    ],
    characterStyles: [{ id: "myCharStyle", name: "My Char Style",
      run: { color: "FF0000", bold: true, underline: { type: UnderlineType.SINGLE } } }]
  },
  sections: [{
    properties: { page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    children: [
      new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("document_impl Title")] }), // Uses overridden Title style
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Heading 1")] }), // Uses overridden Heading1 style
      new Paragraph({ style: "myStyle", children: [new TextRun("Custom paragraph style")] }),
      new Paragraph({ children: [
        new TextRun("Normal with "),
        new TextRun({ text: "custom char style", style: "myCharStyle" })
      ]})
    ]
  }]
});
```

**专业字体组合：**
- **Arial（标题）+ Arial（正文）** - 兼容性最广，效果干净且正式
- **Times New Roman（标题）+ Arial（正文）** - 经典衬线标题搭配现代无衬线正文
- **Georgia（标题）+ Verdana（正文）** - 适合屏幕阅读，具有清晰的优雅对比

**样式关键原则：**
- **覆盖内建样式**：使用 "Heading1"、"Heading2"、"Heading3" 等精确 ID 来覆盖 Word 的内建标题样式
- **HeadingLevel 常量**：`HeadingLevel.HEADING_1` 使用 "Heading1" 样式，`HeadingLevel.HEADING_2` 使用 "Heading2" 样式，依此类推
- **包含 outlineLevel**：H1 设置 `outlineLevel: 0`，H2 设置 `outlineLevel: 1`，依此类推，以确保目录正常工作
- **使用自定义样式**，不要依赖行内格式，以保持一致性
- **设置默认字体**：通过 `styles.default.document.run.font` 设置；Arial 的通用支持最好
- **建立视觉层级**：使用不同字号区分标题、各级小标题和正文
- **添加合适间距**：使用段落间距中的 `before` 和 `after`
- **谨慎用色**：默认使用黑色（000000），标题和小标题可使用灰阶
- **设置一致页边距**（1440 = 1 英寸，是常用标准）


## 列表（始终使用真正的列表，不要使用 Unicode 项目符号）
```javascript
// Bullets - ALWAYS use the numbering config, NOT unicode symbols
// CRITICAL: Use LevelFormat.BULLET constant, NOT the string "bullet"
const doc = new document_impl({
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "first-numbered-list",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "second-numbered-list", // Different reference = restarts at 1
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [{
    children: [
      // Bullet list items
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("First bullet point")] }),
      new Paragraph({ numbering: { reference: "bullet-list", level: 0 },
        children: [new TextRun("Second bullet point")] }),
      // Numbered list items
      new Paragraph({ numbering: { reference: "first-numbered-list", level: 0 },
        children: [new TextRun("First numbered item")] }),
      new Paragraph({ numbering: { reference: "first-numbered-list", level: 0 },
        children: [new TextRun("Second numbered item")] }),
      // ⚠️ CRITICAL: Different reference = INDEPENDENT list that restarts at 1
      // Same reference = CONTINUES previous numbering
      new Paragraph({ numbering: { reference: "second-numbered-list", level: 0 },
        children: [new TextRun("Starts at 1 again (because different reference)")] })
    ]
  }]
});

// ⚠️ CRITICAL NUMBERING RULE: Each reference creates an INDEPENDENT numbered list
// - Same reference = continues numbering (1, 2, 3... then 4, 5, 6...)
// - Different reference = restarts at 1 (1, 2, 3... then 1, 2, 3...)
// Use unique reference names for each separate numbered section!

// ⚠️ CRITICAL: NEVER use unicode bullets - they create fake lists that don't work properly
// new TextRun("• Item")           // WRONG
// new SymbolRun({ char: "2022" }) // WRONG
// ✅ ALWAYS use numbering config with LevelFormat.BULLET for real Word lists
```

## 表格
```javascript
// Complete table with margins, borders, headers, and bullet points
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

new Table({
  columnWidths: [4680, 4680], // ⚠️ CRITICAL: Set column widths at table level - values in DXA (twentieths of a point)
  margins: { top: 100, bottom: 100, left: 180, right: 180 }, // Set once for all cells
  rows: [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          // ⚠️ CRITICAL: Always use ShadingType.CLEAR to prevent black backgrounds in Word.
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR }, 
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ 
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Header", bold: true, size: 22 })]
          })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          children: [new Paragraph({ 
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "Bullet Points", bold: true, size: 22 })]
          })]
        })
      ]
    }),
    new TableRow({
      children: [
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          children: [new Paragraph({ children: [new TextRun("Regular data")] })]
        }),
        new TableCell({
          borders: cellBorders,
          width: { size: 4680, type: WidthType.DXA }, // ALSO set width on each cell
          children: [
            new Paragraph({ 
              numbering: { reference: "bullet-list", level: 0 },
              children: [new TextRun("First bullet point")] 
            }),
            new Paragraph({ 
              numbering: { reference: "bullet-list", level: 0 },
              children: [new TextRun("Second bullet point")] 
            })
          ]
        })
      ]
    })
  ]
})
```

**重要：表格宽度与边框**
- 同时使用 `columnWidths: [width1, width2, ...]` 数组，并在每个单元格上设置 `width: { size: X, type: WidthType.DXA }`
- 数值单位为 DXA（1/20 磅）：1440 = 1 英寸；Letter 纸在 1 英寸页边距下可用宽度为 9360 DXA
- 边框应应用到各个 `TableCell`，不要应用到 `Table` 本身

**预计算列宽（Letter 纸，1 英寸页边距，总宽 9360 DXA）：**
- **2 列：** `columnWidths: [4680, 4680]`（等宽）
- **3 列：** `columnWidths: [3120, 3120, 3120]`（等宽）

## 链接与导航
```javascript
// TOC (requires headings) - CRITICAL: Use HeadingLevel only, NOT custom styles
// ❌ WRONG: new Paragraph({ heading: HeadingLevel.HEADING_1, style: "customHeader", children: [new TextRun("Title")] })
// ✅ CORRECT: new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Title")] })
new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),

// External link
new Paragraph({
  children: [new ExternalHyperlink({
    children: [new TextRun({ text: "Google", style: "Hyperlink" })],
    link: "https://www.google.com"
  })]
}),

// Internal link & bookmark
new Paragraph({
  children: [new InternalHyperlink({
    children: [new TextRun({ text: "Go to Section", style: "Hyperlink" })],
    anchor: "section1"
  })]
}),
new Paragraph({
  children: [new TextRun("Section Content")],
  bookmark: { id: "section1", name: "section1" }
}),
```

**目录的重要限制**：`TableOfContents` 创建的是目录字段占位符。在许多环境中，打开文件时不会自动渲染目录条目。如果需要不依赖 Win COM 的确定性结果，请运行：

`python scripts/render_toc_static.py <file.docx>`

该命令会根据标题把目录转换为静态可点击条目。页码会刻意不渲染。

## 图片与媒体
```javascript
// Basic image with sizing & positioning
// CRITICAL: Always specify 'type' parameter - it's REQUIRED for ImageRun
new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png", // NEW REQUIREMENT: Must specify image type (png, jpg, jpeg, gif, bmp, svg)
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150, rotation: 0 }, // rotation in degrees
    altText: { title: "Logo", description: "Company logo", name: "Name" } // IMPORTANT: All three fields are required
  })]
})
```

## 分页符
```javascript
// Manual page break
new Paragraph({ children: [new PageBreak()] }),

// Page break before paragraph
new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun("This starts on a new page")]
})

// ⚠️ CRITICAL: NEVER use PageBreak standalone - it will create invalid XML that Word cannot open
// ❌ WRONG: new PageBreak() 
// ✅ CORRECT: new Paragraph({ children: [new PageBreak()] })
```

## 页眉、页脚与页面设置
```javascript
const doc = new document_impl({
  sections: [{
    properties: {
      page: {
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, // 1440 = 1 inch
        size: { orientation: PageOrientation.LANDSCAPE },
        pageNumbers: { start: 1, formatType: "decimal" } // "upperRoman", "lowerRoman", "upperLetter", "lowerLetter"
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({ 
        alignment: AlignmentType.RIGHT,
        children: [new TextRun("Header Text")]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ 
        alignment: AlignmentType.CENTER,
        children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] }), new TextRun(" of "), new TextRun({ children: [PageNumber.TOTAL_PAGES] })]
      })] })
    },
    children: [/* content */]
  }]
});
```

## 制表位
```javascript
new Paragraph({
  tabStops: [
    { type: TabStopType.LEFT, position: TabStopPosition.MAX / 4 },
    { type: TabStopType.CENTER, position: TabStopPosition.MAX / 2 },
    { type: TabStopType.RIGHT, position: TabStopPosition.MAX * 3 / 4 }
  ],
  children: [new TextRun("Left\tCenter\tRight")]
})
```

## 常量与快速参考
- **下划线：** `SINGLE`、`DOUBLE`、`WAVY`、`DASH`
- **边框：** `SINGLE`、`DOUBLE`、`DASHED`、`DOTTED`
- **编号：** `DECIMAL`（1,2,3）、`UPPER_ROMAN`（I,II,III）、`LOWER_LETTER`（a,b,c）
- **制表位：** `LEFT`、`CENTER`、`RIGHT`、`DECIMAL`
- **符号：** `"2022"`（•）、`"00A9"`（©）、`"00AE"`（®）、`"2122"`（™）、`"00B0"`（°）、`"F070"`（✓）、`"F0FC"`（✗）

## 关键问题与常见错误
- **关键：PageBreak 必须始终放在 Paragraph 内** - 单独的 PageBreak 会产生 Word 无法打开的无效 XML
- **表格单元格底纹始终使用 ShadingType.CLEAR** - 不要使用 ShadingType.SOLID（会造成黑色背景）
- 度量单位为 DXA（1440 = 1 英寸）| 每个表格单元格至少需要 1 个 Paragraph | 目录只应使用 HeadingLevel 样式
- **始终使用自定义样式**，并使用 Arial 字体，以获得专业外观和正确视觉层级
- **始终设置默认字体**：通过 `styles.default.document.run.font` 设置，建议 Arial
- **表格始终使用 columnWidths 数组**，同时设置各单元格宽度以保证兼容性
- **不要用 Unicode 符号充当项目符号** - 始终用带 `LevelFormat.BULLET` 常量的真正编号配置（不是字符串 "bullet"）
- **任何位置都不要用 \n 换行** - 每一行都应使用独立 Paragraph 元素
- **Paragraph children 中始终使用 TextRun 对象** - 不要直接在 Paragraph 上使用 text 属性
- **图片关键点**：ImageRun 必须带 `type` 参数；始终明确指定 "png"、"jpg"、"jpeg"、"gif"、"bmp" 或 "svg"
- **项目符号关键点**：必须使用 `LevelFormat.BULLET` 常量，而不是字符串 "bullet"，并包含 `text: "•"` 作为项目符号字符
- **编号关键点**：每个 numbering reference 都会创建一个独立列表。同一 reference 会延续编号（1,2,3 后接 4,5,6）；不同 reference 会从 1 重新开始（1,2,3 后接 1,2,3）。每个独立编号段都应使用唯一 reference 名称。
- **目录关键点**：使用 TableOfContents 时，标题只能使用 HeadingLevel；不要给标题段落额外添加自定义样式，否则目录会失效
- **表格**：设置 `columnWidths` 数组和各单元格宽度；边框应用到单元格而不是表格
- **在 TABLE 层级设置表格边距**，以保持单元格内边距一致，避免逐单元格重复设置
