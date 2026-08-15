# Skillbank 阶段性文档 — canonical 清理结果

> 2026-08-15
> 清理前 166 个 skill → 44 活跃 + 21 归档 + 99 删除 + 2 额外删

---

## 一、清理过程

1. 全量 import 7 Agent skill 进 canonical(166 个)
2. Superpowers 15 族按最新源 mtime 合并成 1 主名(删 29 冗余变体)
3. 删 6 个 Codex 没用过的学术 skill
4. 用户人工校验 `docs/canonical-skill-list.md` 标记: 删 99 / 归档 16 / ? 13 / 留 38
5. 13 个 ? 逐一分析后处置: 3 删(测试fixture) + 5 归档(superpowers方法论) + 4 留 + 1 待定
6. 追加删 media-generation + writing-skills(用户最终决定)
7. backup 兜底: `temp/skill-backup/` 独立仓完整备份 7 Agent 真身

---

## 二、44 个活跃 skill — 留什么 + 为什么留

### 思维/讨论(12 个) — 你的核心使用场景

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `agora` | —(共享) | 讨论生态路由器, 6 房间入口, 你高频用 |
| `brainstorming` | —(共享) | 创意工作前的必用头脑风暴, 你高频用 |
| `grill-me` | —(共享) | 无情拷问磨利计划, 你用它审方案 |
| `grill-me-tele` | TeleAgent | TeleAgent 端 grill-me, 你在 TeleAgent 里用 |
| `chatroom-austrian` | ClaudeCode | 哈耶克×米塞斯奥派对话, 你的特色场景 |
| `humanizer-hermes` | Hermes | 文本去 AI 味, 你高频用(08-07 有记录) |
| `yao-meta-skill` | ClaudeCode | 从工作流/提示词创建评估 skill, 你的 meta 工具 |
| `atelier` | ZCode | 工作坊房间 — 创意突破讨论 |
| `bazaar` | ZCode | 集市房间 — 商业与战略讨论 |
| `clinic` | ZCode | 诊疗室房间 — 心理韧性讨论 |
| `forge` | ZCode | 锻造坊房间 — 工程与架构讨论 |
| `oracle` | ZCode | 神谕所房间 — 人生十字路口讨论 |

**留的理由**: agora 房间簇 + brainstorm + grill 是你日常讨论/决策的核心工具链, 高频使用且不可替代。

### 文档生成(12 个) — office 套件各家变体

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `docx-tele` | TeleAgent | TeleAgent 版 Word, 你在 TeleAgent 里用 |
| `pdf-qwen` | QwenWorkCN | QwenWorkCN 版 PDF, 你高频用(08-13 有记录) |
| `pdf-tele` | TeleAgent | TeleAgent 版 PDF(视觉精修版), 中文场景好 |
| `powerpoint` | Hermes | Hermes 版 PPT, 你高频用(08-12, 7 次) |
| `pptx-tele` | TeleAgent | TeleAgent 版中文 PPT(汇报/提案/课件) |
| `print` | TeleAgent | 通用文档打印(PDF/Word/Excel/PPT→真打印机) |
| `xlsx` | QwenWorkCN | QwenWorkCN 版 Excel |
| `xlsx-tele` | TeleAgent | TeleAgent 版电子表格 |
| `data-report` | QwenWorkCN | 从 Excel/CSV 生成 HTML 数据分析报告, 中文办公场景 |
| `paddleocr-doc-parsing` | TeleAgent | 复杂版式 PDF 的 OCR 兜底, PDF skill 搞不定时用 |
| `doc-coauthoring` | TeleAgent | 结构化文档协作撰写 |
| `plugin-creator-qwen` | QwenWorkCN | QwenWorkCN 插件创建/定制 |

**留的理由**: office 套件各家版本 body 不同功能互补 — QwenWorkCN 中文优化、TeleAgent 视觉精修、Hermes 模板丰富。你按场景选不同变体, 不删是保留选择性。删了 Hermes/PDF 通用版和 QwenWorkCN 自带版(docx/pdf/pptx)因为跟保留的变体重叠且更弱。

