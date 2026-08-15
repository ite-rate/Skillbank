---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '9beb8964-3665-4919-82c8-e278cedd699f'
  PropagateID: '9beb8964-3665-4919-82c8-e278cedd699f'
  ReservedCode1: '2b45eab9-ce03-4b7d-ab58-8ed77b05e8ae'
  ReservedCode2: '2b45eab9-ce03-4b7d-ab58-8ed77b05e8ae'
---

# AI 新闻搜索源与关键词

## 搜索关键词组

按优先级排列，每次执行覆盖全部6组（5组中文 + 1组英文）：

1. **核心组**: `人工智能 AI 最新新闻 {{TODAY_DATE}}`
   - `search_recency_filter: "week"`
   - 嵌入当天日期提高精度
2. **大模型组**: `大模型 LLM GPT Claude 最新进展`
   - `search_recency_filter: "month"`
3. **产业组**: `AI 产业 融资 收购 发布`
   - `search_recency_filter: "month"`
4. **应用组**: `AI 应用 落地 场景 产品`
   - `search_recency_filter: "month"`
5. **开源组**: `AI 开源 模型 框架 GitHub`
   - `search_recency_filter: "month"`
6. **英文组**: `AI artificial intelligence latest news breakthrough {{TODAY_DATE}}`
   - `search_recency_filter: "week"`
   - 覆盖海外AI动态，避免遗漏重大国际新闻

## 用户偏好适配

- 如用户指定领域偏好（如"重点看大模型"），对应组额外追加1次细化搜索
- 如用户指定时间范围（如"最近3天"），核心组和英文组改用 `search_recency_filter: "month"`，其他组不变
- 未指定时默认取当天热点

## 降级策略

| 搜索结果条数 | 处理方式 |
|-------------|---------|
| 8-12条 | 正常输出 |
| 5-7条 | 核心组和英文组改用 `search_recency_filter: "month"`，追加1次补充搜索 |
| 3-4条 | 追加泛搜索 `AI 科技 新闻 {{TODAY_DATE}}`，`search_recency_filter: "month"` |
| <3条 | 在网页中显示"今日AI领域信息较少"提示，用已有数据生成简版日报 |

## 去重策略（两层）

1. **URL去重**：相同URL只保留一条
2. **标题相似度去重**：同一事件多篇报道时，优先保留：
   - 来源权威度更高的（官方公告 > 权威媒体 > 科技博客 > 社交媒体）
   - 内容更详尽的
   - 时效更新的
   - 中英文同事件报道，优先保留中文（用户主要使用中文）

## 热门事件追搜

- 判定条件：某条新闻被3组以上关键词同时命中
- 追搜动作：对该事件追加1次深度搜索，关键词为 `{事件核心词} 背景 分析 影响`
- 输出：在摘要末尾补充"【深度背景】"段落（50字内概括行业背景和影响分析）
- 在卡片上标记"热点追踪"标签

## 重要性分级标准

- **头条**（Top 1-2）：符合以下任一条件
  - 大厂/头部企业正式发布新产品或重大更新
  - 行业重大政策/法规出台
  - 具有广泛产业影响的融资/收购/合作
  - 重要开源项目发布
  - 被标记为"热点追踪"的事件
- **次条**（3-12）：其他精选有价值新闻

## 分类标签（9类）

从以下类别中选择最匹配的一个：
- 大模型 / 芯片算力 / 产业应用 / 政策法规 / 开源生态 / 学术研究
- AI安全与伦理 / 机器人与具身智能 / AI+科研

## 时效性标签

对每条新闻，根据搜索结果的时间信息推断并标注：
- "刚刚" / "1小时前" / "3小时前" / "今天上午" / "昨天" / "近日"
- 如无法推断具体时间，标注"近日"

## 交叉验证

对头条级新闻（Top 1-2）：
1. 用第2组关键词单独搜索
2. 对比两源信息一致性
3. 如有矛盾，在摘要中标注"⚠ 该信息经交叉验证存在不同说法，请以官方公告为准"

## 内容提取与改写

每条新闻需提取：
- 标题（精炼15字内）
- 分类标签（从9类中选）
- 重要性级别（头条/次条）
- 时效性标签
- 是否热点追踪
- 摘要（100-150字，突出关键信息和影响）
- 来源链接
- 来源名称

## AI一周趋势回顾

### 搜索策略

- 关键词：`AI 本周趋势 回顾 总结 {{TODAY_DATE}}`
- `search_recency_filter: "week"`
- 从搜索结果中提炼3-5条本周核心趋势

