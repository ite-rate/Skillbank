---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '98a41981-831d-46bb-b660-e610a86562d4'
  PropagateID: '98a41981-831d-46bb-b660-e610a86562d4'
  ReservedCode1: '02b64da1-21a0-4cc7-8a49-c3e1a3702c87'
  ReservedCode2: '02b64da1-21a0-4cc7-8a49-c3e1a3702c87'
---

# infographic 技能精简方案

> 目标：针对 TeleAgent 桌面版运行时，删除无效上下文，减少 token 消耗，同时保留核心功能。

---

## 一、可完全删除的内容

### 1. `## Image Generation Tools` 整节（SKILL.md 第24-46行，约23行）

整节解决"选哪个生图后端"的问题，列举了 Codex `imagegen`、`codex-imagegen`、外部 image-gen skill、Hermes `image_generate` 等多种后端的优先级逻辑。

**删除原因：** TeleAgent 运行时已有内置的 `ImageGen`（文生图）和 `ImageGenWithRef`（图生图）工具，tool description 中完整描述了参数（prompt、size、seed、guidance_scale 等）和约束，无需额外路由逻辑。

**替换为：**

```markdown
## Image Generation

使用运行时内置的 ImageGen / ImageGenWithRef 工具生图。参数（尺寸、seed 等）按工具定义传参。
```

---

### 2. `## User Input Tools` 整节（SKILL.md 第14-22行，约8行）

描述了跨运行时用户输入工具、纯文本 fallback、batching 规则等。

**删除原因：** TeleAgent 运行时已有内置用户提问能力，支持多问题批量、自定义选项，工具说明足够清晰，无需额外指导。

---

### 3. `references/codex-imagegen.md` 整个文件（65行）

Codex CLI 的 imagegen wrapper 调用规范（含 invocation contract、stdout schema、batch semantics）。

**删除原因：** TeleAgent 不是 Codex 运行时，该文件内容完全无效。SKILL.md 中所有引用该文件的段落也一并删除。

---

### 4. `## Reference Images` 中 CLI 参数相关表述（SKILL.md 第52-53行）

```markdown
**Intake**: Accept via `--ref <files...>` or when the user provides file paths / pastes images in conversation.
```

**删除原因：** `--ref <files...>` 是外部生图后端的 CLI 参数，TeleAgent 使用 `ImageGenWithRef` 的参考图参数，用法不同。

---

### 5. Step 6 中 codex-imagegen 的引用（SKILL.md 第301行）

```markdown
- **`codex-imagegen` invocation**: when the rule resolves to `codex-imagegen`, see references/codex-imagegen.md...
```

**删除原因：** 同上，该分支在 TeleAgent 中永远不会触发。

---

### 6. `## Changing Preferences` 中 backend 相关行（SKILL.md 第329-332行）

```markdown
- `preferred_image_backend: codex-imagegen` — pin to Codex's built-in.
- `preferred_image_backend: external-image-gen` — pin to an external image generation skill.
```

**删除原因：** TeleAgent 只有内置 ImageGen，不存在 Codex 或外部生图后端选择。

---

### 7. `preferences-schema.md` 中 backend 相关字段说明（约15行）

包括 `preferred_image_backend` 字段定义、backend id 列举表（codex-imagegen、external-image-gen、image_generate）、resolution logic 说明。

**删除原因：** 无多后端选择需求，该字段及其说明全部冗余。

---

### 8. `first-time-setup.md` 中关于 image backend 的段落（第149行）

```markdown
`preferred_image_backend: auto` is the baked-in default — first-time setup never asks about it. The `## Image Generation Tools` rule...
```

**删除原因：** 依赖已删除的 Image Generation Tools 规则。

---

## 二、可大幅精简的内容

### 1. `## Reference Images`（SKILL.md 第48-77行，30行 → 约8行）

**保留：** 用户可提供参考图、三种用法（direct/style/palette）的核心概念。

