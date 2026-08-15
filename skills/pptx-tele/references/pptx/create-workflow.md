---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '54118f95-cf05-444f-a108-e7d78aa5a7b6'
  PropagateID: '54118f95-cf05-444f-a108-e7d78aa5a7b6'
  ReservedCode1: 'c2b2276a-8655-42ce-b449-739fe498ef37'
  ReservedCode2: 'c2b2276a-8655-42ce-b449-739fe498ef37'
---

# .pptx 创建工作流

> 本文档是 `.pptx` 创建路线的执行指南。开始创建前必须完整阅读本文件，并按需读取引用的 reference。

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

## Creating a new PowerPoint presentation **without a template**

### Workflow: Creating from Scratch (PptxGenJS)

**Use when no template or reference presentation is available.**
**CRITICAL**: You MUST read the relevant reference files in the `references/` directory before and during the generation process to ensure correct API usage and styling.

#### Step 1: Research & Requirements
Search to understand user requirements — topic, audience, purpose, tone, content depth.

#### Step 2: Select Color Palette & Fonts
Use the [Design System](references/shared/design-system.md) to select a palette matching the topic. For Chinese text, prioritize the Typography Guidelines listed above (e.g., Microsoft YaHei).

#### Step 3: Select Design Style
Use the Style Recipes in the [Design System](references/shared/design-system.md) to choose a visual style (Sharp, Soft, Rounded, or Pill) matching the presentation tone.

#### Step 3.1: Icon Library Selection

根据视觉风格**只选库，此时不搜索具体图标名**：

| 视觉风格 | 推荐图标库 | 备注 |
|---|---|---|
| 商务简约 / 正式庄重 / 高端品牌 / 温润亲和 / 中国风 | `chunk-filled` | 直线几何、厚重实心，投影清晰 |
| 科技专业 / 炫彩科技 | `phosphor-duotone` | 双色调，现代感强 |

若演示含真实品牌 logo（AWS、GitHub、微信等），额外声明 `simple-icons` 与主库并存；不含品牌 logo 则省略 `simple-icons`。

#### Step 4: Plan Slide Outline
Classify **every slide** as exactly one of the 5 page types detailed in [Slide Types](references/pptx/slide-types.md). Plan the content and layout. Ensure visual variety.

#### Step 4.1: Icon Inventory（大纲确认后执行）

大纲稳定后，按页面逐一枚举需要用到的图标概念，然后 grep 验证真实文件名：

```bash
# 在已选库里搜关键词（以 chunk-filled 为例）
ls svg-templates/icons/chunk-filled/ | grep shield   # → shield.svg, shield-check.svg
ls svg-templates/icons/chunk-filled/ | grep bolt     # → bolt.svg
ls svg-templates/icons/chunk-filled/ | grep chart    # → chart-bar.svg, chart-line.svg, chart-pie.svg
ls svg-templates/icons/chunk-filled/ | grep cloud    # → 没有 → 换词
ls svg-templates/icons/chunk-filled/ | grep server   # → server.svg  ← 替代
ls svg-templates/icons/chunk-filled/ | grep users    # → users.svg
# 品牌 logo 单独搜 simple-icons
ls svg-templates/icons/simple-icons/ | grep github   # → github.svg
```

**选名规则**：
1. 有精确匹配就用（`shield` → `shield.svg`）
2. 多个候选选语义最贴的（`chart-bar` 比 `chart-line` 更适合柱状图页）
3. 搜不到就换近义词（`cloud` 没有 → 试 `server` / `globe` / `network`）
4. **禁止跨风格库凑数**（chunk-filled 缺图标，不可去其他风格库借）

将验证通过的图标清单追加到 `spec_lock_lite.md`：

```markdown
## icons
- library: chunk-filled
- brand_library: simple-icons   ← 仅含品牌 logo 时才写这行
- inventory: shield, bolt, users, chart-bar, server, target, arrow-right
- brand_inventory: github, amazonaws   ← 仅 brand_library 声明时才写
```

#### Step 4.2: 路由修正 + spec_lock_lite 生成（SVG 集成新增）

> 本步骤只在 **A（改着顺手）或 C（全程可编辑）** 进入本文件时执行。B 和 D 从一开始就走 `references/pptx-svg/create-workflow.md`，不会到达此处。

**路由说明**（本文件只在 A 或 C 进入，无路由切换）：

- A / C 始终保持 PptxGenJS，不切换引擎
- 遇到 SVG-only 图表（桑基/瀑布/漏斗/旭日/弦/复杂雷达等）时，保持 PptxGenJS，告知用户「该图表将以可编辑方式近似实现，数值和文字均可编辑」，继续后续步骤

