# .pptx 编辑工作流

> 本文档是 `.pptx` 编辑路线的执行指南。开始编辑前必须完整阅读本文件，并按需读取引用的 reference。
> 从原 `SKILL.md` 迁移而来，仅更新引用路径；编辑逻辑和注意事项原则上保持原样。

## Content Preprocessing（内容预处理 - MANDATORY）

**CRITICAL**: 在开始创建或修改任何PPT之前，必须先完成内容规划。直接动手生成PPT而不做规划，是导致内容混乱、信息丢失、排版灾难的根因。

**MANDATORY - READ ENTIRE FILE**: Read [`references/shared/content-planner.md`](references/shared/content-planner.md) completely before any PPT creation or editing task. This guide covers:
- 需求分析与内容结构化（从自然语言中提取结构化数据）
- 内容提炼与信息分层（提炼要点而非搬运原文）
- 页面规划与大纲设计
- 内容-模板映射（评估内容密度、类型与模板匹配度）
- 文字截断预防
- 质量自查清单

### Quick Reference: Content Preprocessing Checklist

在动手写任何代码之前，必须完成以下步骤：

1. **结构化提取**：将用户需求整理为结构化表格/列表，确保所有条目完整、无遗漏
2. **内容精简**：每页文字控制在80字以内，每条要点不超过25字
3. **受众适配**：根据受众类型（技术专家/小白/管理层）调整内容深度
4. **页面大纲**：先写出完整的页面大纲，包含每页标题和要点
5. **模板映射**：评估每页内容密度，选择匹配的模板布局
6. **截断预防**：计算目标shape可容纳的字符数，超长内容先精简再填充

### 强制规则
1. 关于解决方案的说明，**只允许输出 1 次**，输出后永久禁止重复打印。
2. 一旦确认解决方案，立即进入代码编写环节，不再重复描述原因。
3. 禁止循环输出相同的解决方案描述。

### 从外部内容源创建PPT时的特殊要求

当用户要求"基于PDF/文档内容创建PPT"时，**绝对禁止逐字搬运原文**：

- **提炼而非复制**：每页提取1-2个核心论点，精简为≤25字的要点
- **信息分层**：原文 → 核心论点 → 幻灯片文字 → 可视化图表
- **术语处理**：对小白受众，每个专业术语必须附带简短解释或类比
- **视觉优先**：能用图表/图示表达的，不用文字；能用关键词的，不用完整句子

## Reading and analyzing content

### Text extraction
If you just need to read the text contents of a presentation, you should convert the document to markdown:

```bash
# Convert document to markdown
python -m markitdown path-to-file.pptx
```

### Raw XML access
You need raw XML access for: comments, speaker notes, slide layouts, animations, design elements, and complex formatting. For any of these features, you'll need to unpack a presentation and read its raw XML contents.

#### Unpacking a file
`python ooxml/scripts/unpack.py <office_file> <output_dir>`

**Note**: The unpack.py script is located at `skills/pptx/ooxml/scripts/unpack.py` relative to the project root. If the script doesn't exist at this path, use `find . -name "unpack.py"` to locate it.

#### Key file structures
* `ppt/presentation.xml` - Main presentation metadata and slide references
* `ppt/slides/slide{N}.xml` - Individual slide contents (slide1.xml, slide2.xml, etc.)
* `ppt/notesSlides/notesSlide{N}.xml` - Speaker notes for each slide
* `ppt/comments/modernComment_*.xml` - Comments for specific slides
* `ppt/slideLayouts/` - Layout templates for slides
* `ppt/slideMasters/` - Master slide templates
* `ppt/theme/` - Theme and styling information
* `ppt/media/` - Images and other media files

#### Typography and color extraction
**When given an example design to emulate**: Always analyze the presentation's typography and colors first using the methods below:
1. **Read theme file**: Check `ppt/theme/theme1.xml` for colors (`<a:clrScheme>`) and fonts (`<a:fontScheme>`)
2. **Sample slide content**: Examine `ppt/slides/slide1.xml` for actual font usage (`<a:rPr>`) and colors
3. **Search for patterns**: Use grep to find color (`<a:solidFill>`, `<a:srgbClr>`) and font references across all XML files

## Editing an existing PowerPoint presentation

### CRITICAL: Choose the right editing approach (Dual-Track Routing)