### 研究/调研(3 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `ai-coding-agent-research` | Hermes | 评估对比 AI coding agent, 你的研究领域(4 次使用) |
| `autoresearchclaw-run-and-monitor` | Hermes | 自动研究流程跑监控, 你的研究工具链 |
| `deep-research` | TeleAgent | 中文深度研究/调研/行业分析, 你的中文场景 |

**留的理由**: 你在用且没有替代品。删了 job-market/live-job-market/llm-model-release 因为职业/模型追踪不是你当前焦点。

### 开发工程(4 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `writing-plans` | —(共享) | 你高频写 plan, 这是写多步骤实施计划的核心 skill |
| `systematic-debugging-hermes` | Hermes | 4 阶段根因调试, Hermes 最新 patched 版 |
| `receiving-code-review-hermes` | Hermes | 收到 review 反馈后的处理流程 |
| `requesting-code-review-hermes` | Hermes | 提交前 review: 安全扫描/质量门/自动修 |

**留的理由**: writing-plans 是你高频核心; Hermes 版 code-review 是 patched 扩充版(mtime 最新); systematic-debugging 是调试方法论。归档了 dispatching/executing/finishing/git-worktrees/subagent 因为 superpowers 流水线你当前没走。

### 发布/编排(1 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `release-orchestrator` | ZCode | 软件发布编排, 你工程流程要用 |

### 办公/集成(7 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `bilibili-summary` | QwenWorkCN | B 站视频总结, 你的中文内容消费场景 |
| `scheduler` | TeleAgent | 定时任务管理(cron+一次性), 你日常要用 |
| `memory-manager` | TeleAgent | 长期记忆管理, 你的持久化需求 |
| `find-skills` | QwenWorkCN | QwenWorkCN 查找可用 skill 的入口 |
| `qwenwork-guidance` | QwenWorkCN | QwenWork Connector 内置工具路由指南 |
| `create-skill` | QwenWorkCN | QwenWorkCN 端 skill 创建引导(格式手册), Skillbank 管同步不管创作, 不重叠 |
| `skill-creator-tele` | TeleAgent | TeleAgent 端 skill 创建指南 |

**留的理由**: 你的日常办公/集成场景在用。删了 dws/email/feishu/spotify/webhook/xitter/box/linear 等因为没在频率数据里出现且不是当前焦点。

### 情报(1 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `daily-agent-briefing` | Hermes | 中文每日简报, 你的最高频 skill(226 次使用) |

**留的理由**: 你用得最多的 skill, 绝对核心。删了 ai-news-digest/career/resume 因为职业/AI 新闻不是当前焦点。

### Agent 元工具/独立(4 个)

| skill | 原生 Agent | 为什么留 |
|---|---|---|
| `full-output-enforcement` | —(社区) | 强制 LLM 完整输出不截断, 独立 meta-skill, 实用 |
| `notebooklm` | ClaudeCode | Google NotebookLM API 编程访问 |
| `openai-docs` | Codex | OpenAI 产品/API 文档查询(Codex 内置, 删了 Codex 工具残) |
| `thoughtcode-go` | ZCode | Go 源码↔思路码(中文自然语言投影)双向转换, 你的 Go 学习场景 |

**留的理由**: full-output-enforcement 是独立社区 skill 不属任何 Agent 内置, 实用; notebooklm/openai-docs 是 API/文档查询工具你偶尔要用; thoughtcode-go 是你的 Go 学习特色工具。

---

## 三、21 个归档 skill — 归档什么 + 为什么归档

### 学术研究系列(8 个) — 你当前不走论文流水线, 将来写论文时 unarchive

| skill | 功能 | 为什么归档 |
|---|---|---|
| `paper-experiment-design` | 论文实验设计 | 学术方法论完整但你当前不写论文 |
| `paper-guardrails` | 论文写作编排层 | 同上 |
| `paper-literature-survey` | 文献综述 | 同上 |
| `paper-peer-review` | 模拟同行评审 | 同上 |
| `paper-structure-logic` | 论文结构逻辑 | 同上 |
| `pre-submission-reviewer` | 提交前五维审查 | 同上 |
| `research-kickoff` | 启动研究论文项目 | 同上 |
| `research-paper-writing` | 端到端论文写作 | 同上 |

### 商业工具箱(4 个) — dbs 系列, 你当前不用但将来可能用

