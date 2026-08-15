# SVG 路线创建工作流

> **阅读顺序**：先完整阅读本文件，再按步骤执行。步骤④开始前还需读取 `references/pptx-svg/shared-standards.md`。

---

## 执行规则（最高优先级）

1. **串行执行**：七个步骤必须按顺序执行，上一步的输出是下一步的输入
2. **SVG 必须手写**：每页 SVG 由 agent 逐页亲自编写，严禁用脚本批量生成
3. **每页生成前重读 spec_lock**：步骤④每生成一页前必须重读 `spec_lock.md`（防止上下文压缩漂移）
4. **不向用户暴露引擎概念**：全程不提及「SVG」「DrawingML」等技术词汇
5. **脚本路径**：所有脚本均在 `scripts/svg/` 下，命令示例已包含正确路径

---

## 步骤① 内容规划

> **视觉偏好 B 或 D 直接进入本文件**：从步骤①正常执行。

**输入**：配置摘要（视觉风格、主题色、视觉素材来源、场景受众、页数、信息呈现偏好、内容来源）

**动作**：完整阅读 `references/shared/content-planner.md`，按其指导完成内容规划。

**输出**：`.temp/{project}/content_plan.md`，包含：
- 完整页面大纲（每页标题 + 要点 + 页面类型）
- 每页图表类型（若有）
- 关键词列表（供后续图标选取）

**第二阶路由修正**（仅视觉偏好 B 可能发生修正）：

对照内容规划中的图表类型：若全是标准图表（柱/折/饼/散/表格）且风格为商务简约/正式庄重/温润亲和 → 切换回 PptxGenJS：**停止本文件，读取 `references/pptx/create-workflow.md`，从 Step 5 继续执行**（内容规划已完成，content_plan.md 已写入）。

其他情况（包括 D，或 B 不满足上述条件）：不修正，继续步骤②。

---

## 步骤② 生成设计合约

**输入**：`content_plan.md` + 配置摘要

**动作**：按下方字段映射，一次性生成 `design_spec.md` 和 `spec_lock.md`，不增加用户交互。

阅读 `references/pptx-svg/spec-lock-reference.md` 了解完整字段格式，然后按以下规则推导：

### spec_lock.md 字段映射

**`## canvas`**（固定）
```
- viewBox: 0 0 1280 720
- format: PPT 16:9
```

**`## colors`** — 从主题色展开

| 字段 | 推导规则 |
|---|---|
| `bg` | 商务简约/正式庄重/温润亲和 → `#FFFFFF`；高端品牌/中国风 → `#FAFAF8` 或深色；炫彩科技 → 深色背景 |
| `primary` | 用户确认的主题色 |
| `accent` | 从 primary 生成互补或类比色；若有第二主题色则优先使用 |
| `secondary_accent` | primary 调浅 25% 或第三品牌色 |
| `text` | 浅色背景 → `#1D1D1D`；深色背景 → `#F0F0F0` |
| `text_secondary` | 浅色背景 → `#666666`；深色背景 → `#A0A0A0` |
| `border` | 浅色背景 → `#E5E8F0`；深色背景 → `#2A3A4A` |
| `image_rendering` | 仅当视觉素材 = AI 生成时填写，按下表推导，省略则 image_gen.md 自行判断 |
| `image_palette` | 同上 |

`image_rendering / image_palette` 内部推导表（视觉素材 = AI 生成时使用）：

| 视觉风格 | 推荐 image_rendering | 推荐 image_palette |
|---|---|---|
| 商务简约 / 正式庄重 | `vector-illustration` | `cool-corporate` |
| 科技专业 / 炫彩科技 | `3d-isometric` | `tech-neon` |
| 温润亲和 | `vector-illustration` | `warm-earth` |
| 高端品牌 | `editorial` | `editorial-classic` |
| 中国风 | `paper-cut` | `earthy-dusty` |
| 自定义 | `vector-illustration` | `cool-corporate` |

**`## typography`** — 从视觉风格推导字体族，从信息呈现偏好推导字号锚点

字体族（相同则省略，`code_family` 有代码内容时必填）：