Before editing an existing PPT, you MUST choose the appropriate track based on task complexity.

#### Track A: Lightweight Template Editing (Fast Path)
- **Use Cases**: Basic text replacement, title updates, or lightweight content editing using an existing template (no complex layout restructuring).
- **Action**: You MUST read and follow the [Editing Presentations](references/pptx/template-editing.md) guide. Use this as the primary method for medium/light editing tasks.

#### Track B: High-Fidelity/Structural Editing (High-Fidelity Structural Path)
- **Use Cases**: Table modifications (e.g., Gantt charts), complex shape alignment, XML-level refinement, or strict brand asset preservation (backgrounds, logos).
- **Action**: Use the OOXML workflow (`unpack.py` -> edit XML -> `pack.py`). You MUST strictly follow the "Pre-Edit Content Structuring (MANDATORY)" and "Table & Dense Content Editing" sections below to prevent layout corruption.

### 编辑前内容结构化预处理（MANDATORY）

**CRITICAL**: 在编辑任何现有PPT之前，**必须先完成内容结构化预处理**。直接拿到需求就写代码修改PPT，是导致内容遗漏、文字截断、布局混乱的根因。

#### 步骤1：结构化提取用户需求

将用户以自然语言描述的需求，提取为结构化表格：

```markdown
| 序号 | 任务名称 | 执行人 | 开始日期 | 结束日期 | 阶段 |
|------|---------|--------|----------|----------|------|
| 1    | 完成集团党建工作满意度测评 | 各支部 | 1月5日 | 1月9日 | 筹备期 |
| 2    | 完成党费基数核算及党费补缴方案 | — | 1月7日 | 1月9日 | 筹备期 |
| ...  | ... | ... | ... | ... | ... |
```

#### 步骤2：分析PPT结构并做内容映射规划

在动手修改之前，必须先完成以下规划：

1. **确定新内容与原PPT结构的映射关系**：
   - 原PPT有几行几列？分别对应什么含义（日期？任务？阶段？）
   - 新内容的每一项应该放在哪一行、哪一列？
   - 是否有跨行/跨列的情况？如何处理？

2. **测量目标单元格/形状的可用空间**：
   - 使用 `inventory.py` 获取每个shape的尺寸（left, top, width, height，单位英寸）
   - 计算可容纳字符数：`(宽度英寸 × 96 / 字号pt) × 行数`（96为每英寸CSS像素数）
   - **如果新内容超出可容纳字符数，必须先精简内容**

3. **文字精简策略**（按优先级）：
   - 去除冗余词汇，保留关键动作+对象（如"制作确定2026年党费预算上会版" → "制作2026年党费预算"）
   - 缩小字号（下限不低于7pt，低于7pt在投影时不可读）
   - 拆分到多个单元格/形状
   - **绝对禁止：用代码截断文字（如 `name[:13] + "…"`）**

#### 步骤3：输出修改方案并获得确认

对于复杂编辑任务，先输出修改方案（文字版），说明：
- 每个位置对应的新内容是什么
- 文字是否需要精简、如何精简
- 哪些位置可能放不下完整内容

然后再开始写代码。

### 表格/密集内容编辑指南（Table & Dense Content Editing）

当编辑包含表格、甘特图、时间线等密集信息的PPT时，**必须在修改前先分析表格结构**：

#### 修改前必做步骤

1. **Unpack并分析表格结构**：
    ```bash
    python ooxml/scripts/unpack.py template.pptx unpacked
    ```
    - 定位表格所在的 slide XML 文件（`ppt/slides/slide1.xml`）
    - 分析 `<a:tbl>` 结构：行数、列数、合并单元格、列宽
    - 分析每个单元格 `<a:tc>` 的内容结构

2. **完整记录表格结构**：
    在修改前，先用表格形式记录原始结构：
    ```markdown
    ## 表格结构分析
    - 行数：X行（含表头）
    - 列数：Y列
    - 列宽（EMU）：[col1, col2, ...]
    - 合并单元格：[描述哪些单元格被合并]
    - 每个单元格的原始内容：[记录]
    ```

3. **测量单元格可用空间**：
    - 从列宽（EMU）计算英寸：`宽度英寸 = EMU值 / 914400`
    - 估算可容纳字符数：`(宽度英寸 × 72 / 字号) × 行数`
    - **如果新内容超出可容纳字符数，必须先精简内容**

