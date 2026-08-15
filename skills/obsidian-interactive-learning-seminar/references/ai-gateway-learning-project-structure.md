# AI Gateway 学习项目结构示例

基于 2026-06-06 GoModel 5 模块深度学习验证的最小项目模板。

## 目录结构

```
Projects/ai-gateway/
├── README.md        — 目标 + 学习方式 + 代码锚点路径
├── MAINLINE.md      — 模块清单（✅已完成 / 🔄进行中 / ⏳待做）
├── STATE.yaml       — 当前模块、主题、进度
├── 01-请求生命周期.md
├── 02-模型发现与user_path.md
├── 03-两层缓存.md
├── 04-Guardrail.md
└── 05-Fallback与断路器.md
```

## 文件模板

### README.md
```markdown
# <主题> 交互式学习

**目标：** 以 <代码库名> 源码为锚点，苏格拉底式深入理解 <领域>。

**学习方式：** 预测 → 解释 → 召回 → 迁移 → 闭卷压缩
**规则：** 先回答再讲解，不跳步。

**代码锚点：** <本地仓库绝对路径>
```

### MAINLINE.md
```markdown
# 主线地图

1. ✅ 模块1名称
2. ✅ 模块2名称
3. 🔄 模块3名称（进行中）
4. ⏳ 模块4名称
```

### STATE.yaml
```yaml
module: 3
topic: 模块3名称
status: in_progress
```

### 模块文件（01-请求生命周期.md 示例）
```markdown
# 模块 N：主题

**代码：** <文件路径>

## 核心概念
...

## 设计决策
...

## 关键问题与回答
...

## 学习者原始回答
...

## 纠偏
...

## 改进版 30 秒回答
...
```

## 写入技巧

**不要用 `write_file` 工具写 vault 文件**——可能显示成功但不落盘。用终端：

```bash
cat > ~/Documents/main_store/<vault-name>/Projects/<topic>/<file>.md << 'ENDOFFILE'
...content...
ENDOFFILE
```

写入后验证：`ls ~/Documents/main_store/<vault-name>/Projects/<topic>/`

**先确认用户在用哪个 vault**——用户可能有多个 Obsidian 库（学习库、设计库等），写错库用户看不到。
