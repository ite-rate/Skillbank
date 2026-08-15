# Agora — 人生全场景多领域审议技能集

**6 个审议室 · 31 位思想家 · 1 个智能路由器 · 黑格尔正反合结构**

Agora 是一个基于 Claude Code 构建的多 Agent 审议系统，覆盖工程、商业、人生抉择、关系、心理韧性、创造性突破六大领域。输入你的问题，AI 自动组建专家面板，通过结构化辩证得出深度结论。

> 名字取自古希腊城邦广场（Agora）——市民把一切问题带到那里：技术、商业、政治、爱情、意义。

## 亮点

- **智能路由** — `/agora` 一个入口，自动分析问题并导向正确的审议室
- **31 位思想家** — 波普尔、康德、尼采、萨特、荣格、庄子……跨越东西方哲学、心理学、经济学
- **黑格尔正反合** — 不只是投票，而是 Thesis → Antithesis → Synthesis 的辩证升华
- **两次交互** — 审议中确认理解、决定深度，全程可引导
- **自包含** — 无需安装其他技能，开箱即用

## 快速开始

**前置条件**：已安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)。

```bash
# 安装（推荐）
npx skills add https://github.com/geekjourneyx/agora

# 或手动安装
git clone https://github.com/geekjourneyx/agora.git ~/.claude/skills/agora
```

```text
# 智能路由（推荐）
/agora 要不要辞职去创业？

# 直接进入审议室
/forge 我们的 monorepo 架构是否还合理？
/oracle 我 38 岁了，觉得一直在过别人的生活
/hearth 我和伴侣每周都为同一件事吵架
/bazaar 竞争对手突然降价 30%，我们怎么应对？
/clinic 我已经三个月没有动力工作了
/atelier 我有写作目标但每次都卡壳

# 查看所有房间
/agora --list
```

## 6 个审议室

| 审议室 | 命令 | 领域 | 典型问题 |
|--------|------|------|---------|
| 锻造坊 | `/forge` | 工程与架构 | "该用什么架构？" "这段代码为什么有问题？" |
| 集市 | `/bazaar` | 商业与战略 | "怎么定价？" "要不要进入这个市场？" |
| 神谕所 | `/oracle` | 人生十字路口 | "要不要辞职？" "我的人生方向是什么？" |
| 火炉边 | `/hearth` | 关系与家庭 | "怎么跟孩子沟通？" "这段感情值得继续吗？" |
| 诊疗室 | `/clinic` | 心理韧性 | "怎么对抗拖延？" "我怎么从倦怠中恢复？" |
| 工作坊 | `/atelier` | 创造性突破 | "我为什么写不出东西？" "怎么建立创作流程？" |

## 使用模式

| 模式 | 命令 | 说明 |
|------|------|------|
| **Full**（默认） | `/forge "问题"` | 8 步完整审议，两次交互，黑格尔正反合 |
| **Quick** | `/forge --quick "问题"` | 2 轮快速模式，无交互，适合快速决策 |
| **Duo** | `/forge --duo "张力"` | 双人辩证，3 轮，探索核心张力 |
| **Triad** | `/forge --triad architecture "问题"` | 预定义三人组，精准匹配问题域 |
| **Full Panel** | `/oracle --full "问题"` | 调用全部成员（6-7 位） |

## 13 位 Agora 专属思想家

| 思想家 | 核心方法论 | 隶属审议室 |
|--------|-----------|-----------|
| 卡尔·波普尔 | 证伪主义 / 红队 | forge |
| 伊曼努尔·康德 | 绝对律令 / 可普遍化 | hearth, forge |
| 奥卡姆的威廉 | 奥卡姆剃刀 / 复杂度审计 | forge, atelier |
| 弗里德里希·尼采 | 创造性破坏 / 价值重估 | forge, oracle, atelier |
| 让-保罗·萨特 | 存在自由 / 激进责任 | oracle |
| 卡尔·荣格 | 阴影整合 / 个体化 | oracle, clinic |
| 埃里希·弗洛姆 | 爱的艺术 / 生产性取向 | hearth |
| 阿尔弗雷德·阿德勒 | 课题分离 / 共同体感觉 | hearth |
| 维克多·弗兰克尔 | 意义疗法 / 态度自由 | clinic, oracle |
| B.F.斯金纳 | 行为主义 / 环境设计 | clinic |
| 约瑟夫·熊彼特 | 创造性毁灭 / 企业家精神 | bazaar |
| 庄子 | 逍遥游 / 齐物论 | hearth, clinic |
| 路德维希·维特根斯坦 | 语言游戏 / 概念分解 | forge, atelier |

另有 18 位来自 Council 的思想家（费曼、图灵、老子、孙子、塔勒布等），已内置，无需额外安装。

## 审议协议

8 步结构化流程，升级自 Council 的 7 步协议：

```
STEP 0  解析模式 + 组建面板
STEP 1  证据收集（按 Room 定制）
STEP 2  问题重述 + ★交互确认
STEP 3  第一轮 — 独立分析（并行、盲审）
STEP 4  自适应深度门控 + ★交互决策
STEP 5  第二轮 — 黑格尔交叉审查（按需）
STEP 6  协调者综合
STEP 7  Room 裁决
```

核心机制：Round 2 中每位 agent 必须提出 **Synthesis**（不能只选边站），Coordinator 识别 Thesis（多数派）→ Antithesis（最强少数派）→ Synthesis（更高整合）。

## 与 Council 的关系

Agora 是 [Council of High Intelligence](https://github.com/0xNyk/council-of-high-intelligence) 的扩展，不是替代。Agora 内置了全部 18 个 council-* agent，无需单独安装 Council。两者可以共存，各有侧重。

## 卸载

```bash
npx skills remove agora          # npx 安装的
rm -rf ~/.claude/skills/agora    # git clone 安装的
```

## 致谢

Agora 的核心 Council agents（18 位）和审议协议基础源自 [Council of High Intelligence](https://github.com/0xNyk/council-of-high-intelligence)，感谢原作者的开创性工作。

## License

[MIT](LICENSE)