#### 表格文字修改规则

**CRITICAL RULES**:

1. **完整性优先**：宁可缩小字号，也不截断文字
   - ❌ "完成党支部履职文"（被截断）
   - ✅ "完成党支部履职文化铭牌设计制作"（完整）或精简为"履职文化铭牌制作"

2. **先精简，再填充**：
   - 如果单元格宽度有限，先提炼任务/条目名称的核心信息
   - 去除冗余词汇，保留关键动作+对象
   - 例如："制作确定2026年党费预算上会版" → "制作2026年党费预算（上会版）"

3. **保持结构一致**：
   - 不要改变表格的行列数（除非用户明确要求）
   - 不要改变合并单元格的结构
   - 不要改变列宽比例（除非需要适应新内容）

4. **验证文字完整性**：
   - 修改后检查每个单元格的文字是否完整
   - 特别注意长任务名称是否被截断
   - 使用 inventory.py 检测文字溢出

5. **保留原始样式**：
   - 复制原始 `<a:rPr>` 的格式属性（字号、字体、颜色、加粗等）
   - 不要引入新的字体或颜色
   - 不要改变对齐方式

#### 时间线/甘特图特殊注意事项（CRITICAL - 常见问题高发区）

编辑甘特图等时间线型PPT时，历史执行中频繁出现表格结构混乱、条形未对齐、文字溢出等问题。**必须严格遵循以下流程**：

##### Step 1: 完整分析原始表格结构（MANDATORY - 不要跳过）

在动手修改任何内容之前，必须完整记录原始表格的**每一个细节**：

```markdown
## 甘特图结构分析（MANDATORY）

### 表格基本信息
- 表格所在：Group Shape内（名称：xxx）
- 行数：X行（含表头行、日期行、任务行）
- 列数：Y列
- 每列含义：[描述每列代表什么——日/周/月？]
- 列宽（EMU）：[col1, col2, ...]

### 原始时间轴映射
- 原始日期范围：[起始日] ~ [结束日]
- 每列对应的日期/时间单位：[第1列=xxx, 第2列=xxx, ...]
- 行结构：[哪行是表头、哪行是日期、哪些行是任务]

### 浮动条形（甘特条）信息
- 条形数量：X个
- 每个条形的位置（x, y, width, height）和对应行
- 每个条形的内容和颜色

### 品牌元素
- 标题、编号、底部品牌信息的位置和样式
- 阶段标签的位置、颜色和内容
```

##### Step 2: 新内容的时间轴映射规划

**CRITICAL**: 在决定如何修改表格之前，必须先完成新内容到原表格结构的映射：

```markdown
## 时间轴映射规划

### 新内容时间范围
- 最早日期：X月X日
- 最晚日期：X月X日
- 总跨度：约X周

### 列映射方案
原表格有Y列（代表7天/周等），新内容需要适配到同样的列结构：
- 方案A（推荐）：保持原有列结构不变（如按天7列），只修改日期行和任务行
- 方案B：如果新内容的时间跨度与原模板差异大，考虑改变列的时间粒度

### 任务-行映射
| 新任务 | 应放置的行 | 对应的列范围 | 精简后的文字（≤目标字符数） |
|--------|-----------|-------------|--------------------------|
| 任务1  | Row[X]    | Col[Y]-Col[Z] | 精简文字 |
| ...    | ...       | ...          | ... |

### 条形-任务映射
| 条形 | 对应任务 | 新位置(y) | 新宽度(width) | 新文字 |
|------|---------|-----------|--------------|--------|
| Bar1 | 任务1+2  | 需重新计算 | 需重新计算 | 精简文字 |
| ...  | ...     | ...       | ...          | ... |
```

**时间轴映射注意事项**：
- **保持列的时间粒度与原模板一致**——如果原模板按天分列（7列=周日~周六），新内容也应按天分列
- **不要随意改变列的语义**——将"按天"改为"按周"会导致表格结构混乱
- **如果新内容时间跨度超出原表格行数**，考虑精简任务或合并相近日期的任务

##### Step 3: 文字精简与截断预防

在修改甘特图时，文字精简是避免溢出的关键：