### 提炼规则

- 每条趋势10-20字，简洁有力
- 使用趋势箭头：↑上升方向 / ↓下降方向 / →稳定
- 示例："↑ 国产大模型集体降价"、"→ AI Agent持续火热"、"↑ 具身智能融资加速"

### HTML格式

```html
<div class="trends-list">
  <div class="trend-item"><span class="trend-arrow up">↑</span>趋势内容</div>
  ...
</div>
```

## 大模型排行榜搜索策略

### 搜索关键词

1. `Chatbot Arena 大模型排名 ELO 最新 {{TODAY_DATE}}`
   - `search_recency_filter: "week"`
   - 搜索 Arena 综合榜（国际）Top 10
2. `SuperCLUE 大模型排名 中文 最新`
   - `search_recency_filter: "month"`
   - 搜索 SuperCLUE 中文榜 Top 10

### 数据提取

**Arena 综合榜**（国际，基于LMSYS Chatbot Arena ELO评分）：
- 排名（1-10）
- 模型名称
- ELO分数（四舍五入整数）
- 趋势（↑上升N位 / ↓下降N位 / →不变）
- 开源/闭源属性
- 数据日期

**SuperCLUE 中文榜**：
- 排名（1-10）
- 模型名称
- 分数
- 趋势
- 开源/闭源属性
- 数据日期

### 开源/闭源标识

常见模型分类参考：
- **闭源**：GPT系列、Claude系列、Gemini系列、Kimi系列、通义千问商业版、文心一言
- **开源**：Llama系列、Qwen开源版、DeepSeek、Mistral、GLM开源版、Phi
- 如无法确定，默认标注闭源

### 数据来源优先级

1. Chatbot Arena 官方网站数据（lmsys.org）
2. 知乎/科技媒体转载的榜单截图或表格
3. CSDN/博客园等整理的榜单文章
4. 如搜索失败，基于最近可获取数据补全，标注"数据截至YYYY-MM-DD"

### 表格HTML格式

每个榜单生成如下结构：
```html
<table class="rank-table">
  <thead><tr><th>#</th><th>模型</th><th>分数</th><th>趋势</th></tr></thead>
  <tbody>
    <tr><td class="rank-num gold">1</td><td>模型名 <span class="model-tag closed">闭源</span></td><td class="rank-score">1387</td><td class="trend-up">↑2</td></tr>
    <tr><td class="rank-num">2</td><td>Llama 4 <span class="model-tag open">开源</span></td><td class="rank-score">1362</td><td class="trend-same">→</td></tr>
    ...
  </tbody>
</table>
<div class="rank-date">数据截至：YYYY-MM-DD</div>
```

### 趋势标记规则

- `trend-up`：绿色，↑N 表示排名上升N位
- `trend-down`：红色，↓N 表示排名下降N位
- `trend-same`：灰色，→ 表示排名不变
- 新上榜：`trend-new` 蓝色，NEW 标记

## 输出格式

见 `assets/news-template.html`，替换占位符：
- `{{DATE}}` → 日期字符串，如 "2026年7月22日"
- `{{SUMMARY_LIST}}` → 4-5条要点 `<li>` 标签
- `{{WEEKLY_TRENDS}}` → 一周趋势回顾 HTML
- `{{HEADLINE_CARDS}}` → 头条新闻卡片 HTML 块
- `{{NEWS_CARDS}}` → 次条新闻卡片 HTML 块
- `{{CATEGORY_FILTERS}}` → 分类筛选按钮 HTML
- `{{ARENA_TABLE}}` → Arena综合榜排名表格 HTML
- `{{SUPERCLUE_TABLE}}` → SuperCLUE中文榜排名表格 HTML
- `{{TIPS}}` → 每日AI知识点卡片 HTML
- `{{STATS}}` → 底部统计信息

## 每日AI知识点题库

⚠ v2.6变更：知识点题库已统一维护在 `references/tips-pool.md`，此处不再重复。

**读取路径**：`references/tips-pool.md`

**题库规模**：热门概念池 25 个 + 进阶概念池 18 个，共 43 个知识点，按日期取模轮换选取。

**选取规则**：详见 `tips-pool.md` 中的"选取规则"章节。

**领域标签**：每个知识点标注了领域标签（NLP/Agent/训练/架构/多模态/推理/安全/部署/基础设施/基础/评测），用于与当天新闻分类精准联动匹配。

> AI生成