---
name: docx-tele
description: 'Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When TeleAgent needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks'
level: manual
native_agent: TeleAgent
description_zh: 支持创建、读取、编辑和整理 Word 文档，可用于报告、备忘录、信函、模板等正式文件的生成与排版，也能处理目录、标题、页码、表格、图片、批注和修订记录，适合把零散内容整理成规范、可交付的 .docx 文档。
name_zh: Word文档助手
license: Proprietary. LICENSE.txt has complete terms
---

# 技能：docx

# DOCX 文档创建、编辑与分析

## 概述

用户可能要求你创建、编辑或分析 .docx 文件的内容。.docx 文件本质上是一个包含 XML 文件和其他资源的 ZIP 压缩包，你可以读取或编辑这些内容。针对不同任务，你可以使用不同的工具和工作流。

## 模板合规策略

当用户提供 `.docx` 模板时，必须严格保留模板的格式约定——文档样式、字体、页面布局（边距 / 页面大小 / 方向）、页眉页脚、分节结构和表格样式。不要引入模板中不存在的结构或版式。

如果用户需求与模板约束冲突，先说明具体冲突并获得明确同意，再做结构性变更。不要静默偏离模板。

**示例**："您的需求需要新增一种双栏布局，但模板中没有该版式。是否允许在模板基础上新增该版式？"

## 强制策略：依赖缺失

- 如果某个必需依赖缺失或不可用，且你**尚未**在当前平台尝试安装，你**必须**先按照**系统依赖**的说明进行安装。
- 如果安装失败或工具仍不可用，你**必须**运行上述步骤中指定的降级模式命令。
- 你**不得**自行替换工具、使用替代流程或自创降级方案，除非上述两个步骤均已尝试且确实无法满足任务需求。

## 强制策略：Windows UTF-8

在 Windows PowerShell 上，所有 `python` 命令前必须加上 `$env:PYTHONUTF8="1"; `，以强制 Python 使用 UTF-8 模式。这可以避免中文/CJK 文件路径和内容的编码错误。

## 工作流决策树

### 读取/分析内容
使用下方"文本提取"或"原始 XML 访问"章节

### 创建新文档
使用"创建新 Word 文档"工作流（Markdown → JS → docx）

### 编辑已有文档
- **自己创建的文档 + 简单修改**
  使用"基本 OOXML 编辑"工作流

- **他人创建的文档**
  使用**"批注审阅工作流"**（推荐默认）

- **法律、学术、商务或政府文档**
  **必须**使用"批注审阅工作流"

## 读取和分析内容

### 文本提取
如果你只需要读取文档的文本内容，可以使用 pandoc 将文档转换为 Markdown。Pandoc 能很好地保留文档结构，并支持显示修订痕迹：

```bash
# 将文档转换为 Markdown，保留修订痕迹
pandoc --track-changes=all path-to-file.docx -o output.md
# 选项：--track-changes=accept/reject/all
```

> 如果该命令不可用，且在按照下方**系统依赖**说明尝试后在当前平台仍无法安装 `pandoc`，则运行：
>
> - `python scripts/fallback_text_extract.py <path-to-file.docx> -o <output.md>`
>
> **限制**：降级提取无法复现 pandoc 的完整修订痕迹差异视图；删除的文本会被隐藏，插入的文本按已接受处理。

### 原始 XML 访问
以下场景需要原始 XML 访问：批注、复杂格式、文档结构、嵌入媒体和元数据。对于这些功能，你需要解包文档并读取其原始 XML 内容。

#### 解包文件
`python ooxml/scripts/unpack_workflow.py <office_file> <output_directory>`

#### 关键文件结构
* `word/document.xml` - 文档主要内容
* `word/comments.xml` - document.xml 中引用的批注
* `word/media/` - 嵌入的图片和媒体文件
* 修订痕迹使用 `<w:ins>`（插入）和 `<w:del>`（删除）标签

## 创建新 Word 文档

从头创建新 Word 文档时，始终使用 **Markdown → JS → docx** 工作流。这种方式最小化 AI 输出，同时通过自动 JS 生成支持所有常见格式。

### 关键：中文引号

Markdown 文本中可以使用中文弯引号（如 `“”`、`‘’`）。转换脚本会保留这些字符，并只转义 JS 模板字符串真正敏感的字符（反斜杠、反引号、`${...}`）。

只有在手动编辑生成的 JS 文件时，才需要特别注意字符串写法：中文正文优先放在反引号模板字符串中，并确保反引号和 `${...}` 已正确转义。