1. **测量目标shape的可用空间**：
   - 使用 inventory.py 获取每个条形/单元格的尺寸
   - 估算可容纳字符数：`(宽度英寸 × 96 / 字号pt) × 行数`
   - **特别注意甘特条形**：它们的宽度通常较窄，可用字符数有限

2. **甘特条形文字精简规则**：
   - 优先级1：去除"完成"、"制作"等冗余动词
   - 优先级2：去除年份前缀（如"2026年"可省略，标题已标明年份）
   - 优先级3：使用简称（如"党建工作"→"党建"，"满意度测评"→"满意度测评"保持）
   - **示例**："完成集团党建工作满意度测评" → "党建工作满意度测评" 或 "满意度测评"
   - **绝对禁止**：超出条形宽度的文字不精简直接填入

##### Step 4: 条形重新定位

**CRITICAL**: 如果修改了表格行的内容，必须同步调整浮动条形的位置：

- 条形的 `y` 坐标必须与对应任务行的 `y` 坐标匹配
- 条形的 `width` 必须与任务对应的时间跨度匹配（列数 × 单列宽度）
- 条形的 `height` 应与对应行的高度一致或略小
- 多个条形之间不能重叠
- **使用OOXML workflow精确调整坐标**，不要用python-pptx（坐标精度不足）
##### Step 5: 视觉验证

修改完成后，必须验证：
- [ ] 所有文字完整无截断（特别是甘特条形中的文字）
- [ ] 条形位置与表格行精确对齐
- [ ] 任务名称出现在PPT中某处（不依赖shape与表格的"隐式对应"）
- [ ] 阶段标签正确对应实际日期范围
- [ ] 底部品牌信息已更新
- [ ] 原模板的编号等无关信息已删除或更新
- [ ] 使用 `inventory.py` 检测所有shape的文字溢出情况

### python-pptx 编辑注意事项

当选择使用 python-pptx 库直接编辑PPT时，需要注意以下限制和最佳实践：

#### 已知限制

1. **Group Shape 坐标变换**：
   - 当表格或shape嵌套在 `<p:grpSp>`（Group Shape）内时，python-pptx 的 `shape.left/top/width/height` 返回的是**组内局部坐标**，不是幻灯片绝对坐标
   - 如果需要计算shape在幻灯片上的实际位置，必须手动叠加group的变换矩阵（`<a:xfrm>` 中的 `chOff` 和 `chExt`）
   - **建议**：需要精确坐标对齐时（如甘特条形与表格行对齐），优先使用 OOXML workflow 直接编辑XML

2. **表格操作限制**：
   - python-pptx **不能**：改变表格行列数、合并/拆分单元格、精确控制单元格边框样式
   - python-pptx **可以**：修改单元格文字和填充色、调整列宽
   - 如果需要改变表格结构（行列数），必须用 OOXML workflow

3. **文本shape定位**：
   - python-pptx 无法创建精确对齐到表格单元格的浮动shape
   - 如果原模板有"浮动shape覆盖在表格上"的设计（如甘特条形），用 python-pptx 修改文字后，shape的位置/大小不会自动适应新内容

#### 最佳实践

- **适合用 python-pptx 的场景**：纯文字替换、修改标题/正文内容、简单格式调整
- **不适合用 python-pptx 的场景**：表格结构变更、精确坐标对齐、group内shape操作、甘特图等需要视觉精度的编辑
- **混合使用**：文字类修改用 python-pptx（快速），表格/图形修改用 OOXML（精确），但需注意两种方法可能产生的ID冲突

### Workflow
1. **MANDATORY - READ ENTIRE FILE**: Read [`references/pptx/ooxml-guide.md`](references/pptx/ooxml-guide.md) (~500 lines) completely from start to finish.  **NEVER set any range limits when reading this file.**  Read the full file content for detailed guidance on OOXML structure and editing workflows before any presentation editing.
2. Unpack the presentation: `python ooxml/scripts/unpack.py <office_file> <output_dir>`
3. Edit the XML files (primarily `ppt/slides/slide{N}.xml` and related files)
4. **CRITICAL**: Validate immediately after each edit and fix any validation errors before proceeding: `python ooxml/scripts/validate.py <dir> --original <file>`
5. Pack the final presentation: `python ooxml/scripts/pack.py <input_directory> <office_file>`