| skill | 功能 | 为什么归档 |
|---|---|---|
| `dbs` | dontbesilent 商业工具箱主入口 | 方法论完整但当前没在用 |
| `dbs-action` | 执行力诊断(阿德勒心理学) | 同上 |
| `dbs-deconstruct` | 概念拆解(维特根斯坦+奥派) | 同上 |
| `dbskill-upgrade` | 升级 dbskill | 同上 |

### Superpowers 工程方法论(5 个) — 方法论完整但你当前没走这条流水线

| skill | 功能 | 为什么归档 |
|---|---|---|
| `dispatching-parallel-agents` | 2+ 独立任务分派并行 agent | 你当前手动管理, 没走自动化流水线 |
| `executing-plans` | 按实施计划执行 | 同上, 你手动执行居多 |
| `finishing-a-development-branch` | 分支完工收尾 | 同上 |
| `using-git-worktrees` | git worktree 隔离开发 | 同上 |
| `subagent-driven-development` | 子 agent 执行+两阶段审查 | 内置能派子 agent, 这个是编排方法论, 你没触发 |

### 面试/研究(3 个)

| skill | 功能 | 为什么归档 |
|---|---|---|
| `deli-autoresearch` | 长周期自主研究框架 | 你当前不走自主调研流水线 |
| `go-interview-rapid-project-design` | 面试速成 Go 项目设计 | 当前不在面试周期 |
| `code-anchored-interview-coaching` | 编程面试辅导(18 次使用) | 当前不在面试周期, 但有使用记录, 归档保留 |
| `session-mqtt-architecture-storytelling` | HTTP+MQTT 系统面试笔记 | 当前不在面试周期 |

### 其他(1 个)

| skill | 功能 | 为什么归档 |
|---|---|---|
| (以上共 21 个) | | |

---

## 四、删除汇总(101 个)

| 删除类别 | 数量 | 代表 |
|---|---|---|
| 创意/视觉全族 | 24 | canvas-design/imagegen/frontend-design/baoyu-* 等 |
| 运维/Hermes 专属 | 13 | network-proxy/maintaining-hermes/hermes-s6 等 |
| 办公/集成(没用过) | 18 | dws/email/feishu/spotify/webhook/box/linear 等 |
| Agent 元工具 | 5 | claude-code/codex/hermes-agent/lathe/qw-pages |
| 开发工程(标删) | 14 | archify/github-*/plan/skill-creator/skill-installer 等 |
| 文档(重叠弱版) | 4 | docx(Hermes)/pdf(Hermes)/pptx(QW)/scanned-pdf-ocr |
| 学术(标删) | 3 | job-market/live-job-market/llm-model-release |
| 情报/职业(标删) | 4 | ai-news/career/go-study/resume |
| 设备/生活 | 2 | minecraft/pokemon |
| 测试 fixture | 3 | broken-skill/broken-yaml-skill/invalid-governance-skill |
| QwenWorkCN 内置(没用过) | 2 | media-generation + writing-skills(用户最终决定删) |
| Superpowers 变体合并 | 29 | 15 族按最新 mtime 合并, 删冗余变体 |
| Codex 学术(之前删) | 6 | benchmark-paper/idea-evaluator/intro-drafter 等 |
| 其他 | (含 3 个合并后已不存在的变体名) | |

---

## 五、数据支撑

- Hermes `.usage.json` 113 条记录中 40 个有 use_count > 0
- 最高频: daily-agent-briefing(226 次)、obsidian-seminar(21 次, 已删)、hermes-agent(20 次, 已删)
- 保留的 44 个中: daily-agent-briefing(226 次)、writing-plans(高频)、powerpoint(7 次) 等有明确使用记录
- 归档的 21 个中: code-anchored-interview-coaching(18 次)有使用记录但当前不在面试周期
- 删除的 101 个中: 多数 use_count=0 或从未在频率数据出现

---

## 六、backup 兜底

- `temp/skill-backup/` 独立 git 仓, 完整备份 7 Agent 真身(含已删的)
- 回滚: `cp -R skill-backup/dot_hermes__skills/* ~/.hermes/skills/`
- 归档恢复: `skillbank unarchive <name>`
- Skillbank git history: 全部 commit 保留, 任何状态可 `git reset` 回去