### Markdown 语法支持
 如果需要目录请在标题下写入`[TOC]`（独占一行；自动：TOC前后分页、需运行 `render_toc_static.py` 渲染） 


| 语法 | 转换为 |
|------|--------|
| `# H1` ~ `#### H4` | 标题 1-4 |
| `**加粗**` | 加粗 TextRun |
| `*斜体*` | 斜体 TextRun |
| `***加粗斜体***` | 加粗+斜体 TextRun |
| `` `代码` `` | Consolas 字体 TextRun |
| `[文字](链接)` | ExternalHyperlink |
| `[*文字*](链接)` | 斜体 ExternalHyperlink（推荐） |
| `[**文字**](链接)` | 加粗 ExternalHyperlink（推荐） |
| `[***文字***](链接)` | 加粗+斜体 ExternalHyperlink（推荐） |
| `*[文字](链接)*` | 斜体 ExternalHyperlink（兼容） |
| `**[文字](链接)**` | 加粗 ExternalHyperlink（兼容） |
| `***[文字](链接)***` | 加粗+斜体 ExternalHyperlink（兼容） |
| `- 条目` / `* 条目` | 无序列表 |
| `1. 条目` | 有序列表 |
| `\| 表格 \|` | 表格 |
| `![替代文本](路径)` | ImageRun |
| ` ``` ` 围栏代码块 | 每行一个 Paragraph，Consolas 字体（比正文小 2pt），紧凑行距，无反引号 |


> **数学公式**：Markdown 围栏代码块 ` ``` ` 中的公式会渲染为 Consolas 等宽字体、紧凑行距的纯文本段落（无反引号）。这是**可读纯文本**公式，非真正数学排版。需要下标、上标、分数、根号等数学排版时，必须走 OOXML 后编辑注入 OMML。参见下方[第3层表格](#第3层ooxml-后编辑大部分情况不用只有格式复杂到无法用js处理才采用)中的"数学公式"行。

### 格式层级

使用能达到效果的最轻量层级。不要用更低层级去处理更高层级已经能完成的事。

| 层级 | 方式 | 用途 |
|------|------|------|
| **1. Markdown + CLI** | 写 `.md`，带参数运行 `md_to_js.py` | 内容结构（标题、列表、表格、图片、链接、目录、可选封面）+ 全局格式（字体、字号、缩进、行距、页边距、页眉页脚） |
| **2. JS 编辑** | 编辑生成的 `.js`，运行 `node` | 单元素覆盖（单个 TextRun 颜色/字体、单个段落对齐）、分页、表格合并、自定义封面页、复杂页眉/页脚内容、多栏布局 |
| **3. OOXML 后编辑** | 解包 → 编辑 XML → 打包 | 不等宽栏、栏分隔线、嵌套表格、文本框、复杂页眉、修订痕迹 |

**第1层可处理约 90% 的文档。** 仅当某个元素需要不同于全局默认值的格式时才降至第2层。第3层用于 docx-js 无法表达的结构性变更。

### 工作流

1. **编写 Markdown**：将文档内容写为 Markdown，保存为 `.md` 文件到 `.temp/` 目录。
2. **转换为 JS**：使用下方列出的 CLI 参数运行 `md_to_js.py`。**不要读取脚本源码**——下方的参数表包含了使用该脚本所需的全部信息。只有在调试或修复脚本 bug 时才需要读取 `md_to_js.py` 源码。
   ```powershell
   $env:PYTHONUTF8="1"; python scripts/md_to_js.py --input <content.md> --output <output.js> --docx-output <output.docx> --font "仿宋_GB2312" --font-size 24 --indent 480 --line-spacing 360
   ```

   | 参数 | 默认值 | 说明 |
   |------|--------|------|
   | `--font` | 仿宋_GB2312 | 文档默认字体 |
   | `--font-size` | 24 | 正文字号，单位半磅（24=12pt） |
   | `--font-size-h1` | auto | H1 字号（默认：font-size × 1.33） |
   | `--font-size-h2` | auto | H2 字号（默认：font-size × 1.17） |
   | `--font-size-h3` | auto | H3 字号（默认：font-size × 1.08） |
   | `--indent` | 0 | 首行缩进，单位缇（480 ≈ 12pt 下2个中文字符） |
   | `--line-spacing` | 0 | 行距（240=单倍, 360=1.5倍, 480=双倍, 0=使用默认） |
   | `--margin-top` | 1440 | 上边距，单位缇（1440=1英寸） |
   | `--margin-right` | 1440 | 右边距 |
   | `--margin-bottom` | 1440 | 下边距 |
   | `--margin-left` | 1440 | 左边距 |
   | `--heading-color` | 1A5276 | 标题颜色，十六进制RRGGBB，所有H1/H2/H3统一使用 |
   | `--cover` | false | 将第一个 H1 生成为封面页；不传时第一个 H1 是普通标题 |
   | `--subtitle` | （空） | 封面副标题，大号浅色居中；仅在 `--cover` 时使用 |
   | `--tagline` | （空） | 封面标语，小号斜体灰色居中；仅在 `--cover` 时使用 |
   | `--header` | 文档标题 | 页眉文字，默认使用文档第一个 H1 标题 |
   | `--no-header` | false | 不生成页眉 |
   | `--footer` | 页码 | 页脚文字；不传时默认生成居中页码 |
   | `--no-footer` | false | 不生成页脚 |

   - 中文文档：默认传入 `--indent 480 --line-spacing 360`
   - **封面页**：需要封面时传入 `--cover --subtitle "XX省全景介绍" --tagline "关键词 · 关键词 · 关键词"`
   - 封面日期自动取当前年月，无需传入
   - 英文文档：将 `--font` 设为 `Calibri` 或 `Arial`，根据样式指南调整 `--indent` 和 `--line-spacing`

3. **按需编辑 JS**：仅用于覆盖第1层全局设置的单元素格式。典型场景：
   - **单个 TextRun**：颜色变更、特定词/句的字体覆盖
   - **单个段落**：对齐方式变更
   - **布局**：表格合并、自定义封面页、复杂页眉/页脚内容、多栏布局（在节属性中添加 `column: { count: 2, space: 720 }`）、章节间分页

   不要在 JS 中编辑全局设置——那些由步骤2的 `--font`、`--font-size`、`--indent`、`--line-spacing`、`--margin-*` 控制。

   **必须 — 编辑 JS 前读取完整文件**：当需要编辑生成的 JS 文件时，必须从头到尾完整阅读 [`md-to-js-edit-guide.md`](md-to-js-edit-guide.md)。**不要设置任何行数限制。** 阅读完整内容以获取 JS 编辑代码模式和操作规范。
4. **高级 docx-js 工具书（仅按需）**：不要默认读取 [`docx-js.md`](docx-js.md)。只有在 `md-to-js-edit-guide.md` 无法覆盖、你确实搞不清楚某个 docx-js 写法、或生成/编辑 JS 报错且无法定位原因时，才使用它。优先用 `rg`/关键词检索（如 `ImageRun`、`section`、`TableOfContents`、`Header`、`PageOrientation`、`VerticalMergeType`）定位相关段落，再阅读必要片段；不要整篇加载。
5. **生成 docx**：确保步骤3的所有 JS 编辑已完成后再运行。执行 JS 文件：
   ```powershell
   node <output.js>
   ```
6. 如果 Markdown 中使用了 `[TOC]`，脚本会自动在 TOC 前后插入分页符。然后运行以下命令渲染目录：
   ```powershell
   $env:PYTHONUTF8="1"; python scripts/render_toc_static.py <output.docx>
   ```

### 第3层：OOXML 后编辑（大部分情况不用，只有格式复杂到无法用js处理才采用）

某些格式无法用 docx-js 表达，需要直接操作 XML。创建 .docx 后使用"编辑已有 Word文档"工作流。

| 场景 | 备注 |
|------|------|
| 不等宽栏 / 栏分隔线 | 等宽基本栏属第2层（编辑 JS 节属性 `column`） |
| 嵌套表格 | Word 规范限制——即使 OOXML 也非真正支持 |
| 文本框 / 形状内容 | docx-js 无文本框 API |
| 复杂页眉（图片、多段落） | 简单文本页眉属第2层 |
| 修订痕迹 | 使用[批注审阅工作流](#批注审阅工作流) |
| 动态页眉/页脚文本 | 如从文档属性读取标题显示在页眉中 |
| **数学公式** | 需要真正的数学排版时，按需阅读 [ooml-math-guide.md](ooml-math-guide.md)。包含 OMML 元素速查、LaTeX 映射表、Python 注入模板 |


## 编辑已有 Word 文档

**不要使用 python-docx 进行编辑。** 它可能无法正确处理其他工具创建的文档的样式 ID 或格式，导致 KeyError 或样式损坏。始终使用下方的 OOXML（document_impl 库）工作流。

编辑已有 Word 文档时，使用 **document_impl 库**（一个用于 OOXML 操作的 Python 库）。该库自动处理基础设施配置，提供文档操作方法。对于复杂场景，你可以直接通过库访问底层 DOM。

### 工作流
1. **必须 — 读取完整文件**：从头到尾完整阅读 [`ooxml.md`](ooxml.md)（约600行）。**不要设置任何行数限制。** 阅读完整内容以获取 document_impl 库 API 和直接编辑文档文件的 XML 模式。
2. 解包文档：`python ooxml/scripts/unpack_workflow.py <office_file> <output_directory>`
3. 使用 document_impl 库创建并运行 Python 脚本（参见 ooxml.md 中"document_impl Library"章节）
4. 打包最终文档：`python ooxml/scripts/pack_workflow.py <input_directory> <office_file>`

> 如果打包步骤因 `soffice`/LibreOffice 不可用而失败，且在当前平台无法安装 LibreOffice，则重新运行：
>
> - `python ooxml/scripts/pack_workflow.py <input_directory> <office_file> --force`
>
> **限制**：`--force` 跳过验证；如果编辑存在 XML 问题，打包后的文件可能损坏。

document_impl 库同时提供常用操作的高级方法和复杂场景的直接 DOM 访问。

## 批注审阅工作流

此工作流允许你在实现 OOXML 修订痕迹之前，先用 Markdown 规划全面的修改。**关键**：要实现完整的修订痕迹，你必须系统地实施所有修改。

**分批策略**：将相关修改分组为 3-10 条的批次。这使调试可控同时保持效率。每个批次完成后测试再继续下一批。

**原则：最小化、精确编辑**
实现修订痕迹时，仅标记实际发生变化的文本。重复未改变的文本会使修改难以审阅且显得不专业。将替换拆分为：[未改变的文本] + [删除] + [插入] + [未改变的文本]。保留原始 run 的 RSID，复用原始 `<w:r>` 元素。

示例 - 将句子中的"30天"改为"60天"：
```python
# 错误 - 替换整句
'<w:del><w:r><w:delText>The term is 30 days.</w:delText></w:r></w:del><w:ins><w:r><w:t>The term is 60 days.</w:t></w:r></w:ins>'

# 正确 - 仅标记变化的部分，保留未改变文本的原始 <w:r>
'<w:r w:rsidR="00AB12CD"><w:t>The term is </w:t></w:r><w:del><w:r><w:delText>30</w:delText></w:r></w:del><w:ins><w:r><w:t>60</w:t></w:r></w:ins><w:r w:rsidR="00AB12CD"><w:t> days.</w:t></w:r>'
```

### 修订痕迹工作流

1. **获取 Markdown 表示**：将文档转换为保留修订痕迹的 Markdown：
   ```bash
   pandoc --track-changes=all path-to-file.docx -o current.md
   ```
   如果该命令不可用，且在按照下方**系统依赖**说明尝试后在当前平台仍无法安装 `pandoc`，则运行：
   - `python scripts/fallback_text_extract.py path-to-file.docx -o current.md`

2. **识别并分组修改**：审阅文档并识别所有需要的修改，按逻辑批次组织：

   **定位方法**（用于在 XML 中查找修改位置）：
   - 章节/标题编号（如"第3.2节"、"第四条"）
   - 段落编号（如有）
   - 含唯一上下文文本的 Grep 模式
   - 文档结构（如"第一段"、"签章区"）
   - **不要使用 Markdown 行号**——它们与 XML 结构不对应

   **批次组织**（每批 3-10 条相关修改）：
   - 按章节：批次1: 第2节修改，批次2: 第5节修改
   - 按类型：批次1: 日期更正，批次2: 当事人名称变更
   - 按复杂度：先简单文本替换，再处理复杂结构性变更
   - 按顺序：批次1: 第1-3页，批次2: 第4-6页

3. **阅读文档并解包**：
   - **必须 — 读取完整文件**：从头到尾完整阅读 [`ooxml.md`](ooxml.md)（约600行）。**不要设置任何行数限制。** 特别关注"document_impl Library"和"Tracked Change Patterns"章节。
   - **解包文档**：`python ooxml/scripts/unpack_workflow.py <file.docx> <dir>`
   - **记录建议的 RSID**：解包脚本会建议一个用于修订痕迹的 RSID。复制此 RSID 供步骤4b 使用。

4. **分批实施修改**：将修改按逻辑分组（按章节、类型或位置），在同一脚本中一起实现。这种方式：
   - 使调试更简单（批次更小 = 更容易定位错误）
   - 允许渐进式推进
   - 保持效率（3-10 条修改的批次效果良好）

   **建议的批次分组：**
   - 按文档章节（如"第3节修改"、"定义"、"终止条款"）
   - 按修改类型（如"日期修改"、"当事人名称更新"、"法律术语修改"）
   - 按位置（如"第1-3页的修改"、"文档前半部分的修改"）

   对于每批相关修改：

   **a. 文本映射到 XML**：在 `word/document.xml` 中 grep 文本，验证文本如何跨 `<w:r>` 元素拆分。

   **b. 创建并运行脚本**：使用 `get_node_impl` 查找节点，实施修改，然后 `doc.save_impl()`。参见 ooxml.md 中"document_impl Library"章节的模式。

   **注意**：编写脚本前务必重新 grep `word/document.xml` 以获取当前行号和验证文本内容。行号在每次脚本运行后会变化。

5. **打包文档**：所有批次完成后，将解包目录转回 .docx：
   ```bash
   python ooxml/scripts/pack_workflow.py unpacked reviewed-document.docx
   ```

   如果打包步骤因 `soffice`/LibreOffice 不可用而失败，且在当前平台无法安装 LibreOffice，则重新运行：
   - `python ooxml/scripts/pack_workflow.py unpacked reviewed-document.docx --force`

6. **最终验证**：对完整文档进行全面检查：
   - 将最终文档转换为 Markdown：
     ```bash
     pandoc --track-changes=all reviewed-document.docx -o verification.md
     ```
     如果该命令不可用，且在按照下方**系统依赖**说明尝试后在当前平台仍无法安装 `pandoc`，则运行：
     - `python scripts/fallback_text_extract.py reviewed-document.docx -o verification.md`
   - 验证所有修改已正确应用：
     ```bash
     grep "原始短语" verification.md  # 不应找到
     grep "替换短语" verification.md  # 应能找到
     ```
   - 检查是否引入了意外修改


## 文档转图片

要对 Word 文档进行可视化分析，可通过两步流程将其转换为图片：

1. **将 DOCX 转换为 PDF**：
   ```bash
   soffice --headless --convert-to pdf document.docx
   ```

2. **将 PDF 页面转换为 JPEG 图片**：
   ```bash
   pdftoppm -jpeg -r 150 document.pdf page
   ```
   这将生成 `page-1.jpg`、`page-2.jpg` 等文件。

选项：
- `-r 150`：设置分辨率为 150 DPI（可调整以平衡质量和大小）
- `-jpeg`：输出 JPEG 格式（如需 PNG 可用 `-png`）
- `-f N`：起始页码（如 `-f 2` 从第2页开始）
- `-l N`：结束页码（如 `-l 5` 到第5页停止）
- `page`：输出文件名前缀

指定范围的示例：
```bash
pdftoppm -jpeg -r 150 -f 2 -l 5 document.pdf page  # 仅转换第2-5页
```

> 如果这些命令不可用，且在按照下方**系统依赖**说明尝试后在当前平台仍无法安装 `LibreOffice` 和/或 `Poppler`，则运行：
>
> - `python scripts/fallback_docx_to_image.py <document.docx> --outdir <outdir> [--dpi 150] [--format jpeg|png]`
>
> **限制**：降级转换可能通过回退渲染生成页面；如果平台不支持（如 Linux），可能回退为 HTML 导出而非图片。

## 代码风格指南
**重要**：编写 DOCX 操作代码时：
- 编写简洁的代码
- 避免冗长的变量名和多余操作
- 避免不必要的 print 语句

## 依赖

### Python 包（所有平台）

- `defusedxml`
- `python-docx`
- `pymupdf`
- `docx2pdf`
- `mammoth`

### npm 包

- `docx`（Markdown → JS 工作流和直接 JS 创建所需）

### 系统依赖

| 依赖 | 用途 | Linux | macOS |
|------|------|-------|-------|
| **pandoc** | 文本提取 | `sudo apt-get install pandoc` | `brew install pandoc` |
| **LibreOffice** | PDF 转换、文档验证 | `sudo apt-get install libreoffice` | `brew install --cask libreoffice` |
| **Poppler** | PDF 转图片（`pdftoppm`） | `sudo apt-get install poppler-utils` | `brew install poppler` |
| **git** | 批注审阅文本差异 | 通常已预装 | `xcode-select --install` |

使用批注审阅辅助工具时，如果 `git` 不可用，会自动回退到基于 `difflib` 的差异比较。

**Windows**：系统依赖难以通过命令行安装。
- `pandoc`：尝试 `winget install JohnMacFarlane.Pandoc`
- `LibreOffice`：尝试 `winget install TheDocumentFoundation.LibreOffice`