**删除：**
- `--ref <files...>` CLI 入口说明
- 外部生图后端的 `--ref` 具体参数用法
- frontmatter 记录格式（过于细节）

**精简为：**

```markdown
## Reference Images

用户可提供参考图引导风格/配色/构图。三种用法：

| Usage | Effect |
|-------|--------|
| `direct` | 传给 ImageGenWithRef 作为参考图 |
| `style` | 提取风格特征写入 prompt |
| `palette` | 提取色值写入 prompt |
```

---

### 2. `first-time-setup.md`（153行 → 约60行）

**删除：**
- Question 5（Save Location）：TeleAgent 写到固定位置即可，无需让用户选
- EXTEND.md 完整 YAML 模板：preferences-schema 已有，无需重复
- 过度装饰的流程图和 BLOCKING OPERATION 警告

**精简：** 将问题列表从结构化 YAML 缩为紧凑的列表格式，去除重复说明。

---

### 3. Step 4 确认流程中的 Image Backend 问题（SKILL.md 第277行）

```markdown
| 4 | **Image Backend** | Only if step 3 of the `## Image Generation Tools` rule needs to ask... | Available backends |
```

**删除原因：** TeleAgent 只有内置生图后端，不需要问用户选哪个。Step 4 从 4 个问题缩减为 3 个。

---

### 4. `## Confirmation Policy`（SKILL.md 第79-87行，9行 → 约4行）

**精简为：**

```markdown
## Confirmation Policy

默认生成前必须确认（布局×风格、宽高比、语言）。以下措辞可跳过确认：`--no-confirm`、"直接生成"、"不用确认"。
```

---

### 5. Backup 命名规则（出现3处：Step 1.2 第235行、Step 5 第281行、Step 6 第298-299行）

`source-backup-YYYYMMDD-HHMMSS.md` 这类重命名规则重复出现。

**建议：** 提取为一条通用规则放在文件头部，或根据实际需求直接删除（TeleAgent 的工作目录管理已由系统处理）。

---

## 三、建议保留的内容

以下内容在 TeleAgent 运行时中**真正有用**，不动：

| 内容 | 保留原因 |
|------|---------|
| Layout Gallery (21) | 布局选择依据，核心数据 |
| Style Gallery (22) | 风格选择依据，核心数据 |
| Recommended Combinations | 布局×风格推荐表，核心决策逻辑 |
| Keyword Shortcuts | 关键词→布局映射，触发逻辑 |
| Step 1-7 主流程骨架 | 工作流步骤，核心逻辑 |
| Core Principles | 数据保真、结构化设计原则 |
| `references/layouts/*.md` | 实际布局定义（按需加载） |
| `references/styles/*.md` | 实际风格定义（按需加载） |
| `references/base-prompt.md` | prompt 模板，核心产出 |
| `references/analysis-framework.md` | 分析框架，Step 1 依赖 |
| `references/structured-content-template.md` | 内容结构模板，Step 2 依赖 |
| "Never substitute SVG/HTML/canvas for raster image" 禁令 | 防止 LLM 用代码画图替代位图 |
| "Never repair rendered text by painting over bitmap" 禁令 | 防止 LLM 用代码修补位图文字 |

---

## 四、量化总结

| 类别 | 当前行数 | 精简后估算 | 节省 |
|------|---------|-----------|------|
| SKILL.md 主文件 | ~333 行 | ~180 行 | **~46%** |
| references/codex-imagegen.md | 65 行 | 0 行（删除） | **100%** |
| references/config/*.md | ~280 行 | ~120 行 | **~57%** |
| **总计** | **~678 行** | **~300 行** | **~56%** |

最大收益来源：删除 Image Generation Tools + codex-imagegen 约 90 行，User Input Tools 约 8 行，backend 相关配置约 40 行，合计约 **138 行对 TeleAgent 无效的上下文**。

> AI生成