**spec_lock_lite 生成**：

在 `{工作目录}/.temp/` 下生成 `spec_lock_lite.md`，内容如下（根据实际配置填写）：

```markdown
# Spec Lock Lite

> PptxGenJS 路线轻量防漂移锁。每 3 页重读一次。

## canvas
- format: PPT 16:9

## colors
- bg: #FFFFFF
- primary: #......
- accent: #......
- secondary_accent: #......
- text: #......
- text_secondary: #......
- border: #......

## typography
- font_family: "Microsoft YaHei", Arial, sans-serif
- title_family: [根据视觉风格填写]
- body_family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif
- title: 32
- body: 22
- subtitle: 24

## icons
- library: chunk-filled
- inventory: [Step 4.1 完成后填入，逗号分隔]
```

> `## icons` 节在 Step 4.1 完成后回填；路由修正判定完成后再生成本文件也可——先留空，Step 4.1 跑完后补上。

#### Step 5: Optional AI Image Plan
If the user selected "视觉素材来源 → 需要 AI 生成", read [`references/shared/image-gen.md`](references/shared/image-gen.md) and [`references/shared/image-prompts.md`](references/shared/image-prompts.md) before writing slide code.

Create an AI image plan after the outline is stable and before writing slide JS:

| Slide | Purpose | Image type | Aspect ratio | Size | Output path | Slot |
|-------|---------|------------|--------------|------|-------------|------|

Rules:
- Write the expected number of generated images in the execution summary and image plan.
- If the image generation service reports quota or availability limits, ask the user to reduce image count, use native PPT components, or switch route.
- Save `.pptx` process images under `{工作目录}/.temp/images/`.
- Do not ask AI images to generate key text, precise numbers, logos, watermarks, page chrome, or legal/brand copy. Use PPT native text and charts for accurate content.
- Keep one deck-level style prefix so all generated images match the selected design system.
- Prefer a no-text style reference image if using 图生图模式; do not use a content-heavy finished slide as the default style reference.
- If a single image fails, retry once. If it still fails, replace that image with native shapes, SVG icons, or a color block and continue.

**图像校验（排版 `.pptx` 配图）：** 所有 AI 配图生成完毕后，按照 `references/shared/image-gen.md` 的"图像校验"章节对每张图片进行校验。校验可并行执行。

校验 FAIL 的重试仍 FAIL 时，该配图位置改用原生形状、SVG 图标或色块占位，继续完成整份文档（排版 PPT 的核心信息由原生文字承载，配图只是装饰素材，降级不影响信息传达），并在执行摘要中标注降级页码。

#### Step 6: Generate Slide JS Files
Create one JS file per slide in the `slides/` directory. Each file must export a synchronous `createSlide(pres, theme)` function.
- **CRITICAL API REFERENCE**: You MUST read [PptxGenJS Reference](references/pptx/pptxgenjs-api.md) for the exact API syntax for adding text, shapes, and charts. 
- Tell subagents to strictly follow the Theme Object Contract and Slide Output Format specified in the references.
- Reference generated images with `slide.addImage({ path })` and keep source PNGs until final PPTX QA is complete.

**SVG 图标使用规范（基于 Step 4.1 的 icon inventory）**：

PPT 2016+ 原生支持 SVG，PptxGenJS 可用 `slide.addImage()` 直接嵌入 SVG 图标，PPT 内矢量渲染，任意缩放不失真。图标在 PPT 中是嵌入式媒体对象（不可在 PPT 内部编辑节点），这对图标场景完全适合。

在 `slides/` 目录内（或 `compile.js`）定义辅助函数：

```javascript
// slides/icon-helper.js
const fs = require('fs');
const path = require('path');

/**
 * 读取 SVG 图标并应用主题色，返回 data URI 供 slide.addImage() 使用。
 * @param {string} library  - 图标库名，如 'chunk-filled'
 * @param {string} name     - 图标文件名（不含 .svg），如 'shield'
 * @param {string} color    - HEX 颜色（不含 #），如 '1A73E8'
 * @returns {string} data URI
 */
function svgIcon(library, name, color) {
  const iconPath = path.join('svg-templates', 'icons', library, `${name}.svg`);
  let svg = fs.readFileSync(iconPath, 'utf8');
  // SVG fill 属性需要 '#' 前缀，而 PptxGenJS 颜色值不带 '#'
  const svgColor = '#' + color;
  svg = svg.replace(/fill="currentColor"/g, `fill="${svgColor}"`);
  // 仅在 <svg> 根标签没有 fill 时才追加，避免重复属性导致无效 XML
  if (!/\bfill="/.test(svg.match(/<svg[^>]*>/)[0])) {
    svg = svg.replace(/(<svg[^>]*?)(?= *>)/, `$1 fill="${svgColor}"`);
  }
  return 'data:image/svg+xml;base64,' + Buffer.from(svg).toString('base64');
}

module.exports = { svgIcon };
```