| 视觉风格 | font_family（默认回落） | title_family（与默认不同时才写） | emphasis_family |
|---|---|---|---|
| 商务简约 / 正式庄重 | `"Microsoft YaHei", Arial, sans-serif` | `Georgia, "Times New Roman", serif` | `Georgia, "Times New Roman", serif` |
| 科技专业 | `"Microsoft YaHei", Arial, sans-serif` | 同默认，**省略** | 同默认，**省略** |
| 温润亲和 | `"Alibaba PuHuiTi", "Microsoft YaHei", sans-serif` | 同默认，**省略** | 同默认，**省略** |
| 高端品牌 | `"Microsoft YaHei", Arial, sans-serif` | `Georgia, SimSun, serif` | `Georgia, serif` |
| 中国风 | `"Microsoft YaHei", SimHei, sans-serif` | `SimSun, "STSong", serif` | `SimSun, serif` |
| 炫彩科技 / 自定义 | `"Microsoft YaHei", Arial, sans-serif` | 同默认，**省略** | 同默认，**省略** |

字号锚点（按信息呈现偏好推导）：

| 信息呈现偏好 | body | title | subtitle | annotation |
|---|---|---|---|---|
| 图表可视化为主 | `18` | `28` | `22` | `13` |
| 图文并重 / Agent 判断 | `22` | `32` | `24` | `14` |
| 文字叙述为主 | `24` | `36` | `26` | `15` |

扩展字号槽（按实际内容按需添加，不必填全）：
- `cover_title`：封面超大标题，约 body × 3.5–5，例如 `cover_title: 72`
- `hero_number`：咨询风大数字，约 body × 2–3，例如 `hero_number: 48`
- `chart_annotation`：图表注释，约 body × 0.6，例如 `chart_annotation: 13`

**`## icons`** — 从视觉风格选库，从内容规划选 inventory

| 视觉风格 | 推荐图标库 |
|---|---|
| 商务简约 / 正式庄重 / 高端品牌 / 温润亲和 / 中国风 | `chunk-filled` |
| 科技专业 / 炫彩科技 | `phosphor-duotone` |

`inventory`：从 `content_plan.md` 提取 4–8 个关键主题词，用 `ls svg-templates/icons/<library>/ | grep <keyword>` 验证文件存在，取验证通过的文件名（不含 `.svg`）。

**`## images`**（影响 quality checker，必须在 step④ SVG 生成前填好）

- **视觉素材 = AI 生成**：step② 先按 content_plan 逐页规划图片，写入 spec_lock 占位条目（slug 确定，filename 待填）；step③ 配图完成后用真实 filename 回填。
  - 格式：`- <slug>: images/<filename>`；无法裁剪（数据截图、密集图表）时追加 ` | no-crop`
  - 封面背景、章节底图 → 可裁剪（默认）；数据图表截图、证书、公式图 → 追加 `no-crop`
  - 示例：`- cover_bg: images/cover_bg.jpg`、`- revenue_chart: images/q3_revenue.png | no-crop`
- **视觉素材 = 自备图片**：列出所有图片，同上格式
- **不需要图片**：省略整节

**`## page_rhythm`** — 从 content_plan 每页类型推导

| 页面类型 | rhythm |
|---|---|
| 封面、目录、章节分隔、结尾 | `anchor` |
| 引言/过渡/单一核心论点/大图展示 | `breathing` |
| 内容页（要点/数据/图表/对比/KPI） | `dense` |

格式：`- P01: anchor`（页码两位补零）。`breathing` 页不可为凑节奏的空白页，必须有独立表达意图。

**`## page_layouts`** — 读取 `svg-templates/layouts/layouts_index.json` 匹配模板

1. 读取 `svg-templates/layouts/layouts_index.json`，了解所有版式名称和描述
2. 逐页对照 content_plan 的页面类型和内容，语义匹配最合适的版式 SVG basename
3. 有匹配 → 填写 `- P<NN>: <basename>`；无匹配 → 不填（自由设计）；全无匹配 → 省略整节
4. **同一页同时出现 page_layouts 和 page_charts 时，确认版式模板能容纳该图表，否则省略 page_layouts 条目**

**`## page_charts`** — 读取 `svg-templates/charts/charts_index.json` 匹配图表模板

