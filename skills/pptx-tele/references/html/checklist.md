## 代码审查（P0/P1 级）

以下检查项在代码层面完成，不依赖截图。

### P0 · 必须通过

| # | 检查项 | 检查方法 |
|---|--------|----------|
| 1 | CSS 类字号全部有 min() 双约束 | `rg 'font-size:\s*\d+\.?\d*vw[;\s]' template.html template-swiss.html` 输出应为空 |
| 2 | inline style 无纯 vw 字号 | `rg 'font-size:\s*\d+\.?\d*vw"' index.html` 输出应为空 |
| 3 | AI 配图只在有图片槽位的布局 | 对照 layouts.md / layouts-swiss.md 图片槽位栏 |

### P1 · 建议通过

| # | 检查项 | 检查方法 |
|---|--------|----------|
| 1 | **hero 页 gap 用 min() 双约束** — `gap:Nvh` 改为 `gap:min(Nvh,Mvw)`，M ≈ N × 1.78 | 代码审查 |
| 2 | **hero 页无 min-height:80vh** — 用 `align-content:center` 代替 | 代码审查 |
| 3 | **grid 容器用 safe center** — `.grid-4` / `.grid-6` 的 `align-content` 应为 `safe center` | CSS 检查 |

---

## 视觉 QA（P0 级）

Step 4.2 多模态视觉 QA 逐页截图检查。 逐项判断 PASS/FAIL，FAIL 则修代码后重试该页（单页最多 3 次）。

### 密度（D）

| # | 问题 | FAIL 条件 |
|---|------|-----------|
| D1 | 页面大面积留白 | 单页视觉上明显空旷，内容只占一半 |

### 裁切（T）

| # | 问题 | FAIL 条件 |
|---|------|-----------|
| T1 | 底行文字被裁切 | grid/flex 末行卡片文字不完整（与 4.1 文字完整性检查互补，4.1 侧重代码排查，T1 侧重截图确认） |
| T2 | 标题孤字 | 中文标题 ≤4 字未设 nowrap，导致 1-2 字独占一行 |

### 结构（S）

| # | 问题 | FAIL 条件 |
|---|------|-----------|
| S1 | 大纲内容遗漏 | 用户 outline/arc 中的要点未出现在页面 |
| S2 | 必选组件缺失 | 版式要求的必选组件未出现 |

### 风格一致性（F）

| # | 问题 | FAIL 条件 |
|---|------|-----------|
| F1 | 风格交叉污染 | A 类页面用了 B 的 CSS class，或反之 |
| F2 | 多 accent 色 | B 类 deck 同时出现两种高亮色 |