在 slide 文件中引用：

```javascript
const { svgIcon } = require('./icon-helper');

// 用 primary 色的 shield 图标，左上角 0.3in × 0.3in
slide.addImage({
  data: svgIcon('chunk-filled', 'shield', theme.primary),
  x: 0.3, y: 1.2, w: 0.3, h: 0.3
});

// 品牌 logo 用原色（simple-icons 通常有品牌色，传 'currentColor' 保持原色）
slide.addImage({
  data: svgIcon('simple-icons', 'github', '#24292F'),
  x: 1.0, y: 6.5, w: 0.25, h: 0.25
});
```

**只使用 spec_lock_lite.md `## icons.inventory` 白名单内的图标名**；白名单外的图标名经 Step 4.1 验证后才可补充进去。

**漂移防护纪律（SVG 集成新增）**：

> **批次自检**（每 3 页执行一次）：每生成完第 3、6、9…页 JS 文件后，重读 `.temp/spec_lock_lite.md`，对**本批**代码中出现的色值和字体名做即时核对；发现偏离立即在本批内修正，再继续生成后续页面。
>
> 自检范围：① 代码中出现的色值是否与 spec_lock_lite 声明的一致（允许视觉不可辨的近似）；② 字体名是否在 spec_lock_lite 白名单中。不做图片路径检查（路径错误是显性 bug，node 执行阶段会报错）。

#### Step 7: Compile into Final PPTX
Create `slides/compile.js` to combine all slide modules.

#### Step 7.5: 全局漂移复核（SVG 集成新增）

全部页面 JS 文件生成完毕后，重读 `.temp/spec_lock_lite.md`，对整份代码做最终漂移扫描：

- 逐页检查所有色值是否与 spec_lock_lite 声明一致
- 逐页检查所有字体名是否在白名单中
- 发现偏离的页面：立即修正该页代码，再继续后续步骤

#### Step 8: QA (Required)
You MUST read [Pitfalls & QA](references/pptx/pitfalls.md) and execute the QA process to catch common rendering errors before finalizing the PPTX.

### Design Principles

**CRITICAL**: Before creating any presentation, analyze the content and choose appropriate design elements:
1. **Consider the subject matter**: What is this presentation about? What tone, industry, or mood does it suggest?
2. **Check for branding**: If the user mentions a company/organization, consider their brand colors and identity
3. **Match palette to content**: Select colors that reflect the subject
4. **State your approach**: Explain your design choices before writing code

**Requirements**:
- ✅ State your content-informed design approach BEFORE writing code
- ✅ Use appropriate fonts based on content language:
  - **中文内容（推荐）**：微软雅黑、思源黑体、思源宋体、阿里巴巴普惠体、华文细黑
  - **英文内容/通用**：Arial, Helvetica, Times New Roman, Georgia, Courier New, Verdana, Tahoma, Trebuchet MS, Impact
  - **Web-safe fonts（兼容性）**：上述所有字体均为常用字体，跨平台兼容性好
- ✅ Create clear visual hierarchy through size, weight, and color
- ✅ Ensure readability: strong contrast, appropriately sized text, clean alignment
- ✅ Be consistent: repeat patterns, spacing, and visual language across slides
- ✅ For Chinese content, prefer "微软雅黑" (Microsoft YaHei) as default font family

#### Color Palette Selection

**Choosing colors creatively**:
- **Think beyond defaults**: What colors genuinely match this specific topic? Avoid autopilot choices.
- **Consider multiple angles**: Topic, industry, mood, energy level, target audience, brand identity (if mentioned)
- **Be adventurous**: Try unexpected combinations - a healthcare presentation doesn't have to be green, finance doesn't have to be navy
- **Build your palette**: Pick 3-5 colors that work together (dominant colors + supporting tones + accent)
- **Ensure contrast**: Text must be clearly readable on backgrounds

**Example color palettes** (use these to spark creativity - choose one, adapt it, or create your own):

### 中国风配色方案（Chinese Style Palettes - 适用于中文内容）

