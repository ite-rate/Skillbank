

# 编辑 md_to_js 生成的 JS 文件

> 全局字体/字号/缩进/行距/页边距由 `md_to_js.py` 的 CLI 参数设置，不需编辑 JS。
> 本文档仅用于：局部样式覆盖、表格合并、自定义封面页、复杂页眉/页脚、双栏布局。
> 如果这里没有覆盖所需 docx-js 写法，先用关键词检索 `docx-js.md`，只阅读相关片段，不要整篇加载。

md_to_js.py 生成的 JS 文件结构固定，按需修改 children 数组中的内容即可。

## 文件结构

```javascript
const { document_impl, Packer, Paragraph, TextRun, ... } = require('docx');
const doc = new document_impl({
  styles: { ... },           // 样式定义 — 一般不改
  numbering: { ... },        // 列表定义 — 一般不改
  sections: [{
    headers: { ... },        // 页眉
    footers: { ... },        // 页脚
    children: [
      // ← 在这里增删改段落/表格
    ]
  }]
});
```

## 常见修改操作

### 给 TextRun 加颜色
找到对应的 TextRun，加 `color` 属性：
```javascript
// 改前
new TextRun({ text: `注意`, bold: true })
// 改后
new TextRun({ text: `注意`, bold: true, color: "FF0000" })
```

### 给 TextRun 换字体
仅在某个词/句需要不同字体时使用。全文统一字体用 `--font` CLI 参数。
加 `font` 属性：
```javascript
new TextRun({ text: `代码片段`, font: "Consolas" })
```

### 修改段落对齐
仅用于某段对齐不同于其他段落时。全文统一对齐需逐段操作（Markdown 无对齐语法）。
在 Paragraph 对象中加 `alignment`：
```javascript
new Paragraph({
  alignment: AlignmentType.CENTER,  // CENTER / RIGHT / LEFT
  children: [...]
})
```

### 自定义封面页模板

普通封面页优先用 `md_to_js.py --cover --subtitle ... --tagline ...`。只有需要特殊布局时，才**替换** children 数组最前面的第一个 H1 标题段落，用以下模板。封面页不可见分页进入正文（`pageBreakBefore`），不产生分页符标记。

```javascript
// ===== 封面页开始 =====
// 1. 顶开内容（上边距撑开，让标题在页面中上部）
new Paragraph({
  spacing: { before: 3600 },
  alignment: AlignmentType.CENTER,
  children: []
}),
// 2. 主标题 — 深色、大号、加粗
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: `云南之美`, bold: true, size: 72, color: "1A5276" })]
}),
// 3. 副标题 — 浅色、中号
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 100 },
  children: [new TextRun({ text: `彩云之南 · 云南省全景介绍 · 云南`, size: 36, color: "2E86C1" })]
}),
// 4. 标语行 — 斜体、灰色、小号
new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: `自然之美 · 民族之魂 · 历史之韵 · 美食之乡`, italics: true, size: 24, color: "5D6D7E" })]
}),
// 5. 日期 — 浅灰、上留白
new Paragraph({
  spacing: { before: 2400 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: `2026年6月`, size: 22, color: "888888" })]
}),
// ===== 封面页结束 =====
// 6. 第一个章节标题 — 带 pageBreakBefore 自动从新页开始
new Paragraph({
  pageBreakBefore: true,
  heading: HeadingLevel.HEADING_1,
  outlineLevel: 0,
  spacing: { before: 240, after: 240 },
  children: [new TextRun({ text: `一、地理概况`, bold: true, size: 32, color: "000000" })]
}),
```

**字体说明**：封面页不写 `font` 属性，继承 `md_to_js.py --font` 参数的全局字体。如需特定字体（如数字用 Arial），在对应 TextRun 上加 `font: "Arial"`。

**删除旧标题**：生成的 JS 中第一个 H1 段落（`heading: HeadingLevel.HEADING_1`）即是 Markdown 的 `# 标题`。用封面页模板替换它，保留其后的 TOC 或正文不改。

### 修改表格单元格合并
将普通 TableCell 替换为带 merge 的写法（需引入 `VerticalMergeType`）：
```javascript
// 垂直合并 — 起始单元格
new TableCell({
  borders: cellBorders,
  verticalMerge: VerticalMergeType.RESTART,
  children: [new Paragraph({ children: [new TextRun(`合并内容`)] })]
})
// 垂直合并 — 续接单元格
new TableCell({
  borders: cellBorders,
  verticalMerge: VerticalMergeType.CONTINUE,
  children: [new Paragraph({ children: [] })]
})
```

### 修改页眉/页脚内容
找到 header 部分，修改 children：
```javascript
headers: {
  default: new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "文档标题", size: 18, color: "999999" })]
    })]
  })
}
```
页脚同理修改 `footers.default`。普通页脚优先使用 `--footer` 或 `--no-footer`，不要为了改全文页脚手动逐段编辑。

### 多栏布局
在 section 的 `properties` 中加 `column` 属性：
```javascript
properties: {
  page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } },
  column: { count: 2, space: 720 }
}
```
- `count`: 栏数
- `space`: 栏间距 (twips, 720 = 0.5 inch)
- 同一文档内切换单栏/双栏：加多个 section
- 不等宽栏需走 OOXML 编辑

## 注意事项

- JS 中中文正文优先使用反引号模板字符串；如文本包含反引号或 `${...}`，必须先转义
- 修改后执行 `node xxx.js` 生成 docx，确认无报错
- **禁止修改 styles 和 numbering 部分**
- **禁止在 `paragraphStyles` 中添加 `id: "Heading1"/"Heading2"/"Heading3"`** — docx-js 自带内建标题样式，重复定义会导致 Word 报"节和标题"错误
- **表格每个 `TableCell` 必须有 `width: { size: <列宽>, type: WidthType.DXA }`**，否则 Word 报"表格属性"错误
- **分页用 `pageBreakBefore: true`，不要用 `PageBreak()`** — PageBreak 在 Word 中显示为可见分页符标记，`pageBreakBefore` 是段落属性，无可见痕迹
- 表格前需要分页时，插入不可见空段落：`new Paragraph({ pageBreakBefore: true, spacing: { after: 0 }, children: [] })`

### 新建表格的正确写法

在 children 数组中新建表格时，**每个单元格必须带 width**：

```javascript
const colW = 9026 / 列数 | 0;  // A4 可用宽度 9026 DXA
new Table({
  width: { size: colW * 列数, type: WidthType.DXA },
  columnWidths: Array(列数).fill(colW),
  rows: [
    new TableRow({
      children: [
        new TableCell({
          width: { size: colW, type: WidthType.DXA },
          borders: cellBorders,
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ children: [new TextRun("内容")] })]
        }),
        // 每个单元格都带 width
      ]
    })
  ]
})
```