1. 读取 `svg-templates/charts/charts_index.json` 的全部条目（含 summary "Pick for … Skip if …" 字段）
2. 逐页对照 content_plan 中的图表类型，语义匹配：数据类（趋势/比较/构成）和结构类（流程/矩阵/旅程图/方法论框架）均在匹配范围内
3. 有匹配 → 填写 `- P<NN>: <chart_name>`；无匹配（`no-template-match`）→ 不填（executor 自由设计）；全无图表 → 省略整节

**`## forbidden`** — 从 `references/pptx-svg/spec-lock-reference.md` 原样复制该节全部条目。

**输出**：
- `.temp/{project}/design_spec.md`（简要版，记录风格意图和页面大纲，非 ppt-master 11 节完整格式）
- `.temp/{project}/spec_lock.md`（机器可读执行合约，executor 每页重读的信源）

---

## 步骤③ 配图（条件执行）

**触发条件**：视觉素材来源 = AI 生成，或视觉素材 = 已有自备图片（需验证路径存在）

**动作**：完整阅读 `references/shared/image-gen.md`，按其指导生成或引入图片。

图片生成完成后，回填 `spec_lock.md` 的 `## images` 节。

**跳过条件**：视觉素材来源 = 不需要图片。

---

## 步骤④ SVG 生成

**必须先读取**：`references/pptx-svg/shared-standards.md`（SVG 技术约束）

### 生成前准备（批量读取，每次生成只做一次）

1. 输出设计参数确认：画布尺寸、body 字号、主题色 HEX、字体方案
2. 批量读取所有 `spec_lock.md page_layouts` 中引用的版式 SVG（`svg-templates/layouts/<basename>.svg`）
3. 批量读取所有 `spec_lock.md page_charts` 中引用的图表 SVG（`svg-templates/charts/<name>.svg`）
4. 创建输出目录：`.temp/{project}/svg_output/`

### 逐页生成规则

**每页生成前**必须执行：
```
重读 .temp/{project}/spec_lock.md
```

取出当前页的：
- `page_rhythm`：确定布局密度（anchor/breathing/dense）
- `page_layouts`：确定版式模板（若有）
- `page_charts`：确定图表模板（若有）

所有颜色、字体、图标、图片引用**只能**来自 spec_lock.md，不得凭记忆或临时发明。

**输出命名**：`svg_output/<NN>_<page_slug>.svg`（NN 两位补零）

**含图表的页面**：在 `<g id="chartArea">` 内数据元素之前写入坐标标记（见 `shared-standards.md §5`）。

生成过程中不得向用户确认，不得分批（禁止「先生成 5 页」），一次连续完成全部页面。

---

## 步骤⑤ 质量检查

全部 SVG 生成完毕后运行：

```bash
python3 scripts/svg/svg_quality_checker.py .temp/{project}
```

**处理规则**：
- `error`（禁用特性、viewBox 不匹配、spec_lock 漂移等）→ **必须修复**，重新生成该页后再次运行检查
- `warning`（低分辨率图片、非 PPT 安全字体尾部等）→ 能修则修，否则记录后放行

> 必须在 `finalize_svg.py` 之前运行——后处理会重写 SVG 并掩盖部分违规。

---

## 步骤⑥ SVG 后处理

```bash
python3 scripts/svg/finalize_svg.py .temp/{project}
```

将处理后的 SVG 写入 `.temp/{project}/svg_final/`。执行四步：图标展开 → 图片对齐嵌入 → 文字拍平 → 圆角矩形转路径。

---

## 步骤⑦ 导出 PPTX

```bash
python3 scripts/svg/svg_to_pptx.py .temp/{project}
```

输出：`.temp/{project}/exports/{project_name}_{timestamp}.pptx`

向用户提供输出文件路径。告知文字内容均可在 PPT 中直接编辑；如有视觉冲击型元素（特效图形等）为嵌入式图元，不支持在 PPT 内拖拽修改。

---

## 工作目录结构

```
.temp/{project}/
├── content_plan.md
├── design_spec.md
├── spec_lock.md
├── images/                  ← AI 生图 / 自备图片
├── svg_output/              ← 步骤④ 原始 SVG
├── svg_final/               ← 步骤⑥ 后处理 SVG
└── exports/                 ← 步骤⑦ 最终 .pptx
```