C1. **科技蓝**：科技蓝 (#0052D9), 深蓝 (#0033A0), 浅蓝 (#E6F0FF), 白色 (#FFFFFF)
C2. **党政红金**：中国红 (#DE2910), 金色 (#FFD700), 深红 (#8B0000), 米白 (#FFF8DC)
C3. **淡雅水墨**：墨黑 (#2C2C2C), 灰色 (#808080), 浅灰 (#D3D3D3), 宣纸白 (#F5F5DC)
C4. **新中式**：朱砂红 (#E86161), 青瓷色 (#7FB068), 米黄 (#F2E6CE), 深灰 (#4A4A4A)
C5. **商务深灰**：深灰 (#333333), 中灰 (#666666), 浅灰 (#CCCCCC), 白色 (#FFFFFF)
C6. **竹韵青**：竹青 (#789262), 浅绿 (#B5C99A), 米白 (#F7F7F0), 深绿 (#2F4F4F)
C7. **紫气东来**：紫罗兰 (#9370DB), 浅紫 (#DDA0DD), 金黄 (#FFD700), 白色 (#FFFFFF)
C8. **江南烟雨**：青灰 (#6B7A8F), 浅蓝灰 (#A8B8C8), 灰白 (#D9E4EC), 深蓝 (#2C3E50)

### 国际通用配色方案（International Palettes）

1. **Classic Blue**: Deep navy (#1C2833), slate gray (#2E4053), silver (#AAB7B8), off-white (#F4F6F6)
2. **Teal & Coral**: Teal (#5EA8A7), deep teal (#277884), coral (#FE4447), white (#FFFFFF)
3. **Bold Red**: Red (#C0392B), bright red (#E74C3C), orange (#F39C12), yellow (#F1C40F), green (#2ECC71)
4. **Warm Blush**: Mauve (#A49393), blush (#EED6D3), rose (#E8B4B8), cream (#FAF7F2)
5. **Burgundy Luxury**: Burgundy (#5D1D2E), crimson (#951233), rust (#C15937), gold (#997929)
6. **Deep Purple & Emerald**: Purple (#B165FB), dark blue (#181B24), emerald (#40695B), white (#FFFFFF)
7. **Cream & Forest Green**: Cream (#FFE1C7), forest green (#40695B), white (#FCFCFC)
8. **Pink & Purple**: Pink (#F8275B), coral (#FF574A), rose (#FF737D), purple (#3D2F68)
9. **Lime & Plum**: Lime (#C5DE82), plum (#7C3A5F), coral (#FD8C6E), blue-gray (#98ACB5)
10. **Black & Gold**: Gold (#BF9A4A), black (#000000), cream (#F4F6F6)
11. **Sage & Terracotta**: Sage (#87A96B), terracotta (#E07A5F), cream (#F4F1DE), charcoal (#2C2C2C)
12. **Charcoal & Red**: Charcoal (#292929), red (#E33737), light gray (#CCCBCB)
13. **Vibrant Orange**: Orange (#F96D00), light gray (#F2F2F2), charcoal (#222831)
14. **Forest Green**: Black (#191A19), green (#4E9F3D), dark green (#1E5128), white (#FFFFFF)
15. **Retro Rainbow**: Purple (#722880), pink (#D72D51), orange (#EB5C18), amber (#F08800), gold (#DEB600)
16. **Vintage Earthy**: Mustard (#E3B448), sage (#CBD18F), forest green (#3A6B35), cream (#F4F1DE)
17. **Coastal Rose**: Old rose (#AD7670), beaver (#B49886), eggshell (#F3ECDC), ash gray (#BFD5BE)
18. **Orange & Turquoise**: Light orange (#FC993E), grayish turquoise (#667C6F), white (#FCFCFC)

#### Visual Details Options

**Geometric Patterns**:
- Diagonal section dividers instead of horizontal
- Asymmetric column widths (30/70, 40/60, 25/75)
- Rotated text headers at 90° or 270°
- Circular/hexagonal frames for images
- Triangular accent shapes in corners
- Overlapping shapes for depth

**Border & Frame Treatments**:
- Thick single-color borders (10-20pt) on one side only
- Double-line borders with contrasting colors
- Corner brackets instead of full frames
- L-shaped borders (top+left or bottom+right)
- Underline accents beneath headers (3-5pt thick)

**Typography Treatments**:
- Extreme size contrast (72pt headlines vs 11pt body)
- All-caps headers with wide letter spacing
- Numbered sections in oversized display type
- Monospace (Courier New) for data/stats/technical content
- Condensed fonts (Arial Narrow) for dense information
- Outlined text for emphasis

**Chart & Data Styling**:
- Monochrome charts with single accent color for key data
- Horizontal bar charts instead of vertical
- Dot plots instead of bar charts
- Minimal gridlines or none at all
- Data labels directly on elements (no legends)
- Oversized numbers for key metrics

**Layout Innovations**:
- Full-bleed images with text overlays
- Sidebar column (20-30% width) for navigation/context
- Modular grid systems (3×3, 4×4 blocks)
- Z-pattern or F-pattern content flow
- Floating text boxes over colored shapes
- Magazine-style multi-column layouts

**Background Treatments**:
- Solid color blocks occupying 40-60% of slide
- Gradient fills (vertical or diagonal only)
- Split backgrounds (two colors, diagonal or vertical)
- Edge-to-edge color bands
- Negative space as a design element

### Layout Tips
**When creating slides with charts or tables:**
- **Two-column layout (PREFERRED)**: Use a header spanning the full width, then two columns below - text/bullets in one column and the featured content in the other. This provides better balance and makes charts/tables more readable. Use flexbox with unequal column widths (e.g., 40%/60% split) to optimize space for each content type.
- **Full-slide layout**: Let the featured content (chart/table) take up the entire slide for maximum impact and readability
- **NEVER vertically stack**: Do not place charts/tables below text in a single column - this causes poor readability and layout issues

### 中文排版规则（Chinese Typography Guidelines）

#### 字号对照表（Font Size Reference）

中文常用字号与磅值(pt)对照：

| 中文称呼 | 磅值(pt) | 英文近似 | 用途 |
|---------|---------|---------|------|
| 初号 | 42pt | - | 标题/封面 |
| 小初 | 36pt | - | 大标题 |
| 一号 | 26pt | 32pt | 主标题 |
| 小一 | 24pt | 28pt | 副标题 |
| 二号 | 22pt | 24pt | 二级标题 |
| 小二 | 18pt | 20pt | 三级标题 |
| 三号 | 16pt | 18pt | 正文大标题 |
| 小三 | 15pt | 16pt | 正文小标题 |
| 四号 | 14pt | 14pt | 正文标题 |
| 小四 | 12pt | 12pt | **正文默认** |
| 五号 | 10.5pt | 10pt | 小字正文 |
| 小五 | 9pt | 9pt | 注释/说明 |

**推荐使用**：
- 标题：18-24pt（小二至二号）
- 正文：12-14pt（小四至四号）
- 注释：9-10pt（小五至五号）

#### 行首行尾禁则（Line Start/End Prohibition Rules）

以下标点符号不应出现在行首或行尾：

**不应出现在行尾**（需要与后续字符保持在一起）：
- 开括号：`(` `（` `[` `【` `{` `「` `『`
- 前置标点：`"` `"` `'` `'`

**不应出现在行首**（需要与前置字符保持在一起）：
- 闭括号：`)` `）` `]` `】` `}` `」` `』`
- 后置标点：`,` `,` `.` `.` `;` `；` `:` `：` `!` `！` `?` `？`
- 省略号：`......` `……`
- 破折号：`——`

#### 中英文间距（Chinese-English Spacing）

在中文字符与英文字符/数字之间添加适当间距（约0.25em）：

**示例**：
- ❌ 错误：使用PowerPoint创建演示文稿
- ✅ 正确：使用 PowerPoint 创建演示文稿
- ❌ 错误：2024年度报告
- ✅ 正确：2024 年度报告

**实现方式**（在HTML/CSS中）：
```css
.chinese-text {
    letter-spacing: 0.05em;
}
.chinese-text + .english-text,
.chinese-text + .number {
    margin-left: 0.25em;
}
```

#### 推荐的中文字体设置

**默认字体栈**（按优先级排序）：
```css
font-family: "Microsoft YaHei", "微软雅黑", "Source Han Sans CN",
             "思源黑体", "Alibaba PuHuiTi", "阿里巴巴普惠体",
             "STHeiti", "华文细黑", "SimHei", "黑体",
             sans-serif;
}
```

**标题使用**（更有力量感）：
- "Microsoft YaHei Bold" / "微软雅黑 Bold"
- "Source Han Sans CN Bold" / "思源黑体 Bold"

**正文使用**（易读性优先）：
- "Microsoft YaHei" / "微软雅黑"
- "Alibaba PuHuiTi" / "阿里巴巴普惠体"

#### 标点符号使用规范

**中文标点符号优先**：
- 在纯中文文本中使用中文标点：`，。；：？！""''（）【】`
- 在中英混排文本中，根据前后内容选择合适的标点

**数字与单位**：
- 数字与中文单位之间不加空格：100元、50公斤、25%
- 英文单位前加空格：100 kg, 25 %, 30 px

### PPT旧格式支持（Legacy PPT Format Support）

#### 转换旧版PPT为PPTX

当用户提供`.ppt`格式文件（旧版PowerPoint格式）时，需要先转换为`.pptx`格式：

```bash
# 使用LibreOffice进行格式转换
soffice --headless --convert-to pptx input.ppt
```

**注意事项**：
- 转换后的文件可能需要检查格式兼容性
- 某些旧版特效可能无法完美转换
- 建议转换后进行视觉验证

**自动检测与转换脚本**：
```bash
# 检测文件格式并自动转换
python scripts/convert_legacy_ppt.py input.ppt output.pptx
```

## Creating a new PowerPoint presentation **using a template**

When you need to create a presentation that follows an existing template's design, you'll need to duplicate and re-arrange template slides before then replacing placeholder context.

### Workflow
1. **Extract template text AND create visual thumbnail grid**:
   * Extract text: `python -m markitdown template.pptx > template-content.md`
   * Read `template-content.md`: Read the entire file to understand the contents of the template presentation. **NEVER set any range limits when reading this file.**
   * Create thumbnail grids: `python scripts/thumbnail.py template.pptx`
   * See [Creating Thumbnail Grids](#creating-thumbnail-grids) section for more details

2. **Analyze template and save inventory to a file**:
   * **Visual Analysis**: Review thumbnail grid(s) to understand slide layouts, design patterns, and visual structure
   * Create and save a template inventory file at `template-inventory.md` containing:
     ```markdown
     # Template Inventory Analysis
     **Total Slides: [count]**
     **IMPORTANT: Slides are 0-indexed (first slide = 0, last slide = count-1)**

     ## [Category Name]
     - Slide 0: [Layout code if available] - Description/purpose
     - Slide 1: [Layout code] - Description/purpose
     - Slide 2: [Layout code] - Description/purpose
     [... EVERY slide must be listed individually with its index ...]
     ```
   * **Using the thumbnail grid**: Reference the visual thumbnails to identify:
     - Layout patterns (title slides, content layouts, section dividers)
     - Image placeholder locations and counts
     - Design consistency across slide groups
     - Visual hierarchy and structure
   * This inventory file is REQUIRED for selecting appropriate templates in the next step

3. **Create presentation outline based on template inventory**:
   * Review available templates from step 2.
   * Choose an intro or title template for the first slide. This should be one of the first templates.
   * Choose safe, text-based layouts for the other slides.
   * **CRITICAL: Match layout structure to actual content**:
     - Single-column layouts: Use for unified narrative or single topic
     - Two-column layouts: Use ONLY when you have exactly 2 distinct items/concepts
     - Three-column layouts: Use ONLY when you have exactly 3 distinct items/concepts
     - Image + text layouts: Use ONLY when you have actual images to insert
     - Quote layouts: Use ONLY for actual quotes from people (with attribution), never for emphasis
     - Never use layouts with more placeholders than you have content
     - If you have 2 items, don't force them into a 3-column layout
     - If you have 4+ items, consider breaking into multiple slides or using a list format
   * Count your actual content pieces BEFORE selecting the layout
   * Verify each placeholder in the chosen layout will be filled with meaningful content
   * Select one option representing the **best** layout for each content section.
   * Save `outline.md` with content AND template mapping that leverages available designs
   * Example template mapping:
      ```
      # Template slides to use (0-based indexing)
      # WARNING: Verify indices are within range! Template with 73 slides has indices 0-72
      # Mapping: slide numbers from outline -> template slide indices
      template_mapping = [
          0,   # Use slide 0 (Title/Cover)
          34,  # Use slide 34 (B1: Title and body)
          34,  # Use slide 34 again (duplicate for second B1)
          50,  # Use slide 50 (E1: Quote)
          54,  # Use slide 54 (F2: Closing + Text)
      ]
      ```

   * **Optional AI images**: If the user selected AI-generated visual assets, read `references/shared/image-gen.md` and `references/shared/image-prompts.md` after the outline and template mapping are stable. Generate a plan listing slide index, placeholder/slot, image type, size, output path, and expected image count. Save generated images under `{工作目录}/.temp/images/` and only reference them from the replacement or post-processing step. Do not generate key text or precise data inside images. All AI images must be validated per the "图像校验" section in `references/shared/image-gen.md` before assembly; on FAIL after retry, replace the slot with native shapes, SVG icons, or a color block.

4. **Duplicate, reorder, and delete slides using `rearrange.py`**:
   * Use the `scripts/rearrange.py` script to create a new presentation with slides in the desired order:
     ```bash
     python scripts/rearrange.py template.pptx working.pptx 0,34,34,50,52
     ```
   * The script handles duplicating repeated slides, deleting unused slides, and reordering automatically
   * Slide indices are 0-based (first slide is 0, second is 1, etc.)
   * The same slide index can appear multiple times to duplicate that slide

5. **Extract ALL text using the `inventory.py` script**:
   * **Run inventory extraction**:
     ```bash
     python scripts/inventory.py working.pptx text-inventory.json
     ```
   * **Read text-inventory.json**: Read the entire text-inventory.json file to understand all shapes and their properties. **NEVER set any range limits when reading this file.**

   * The inventory JSON structure:
      ```json
        {
          "slide-0": {
            "shape-0": {
              "placeholder_type": "TITLE",  // or null for non-placeholders
              "left": 1.5,                  // position in inches
              "top": 2.0,
              "width": 7.5,
              "height": 1.2,
              "paragraphs": [
                {
                  "text": "Paragraph text",
                  // Optional properties (only included when non-default):
                  "bullet": true,           // explicit bullet detected
                  "level": 0,               // only included when bullet is true
                  "alignment": "CENTER",    // CENTER, RIGHT (not LEFT)
                  "space_before": 10.0,     // space before paragraph in points
                  "space_after": 6.0,       // space after paragraph in points
                  "line_spacing": 22.4,     // line spacing in points
                  "font_name": "Arial",     // from first run
                  "font_size": 14.0,        // in points
                  "bold": true,
                  "italic": false,
                  "underline": false,
                  "color": "FF0000"         // RGB color
                }
              ]
            }
          }
        }
      ```

   * Key features:
     - **Slides**: Named as "slide-0", "slide-1", etc.
     - **Shapes**: Ordered by visual position (top-to-bottom, left-to-right) as "shape-0", "shape-1", etc.
     - **Placeholder types**: TITLE, CENTER_TITLE, SUBTITLE, BODY, OBJECT, or null
     - **Default font size**: `default_font_size` in points extracted from layout placeholders (when available)
     - **Slide numbers are filtered**: Shapes with SLIDE_NUMBER placeholder type are automatically excluded from inventory
     - **Bullets**: When `bullet: true`, `level` is always included (even if 0)
     - **Spacing**: `space_before`, `space_after`, and `line_spacing` in points (only included when set)
     - **Colors**: `color` for RGB (e.g., "FF0000"), `theme_color` for theme colors (e.g., "DARK_1")
     - **Properties**: Only non-default values are included in the output

6. **Generate replacement text and save the data to a JSON file**
   Based on the text inventory from the previous step:
   - **CRITICAL**: First verify which shapes exist in the inventory - only reference shapes that are actually present
   - **VALIDATION**: The replace.py script will validate that all shapes in your replacement JSON exist in the inventory
     - If you reference a non-existent shape, you'll get an error showing available shapes
     - If you reference a non-existent slide, you'll get an error indicating the slide doesn't exist
     - All validation errors are shown at once before the script exits
   - **IMPORTANT**: The replace.py script uses inventory.py internally to identify ALL text shapes
   - **AUTOMATIC CLEARING**: ALL text shapes from the inventory will be cleared unless you provide "paragraphs" for them
   - Add a "paragraphs" field to shapes that need content (not "replacement_paragraphs")
   - Shapes without "paragraphs" in the replacement JSON will have their text cleared automatically
   - Paragraphs with bullets will be automatically left aligned. Don't set the `alignment` property on when `"bullet": true`
   - Generate appropriate replacement content for placeholder text
   - Use shape size to determine appropriate content length
   - **CRITICAL**: Include paragraph properties from the original inventory - don't just provide text
   - **IMPORTANT**: When bullet: true, do NOT include bullet symbols (•, -, *) in text - they're added automatically
   - **ESSENTIAL FORMATTING RULES**:
     - Headers/titles should typically have `"bold": true`
     - List items should have `"bullet": true, "level": 0` (level is required when bullet is true)
     - Preserve any alignment properties (e.g., `"alignment": "CENTER"` for centered text)
     - Include font properties when different from default (e.g., `"font_size": 14.0`, `"font_name": "Lora"`)
     - Colors: Use `"color": "FF0000"` for RGB or `"theme_color": "DARK_1"` for theme colors
     - The replacement script expects **properly formatted paragraphs**, not just text strings
     - **Overlapping shapes**: Prefer shapes with larger default_font_size or more appropriate placeholder_type
   - Save the updated inventory with replacements to `replacement-text.json`
   - **WARNING**: Different template layouts have different shape counts - always check the actual inventory before creating replacements

   Example paragraphs field showing proper formatting:
   ```json
   "paragraphs": [
     {
       "text": "New presentation title text",
       "alignment": "CENTER",
       "bold": true
     },
     {
       "text": "Section Header",
       "bold": true
     },
     {
       "text": "First bullet point without bullet symbol",
       "bullet": true,
       "level": 0
     },
     {
       "text": "Red colored text",
       "color": "FF0000"
     },
     {
       "text": "Theme colored text",
       "theme_color": "DARK_1"
     },
     {
       "text": "Regular paragraph text without special formatting"
     }
   ]
   ```

   **Shapes not listed in the replacement JSON are automatically cleared**:
   ```json
   {
     "slide-0": {
       "shape-0": {
         "paragraphs": [...] // This shape gets new text
       }
       // shape-1 and shape-2 from inventory will be cleared automatically
     }
   }
   ```

   **Common formatting patterns for presentations**:
   - Title slides: Bold text, sometimes centered
   - Section headers within slides: Bold text
   - Bullet lists: Each item needs `"bullet": true, "level": 0`
   - Body text: Usually no special properties needed
   - Quotes: May have special alignment or font properties

7. **Apply replacements using the `replace.py` script**
   ```bash
   python scripts/replace.py working.pptx replacement-text.json output.pptx
   ```

   The script will:
   - First extract the inventory of ALL text shapes using functions from inventory.py
   - Validate that all shapes in the replacement JSON exist in the inventory
   - Clear text from ALL shapes identified in the inventory
   - Apply new text only to shapes with "paragraphs" defined in the replacement JSON
   - Preserve formatting by applying paragraph properties from the JSON
   - Handle bullets, alignment, font properties, and colors automatically
   - Save the updated presentation

   Example validation errors:
   ```
   ERROR: Invalid shapes in replacement JSON:
     - Shape 'shape-99' not found on 'slide-0'. Available shapes: shape-0, shape-1, shape-4
     - Slide 'slide-999' not found in inventory
   ```

   ```
   ERROR: Replacement text made overflow worse in these shapes:
     - slide-0/shape-2: overflow worsened by 1.25" (was 0.00", now 1.25")
   ```

## Creating Thumbnail Grids

To create visual thumbnail grids of PowerPoint slides for quick analysis and reference:

```bash
python scripts/thumbnail.py template.pptx [output_prefix]
```

**Features**:
- Creates: `thumbnails.jpg` (or `thumbnails-1.jpg`, `thumbnails-2.jpg`, etc. for large decks)
- Default: 5 columns, max 30 slides per grid (5×6)
- Custom prefix: `python scripts/thumbnail.py template.pptx my-grid`
  - Note: The output prefix should include the path if you want output in a specific directory (e.g., `workspace/my-grid`)
- Adjust columns: `--cols 4` (range: 3-6, affects slides per grid)
- Grid limits: 3 cols = 12 slides/grid, 4 cols = 20, 5 cols = 30, 6 cols = 42
- Slides are zero-indexed (Slide 0, Slide 1, etc.)

**Use cases**:
- Template analysis: Quickly understand slide layouts and design patterns
- Content review: Visual overview of entire presentation
- Navigation reference: Find specific slides by their visual appearance
- Quality check: Verify all slides are properly formatted

**Examples**:
```bash
# Basic usage
python scripts/thumbnail.py presentation.pptx

# Combine options: custom name, columns
python scripts/thumbnail.py template.pptx analysis --cols 4
```

## Converting Slides to Images

To visually analyze PowerPoint slides, convert them to images using a two-step process:

1. **Convert PPTX to PDF**:
   ```bash
   soffice --headless --convert-to pdf template.pptx
   ```

2. **Convert PDF pages to JPEG images**:
   ```bash
   pdftoppm -jpeg -r 150 template.pdf slide
   ```
   This creates files like `slide-1.jpg`, `slide-2.jpg`, etc.

Options:
- `-r 150`: Sets resolution to 150 DPI (adjust for quality/size balance)
- `-jpeg`: Output JPEG format (use `-png` for PNG if preferred)
- `-f N`: First page to convert (e.g., `-f 2` starts from page 2)
- `-l N`: Last page to convert (e.g., `-l 5` stops at page 5)
- `slide`: Prefix for output files

Example for specific range:
```bash
pdftoppm -jpeg -r 150 -f 2 -l 5 template.pdf slide  # Converts only pages 2-5
```

## Code Style Guidelines
**IMPORTANT**: When generating code for PPTX operations:
- Write concise code
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

## Dependencies

Required dependencies (should already be installed):

- **markitdown**: `pip install "markitdown[pptx]"` (for text extraction from presentations)
- **pptxgenjs**: `npm install -g pptxgenjs` (for creating presentations via html2pptx)

- **react-icons**: `npm install -g react-icons react react-dom` (for icons)
- **sharp**: `npm install -g sharp` (for SVG rasterization and image processing)
- **LibreOffice**: `sudo apt-get install libreoffice` (for PDF conversion)
- **Poppler**: `sudo apt-get install poppler-utils` (for pdftoppm to convert PDF to images)
- **defusedxml**: `pip install defusedxml` (for secure XML parsing)

> AI生成