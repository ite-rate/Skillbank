# SVG 路线技术约束

> 本文档是 `references/pptx-svg/create-workflow.md` 步骤④（SVG 生成）的技术规范，在生成第一页 SVG 前必须完整阅读。

---

## 1. SVG 禁用特性（违反则导出失败）

### 1.1 文本字符规则

SVG 是严格 XML，所有文本和属性值必须遵守：

| 字符类型 | 正确写法 | 禁止写法 |
|---|---|---|
| 排版符号（破折号、©、→、NBSP、全角标点等） | **直接写 Unicode 字符**：`—` `©` `→` | HTML named entity：`&mdash;` `&copy;` `&rarr;` `&nbsp;` `&hellip;` 等 |
| XML 保留字符（`&` `<` `>` `"` `'`） | **XML 实体**：`&amp;` `&lt;` `&gt;` `&quot;` `&apos;` | 裸字符：`&` `<` `>` |

### 1.2 结构黑名单

以下标签/属性在生成的 SVG 中**严格禁止**：

| 禁止项 | 说明 |
|---|---|
| `<style>` / `class` | 禁用嵌入样式表和 CSS 类（`<defs>` 内的 `id` 合法） |
| `<foreignObject>` | 禁止嵌入外部内容 |
| `<symbol>` + `<use>` | 禁止符号引用复用（图标用 `<use data-icon="...">` 代替，见下） |
| `textPath` | 禁止路径文本 |
| `@font-face` | 禁止自定义字体声明 |
| `<animate*>` / `<set>` | 禁止 SVG 动画 |
| `<script>` / 事件属性 | 禁止脚本和交互 |
| `<iframe>` | 禁止嵌入框架 |
| `rgba()` | 透明度用 `fill-opacity` / `stroke-opacity` 代替 |
| `<g opacity="...">` | 在每个子元素上单独设置 opacity |
| `mask` | 用渐变叠加矩形代替（参见下方替代方案） |

### 1.3 条件允许

- **`marker-start` / `marker-end`**：仅用于连接线箭头，引用的 `<marker>` 必须在 `<defs>` 内，`orient="auto"`，形状为三角/菱形/圆形之一
- **`clipPath` on `<image>`**：仅用于图片非矩形裁切（圆形头像、圆角卡片等），且 `<clipPath>` 必须在 `<defs>` 内，只能包含单一形状子元素；**禁止**用在非 `<image>` 元素上

---

## 2. PPT 兼容替代写法

| 禁止语法 | 正确替代 |
|---|---|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">...</g>` | 在每个子元素上分别设置 `fill-opacity` / `stroke-opacity` |
| `<image opacity="0.3"/>` | 在图片上叠加一个 `<rect fill="背景色" opacity="0.7"/>` |

---

## 3. 基本 SVG 规则

- **viewBox**：必须与画布尺寸一致（`width` / `height` 与 `viewBox` 匹配）；PPT 16:9 固定用 `viewBox="0 0 1280 720"`
- **背景**：用 `<rect x="0" y="0" width="1280" height="720" fill="#BGCOLOR"/>` 定义页面背景
- **样式**：只用内联属性（`fill=""` `font-size=""`），不用 `<style>` / `class`
- **颜色**：只用 HEX，透明度用 `fill-opacity` / `stroke-opacity`
- **图片引用**：`<image href="../images/xxx.png" preserveAspectRatio="xMidYMid slice"/>`
- **图标**：`<use data-icon="<library>/<name>" x="" y="" width="48" height="48" fill="#HEX"/>` — 后处理自动展开；每套 PPT 只用一个主图标库

---

## 4. 文本规则

### 4.1 同一行的混合样式用一个 `<text>` + `<tspan>`

```xml
<!-- ✅ 正确：一个 <text> → 一个 PPT 文本框，三个 run -->
<text x="100" y="200" font-size="24" fill="#333333">
  实现<tspan fill="#1A73E8" font-weight="bold">10倍</tspan>效率提升
</text>

<!-- ❌ 错误：三个 <text> → 三个独立文本框，对齐易漂移 -->
<text x="100" y="200">实现</text>
<text x="160" y="200" fill="#1A73E8">10倍</text>
<text x="240" y="200">效率提升</text>
```

### 4.2 字体栈

每个 `font-family` 栈必须以跨平台预装字体结尾：`"Microsoft YaHei"` / `SimSun` / `Arial` / `"Times New Roman"` / `Consolas`。非预装字体只能排在栈前面。

### 4.3 字号规范

以 `spec_lock.md` 中的 `body` 值为基准锚点：

| 角色 | 典型比率 | 说明 |
|---|---|---|
| 封面大标题 | 3.0–4.5× body | 视觉冲击 |
| 页面标题 | 1.4–1.8× body | `title` 字段 |
| 副标题 / 章节 | 1.1–1.3× body | `subtitle` 字段 |
| 正文 / 要点 | 1.0× body | 基准 |
| 注释 / 脚注 | 0.6–0.8× body | `annotation` 字段 |

---

## 5. 图表占位标记（含图表的页面必须包含）

每个含数据图表的 SVG 页必须在 `<g id="chartArea">` 内，数据元素之前，写入坐标标记：

```xml
<!-- 矩形图表（柱/折/散/瀑布等） -->
<!-- chart-plot-area: x_min,y_min,x_max,y_max -->

<!-- 饼/环图 -->
<!-- chart-plot-area: pie | center: cx,cy | radius: r -->

<!-- 雷达图 -->
<!-- chart-plot-area: radar | center: cx,cy | radius: r -->
```

---

## 6. 后处理流程说明

`finalize_svg.py` 会对 `svg_output/` 中的 SVG 执行以下步骤，输出到 `svg_final/`：

1. **embed-icons**：将 `<use data-icon="...">` 展开为实际 SVG 图标
2. **align-images**：图片对齐裁切并 Base64 内嵌
3. **flatten-text**：将 `<tspan>` 拍平为独立 `<text>`（供特殊渲染器）
4. **fix-rounded**：将 `<rect rx="..."/>` 转为 `<path>`（供 PPT 形状转换）

> 不要用 `cp` 替代 `finalize_svg.py`——后处理包含 PPTX 导出所必需的转换步骤。
