---
name: ai-news-digest
description: Search and curate the latest AI-related news from the internet within the past day, generate a visually appealing responsive HTML webpage with categorized news cards and summaries. Trigger when user asks for "AI新闻", "AI日报", "AI热点", "人工智能新闻", "AI news digest", "today's AI news", or similar requests about recent AI news highlights. Also trigger for "AI资讯速递", "AI快报".
level: manual
native_agent: Hermes
description_zh: v2.6版本：7轮14次并发搜索（新一步优化）、全模块降级策略+灾难兜底、知识点题库43个去重统一维护。含大模型实时排行榜（Top5默认+展开按钮）、每日鸡汤、AI产业动态（融资+人才合并）、AI政策+运营商动态（v2.6合并搜索）、AI工具推荐、AI会议日历、AI市场行情（算力+概念股合并），今日要点+本周趋势合并卡片，一键导出长图PNG，回到顶部按钮，手机电脑都能看，暗色模式适配
name_zh: AI新闻速递
---

# AI 新闻速递（v2.6）

从互联网搜索最近一天内AI相关热点新闻，生成纯文字卡片的响应式HTML网页。支持用户指定关注领域，自动分级头条/次条，暗色模式适配，热门事件深度追踪，附大模型实时排行榜（Top5默认+展开按钮）、每日鸡汤（主内容区header下方渐变卡片）、AI产业动态（融资速览+人才动态合并）、AI政策+运营商动态（v2.6合并搜索）、AI工具推荐、AI会议日历、AI市场行情（算力价格+概念股行情合并）和今日要点+本周趋势合并渐变卡片。v2.6新增：全模块降级策略+灾难兜底，知识点题库统一维护扩充至43个。支持一键导出长图PNG，回到顶部浮动按钮，方便微信分享。

## 工作流

### 步骤0：解析用户偏好（可选）

1. 检查用户输入是否包含领域偏好（如"重点关注大模型""只要产业应用相关的"）
2. 如有偏好 → 提升对应关键词组的搜索优先级，增加该组搜索深度
3. 如无偏好 → 按6组关键词均衡执行（5组中文 + 1组英文）
4. 检查用户是否指定时间范围（如"最近3天""昨天到今天"），默认取当天

### 步骤1：搜索新闻

1. 读取 `references/news-sources.md` 获取搜索关键词组
2. 执行6组关键词搜索，使用 `online_search`：
    - 核心组：`search_recency_filter: "week"`，关键词嵌入当天日期
    - 其余4组中文：`search_recency_filter: "month"`
    - 英文组：`search_recency_filter: "week"`
3. 如用户指定了领域偏好，对应组额外追加1次细化搜索
4. 合并结果，进行两层去重：
    - **URL去重**：相同URL只保留一条
    - **标题相似度去重**：同一事件多篇报道，只保留权威度最高、内容最详尽的一篇
5. 按相关度 × 时效性加权排序，选8-12条最值得关注的新闻
6. **重要性分级**：
    - 头条（Top 1-2）：当天最具影响力的AI新闻
    - 次条（3-12）：其他精选新闻
7. **热门事件追搜**：如某条新闻被3组以上关键词同时命中，标记为"热点追踪"，追加1次深度搜索获取更多背景信息，在摘要中补充"深度背景"段落
8. **降级策略**：
    - 正常：选8-12条
    - 结果5-7条：放宽时间过滤，核心组和英文组改用 `search_recency_filter: "month"`，补充搜索
    - 结果3-4条：放宽关键词，追加泛搜索 `AI 科技 新闻 {{TODAY_DATE}}`
    - 结果<3条：在网页中显示"今日AI领域信息较少"提示，并用已有数据生成简版日报
    - **灾难兜底**（v2.6新增）：如全部6组搜索均失败（0条结果），仅用每日知识点题库 + 当天日期生成最简版日报，页面顶部标注"⚠ 今日数据获取异常，仅展示AI知识点"，新闻/排行榜/侧边栏模块均显示降级占位提示

### ⚡ 搜索轮次优化（v2.6）：14次搜索 / 7轮并发

搜索是生成耗时的主瓶颈（每轮5-8秒），v2.6在v2.5基础上进一步优化，将搜索从15次/8轮缩减为14次/7轮：

| 优化项 | v2.5方案 | v2.6优化后 | 省量 |
|---|---|---|---|
| 政策+运营商 | 各1次分开搜索 | 合并1次搜索 | -1次 |
| R8空位消除 | R8仅1-2次搜索含空位 | 全部填满7轮，无空位 | -1轮 |

**v2.5→v2.6 对比**：

| 指标 | v2.5 | v2.6 |
|---|---|---|
| 搜索次数 | 15次 | 14次 |
| 搜索轮次 | 8轮 | 7轮 |
| 预计耗时 | ~55s | ~48s |

**优化后7轮并发排布**：

| 轮次 | 并发搜索1 | 并发搜索2 | 搜索数 |
|---|---|---|---|
| R1 | 新闻组1 | 新闻组2 | 2 |
| R2 | 新闻组3 | 新闻组4 | 2 |
| R3 | 新闻组5 | 新闻组6 | 2 |
| R4 | Arena排行榜 | SuperCLUE排行榜 | 2 |
| R5 | 每日鸡汤 | 产业动态(合并) | 2 |
| R6 | 政策+运营商(合并) | 市场行情(合并) | 2 |
| R7 | AI工具推荐 | AI会议日历 | 2 |

⚠ 排行榜保持2次分开搜索，确保数据完整性。政策+运营商、产业动态、市场行情的合并搜索如数据不完整，可追加1次补全。热点追搜从步骤1的新闻命中判定后自动追加，不占用上述7轮排位。

### 步骤2：搜索大模型排名

1. 使用 `online_search` 搜索最新大模型排名，关键词：
   - `Chatbot Arena 大模型排名 ELO 最新 {{TODAY_DATE}}`
   - `SuperCLUE 大模型排名 中文 最新`
2. 提取两个榜单的 Top 10 数据：
   - **Arena 综合榜**（国际）：排名、模型名、ELO分数、趋势、开源/闭源
   - **SuperCLUE 中文榜**：排名、模型名、分数、趋势、开源/闭源
3. 标注每个模型的**开源/闭源**属性：`[开源]` 或 `[闭源]`
4. 如搜索失败或数据不完整，基于搜索到的信息补全，缺失部分标注"-"
5. **数据时效性校验**：提取到的排名数据日期如距当天超过7天，在表格下方标注"⚠ 数据可能非最新，最后更新于YYYY-MM-DD"
6. **降级策略**：
   - 某一榜搜搜索失败 → 展示已获取的另一榜单，失败榜单显示"数据获取失败，请稍后重试"占位
   - 两榜均失败 → 使用最近已知排名数据填充，标注"⚠ 排行榜数据为备份缓存，非实时获取"
   - 两榜均失败且无缓存 → 侧边栏排行榜区域显示"今日排行榜数据不可用"提示卡片
7. 将排名数据格式化为 `{{ARENA_TABLE}}` 和 `{{SUPERCLUE_TABLE}}` 占位符的HTML

### 步骤3：AI一周趋势回顾（v2.5优化：从新闻结果提炼，不再单独搜索）

1. ⚠ 不再单独使用 `online_search` 搜索趋势，改为从步骤1的6组新闻搜索结果中直接提炼
2. 基于已收集的新闻，提炼3-5条本周核心趋势（每条10-20字），如"国产大模型集体降价"、"AI Agent成为新焦点"等
3. 如新闻结果不足以提炼趋势，可追加1次搜索：`AI 本周趋势 回顾 总结 {{TODAY_DATE}}`
4. 格式化为 `{{WEEKLY_TRENDS}}` 占位符HTML（嵌入要点+趋势合并卡片内）

### 步骤3.5：每日AI知识点 ⚠ 必须执行，不可跳过

1. ⚠ v2.6变更：知识点题库统一维护在 `references/tips-pool.md`（原news-sources.md中的知识点部分已迁移）
2. 读取 `references/tips-pool.md` 获取知识点题库（热门池25个 + 进阶池18个，共43个）
3. 选取1-2个知识点：
    - 第1个：从热门概念池按日期对25取模轮换选取
    - 第2个：优先选取与当天新闻分类对应的领域标签知识点（知识点的``[标签: xxx]``与新闻分类匹配）
4. 为每个知识点撰写：
    - 标题（保留题库原文）
    - 通俗解释（3-5句，非技术人员也能看懂）
    - 实用场景（1个与日常工作/生活相关的应用场景）
5. 按步骤5第7点的知识点HTML结构，生成完整的 `{{TIPS}}` 占位符HTML代码
6. ⚠ **绝对不能留空 `{{TIPS}}` 占位符**，即使搜索异常也必须从题库中选取并生成完整HTML

### 步骤3.7：每日鸡汤

1. 使用 `online_search` 搜索人民日报新闻早班车的每日一句，关键词：`人民日报 新闻早班车 每日一句 {{TODAY_DATE}}`
2. 从搜索摘要中提取每日金句（通常是一句励志/哲理短句，10-30字）
3. 如搜索失败或未找到当日内容，使用备用关键词：`人民日报 早班车 金句 今天`，或基于常见励志金句生成一条
4. **降级策略**：
   - 搜索无结果 → 生成一条通用励志金句（如"种一棵树最好的时间是十年前，其次是现在。"），标注来源为"AI生成"
   - **不可留空 `{{DAILY_QUOTE}}`**
5. 格式化为 `{{DAILY_QUOTE}}` 占位符HTML
6. ⚠ v2.5变更：鸡汤从侧边栏移至主内容区header下方，使用渐变色背景的 `main-quote` 样式

### 步骤3.8：AI产业动态（融资速览+人才动态合并）

1. ⚠ v2.5优化：融资和人才合并为1次搜索，关键词：`AI 融资投资 人才招聘薪资 最新 {{TODAY_DATE}}`
2. 从搜索结果中分别提取融资事件和人才动态数据
3. **融资速览**：提取3-5条融资事件，每条包含：公司名、融资金额、融资轮次、时间，按金额从大到小排序
4. **人才动态**：提取2-3条人才市场关键数据/趋势，每条包含：要点标题、标签（如行业趋势/薪资/缺口）、补充说明
5. 如合并搜索结果不完整（融资或人才任一方数据不足），可追加1次针对性搜索补全
6. **降级策略**：
   - 融资数据不足3条 → 展示已获取的条数，不足部分不补凑
   - 人才数据不足2条 → 展示已获取的条数，补充"AI人才市场整体保持高需求"通用提示
   - 合并搜索完全失败 → 产业动态卡片显示"今日产业动态数据获取失败"占位，不隐藏卡片框架
7. 格式化为 `{{AI_INDUSTRY}}` 占位符HTML，使用合并卡片结构（共享一个header，内分两个section）

### 步骤3.9：AI政策速递（v2.6优化：与运营商动态合并搜索）

1. ⚠ v2.6优化：政策速递与运营商动态合并为1次搜索，关键词：`AI 政策 法规 标准 备案 运营商 中国电信 中国移动 中国联通 {{TODAY_DATE}}`
2. 从搜索结果中分别提取政策动态和运营商动态数据
3. **AI政策速递**：提取3-4条近期政策动态，每条包含：政策标题、发布机构（标签形式）、发布时间
4. 如合并搜索结果不完整（政策或运营商任一方数据不足），可追加1次针对性搜索补全
5. 降级策略：
   - 搜索结果不足3条 → 放宽时间过滤为 `search_recency_filter: "month"` 追加1次
   - 仍无结果 → 显示"今日暂无重要政策动态"占位提示，不显示空卡片
6. 格式化为 `{{AI_POLICY}}` 占位符HTML

### 步骤3.10：运营商AI动态（v2.6优化：与政策速递合并搜索）

1. ⚠ v2.6优化：运营商动态与政策速递共用1次搜索（见步骤3.9），从同一搜索结果中提取运营商数据
2. 为每家运营商提取1条最新AI动态，包含：运营商名称、动态描述
3. 使用区分运营商的标签颜色：中国电信（蓝色）、中国移动（绿色）、中国联通（橙色）
4. 降级策略：
   - 某运营商无当日动态 → 提取近7天内最近1条补充
   - 仍无数据 → 对应运营商显示"暂无最新动态"占位，其他运营商正常显示
5. 格式化为 `{{CARRIER_NEWS}}` 占位符HTML

### 步骤3.11：AI工具推荐

1. 使用 `online_search` 搜索近期实用AI工具推荐，关键词：`AI工具 推荐 实用 {{TODAY_DATE}}`
2. 选取1个实用AI工具，包含：工具名称、功能描述（2-3句）、实用场景、了解更多链接
3. **降级策略**（v2.6新增）：
   - 搜索无结果 → 从以下常用AI工具中轮换推荐1个：Kimi、通义千问、智谱清言、文心一言、豆包、Gamma（PPT生成）、通义万相（AI画图）、即梦（视频生成），补充功能描述和场景
   - 搜索结果仅有工具名无描述 → 补充通用描述后输出
4. 格式化为 `{{AI_TOOL}}` 占位符HTML

### 步骤3.12：AI会议日历

1. 使用 `online_search` 搜索近期AI行业会议/峰会/活动，关键词：`AI 峰会 论坛 大会 活动 {{TODAY_DATE}}`
2. 提取2-4条近期AI会议活动，每条包含：会议名称、日期、状态标签（即将开幕/进行中/已结束）
3. **降级策略**（v2.6新增）：
   - 搜索不足2条 → 放宽时间过滤为 `search_recency_filter: "month"` 追加1次
   - 仍无结果 → 显示"近期暂无大型AI会议活动"占位提示，不显示空卡片
4. 格式化为 `{{AI_EVENT}}` 占位符HTML

### 步骤3.13：AI市场行情（算力价格+概念股行情合并）

1. ⚠ v2.5优化：算力和概念股合并为1次搜索，关键词：`AI算力 GPU租赁价格 概念股行情 涨跌 {{TODAY_DATE}}`
2. 从搜索结果中分别提取算力价格和概念股行情数据
3. **算力价格**：提取3-4款主流GPU的租赁价格数据，每条包含：芯片型号、价格、涨跌趋势，补充市场供需分析备注
4. **概念股行情**：提取板块指数数据：中证AI主题指数（930713）当日收盘涨跌幅
5. 提取5-7只AI龙头股当日涨跌幅，优先选取：中际旭创、寒武纪、澜起科技、海光信息、中科曙光、新易盛等，每只含股票简称、细分领域标签、涨跌幅
6. 补充北向资金/主力流向关键数据作为备注，A股红涨绿跌配色
7. 如合并搜索结果不完整（算力或概念股任一方数据不足），可追加1次针对性搜索补全
8. **降级策略**（v2.6新增）：
   - 算力数据缺失 → 算力section显示"今日算力价格数据暂未获取"占位，概念股行情正常展示
   - 概念股数据缺失 → 概念股section显示"今日为非交易日或数据获取失败"占位，算力价格正常展示
   - 合并搜索完全失败 → 市场行情卡片显示"今日市场行情数据不可用"占位，不隐藏卡片框架
   - ⚠ 所有行情数据均附加"数据仅供参考，不构成投资建议"提示
9. 格式化为 `{{AI_MARKET}}` 占位符HTML，使用合并卡片结构（共享一个header，内分算力价格和概念股行情两个section）

### 步骤4：提炼内容

对每条入选新闻：
- 精炼标题（15字以内）
- 选择分类标签，从以下9类中选：
  - 大模型 / 芯片算力 / 产业应用 / 政策法规 / 开源生态 / 学术研究
  - AI安全与伦理 / 机器人与具身智能 / AI+科研
- 改写摘要（100-150字，突出关键信息和影响）
- 标注时效性标签（如"2小时前""今天上午""昨日"等，基于搜索结果的时间戳推断）
- 保留原始来源链接
- **头条级新闻交叉验证**：对Top 1-2条头条，用第2组关键词单独搜索确认，如有事实矛盾则在摘要中标注"⚠ 待确认"

### 步骤5：组装网页

1. 读取 `assets/news-template.html` 模板
2. 替换占位符：
    - `{{DATE}}` → 当天日期，格式"YYYY年M月D日"
    - `{{SUMMARY_LIST}}` → 4-5条要点 `<li>` 标签
    - `{{WEEKLY_TRENDS}}` → 一周趋势回顾HTML（v2.5: 嵌入要点+趋势合并卡片内）
    - `{{DAILY_QUOTE}}` → 每日鸡汤（v2.5: 移至主内容区header下方，渐变色main-quote样式）
    - `{{HEADLINE_CARDS}}` → 头条新闻卡片
    - `{{NEWS_CARDS}}` → 次条新闻卡片
    - `{{CATEGORY_FILTERS}}` → 分类筛选按钮HTML
    - `{{ARENA_TABLE}}` → Arena综合榜排名表格HTML（v2.5: 6-10名加 `rank-hidden` 类默认隐藏）
    - `{{SUPERCLUE_TABLE}}` → SuperCLUE中文榜排名表格HTML（v2.5: 6-10名加 `rank-hidden` 类默认隐藏）
    - `{{TIPS}}` → ⚠ **必须生成**，每日AI知识点卡片HTML，不可留空
    - `{{AI_INDUSTRY}}` → AI产业动态卡片HTML（v2.5: 融资速览+人才动态合并）
    - `{{AI_POLICY}}` → AI政策速递卡片HTML
    - `{{CARRIER_NEWS}}` → 运营商AI动态卡片HTML
    - `{{AI_TOOL}}` → AI工具推荐卡片HTML
    - `{{AI_EVENT}}` → AI会议日历卡片HTML
    - `{{AI_MARKET}}` → AI市场行情卡片HTML（v2.5: 算力价格+概念股行情合并）
    - `{{STATS}}` → 底部统计（"本日共X条 · 覆盖X个领域 · 数据更新于HH:MM"）
3. 头条卡片结构（纯文字，左侧分类色条）：
```html
<div class="news-card headline-card" data-category="{分类}">
  <div class="card-color-bar" data-category="{分类}"></div>
  <div class="content">
    <div class="meta">
      <span class="tag headline-tag">头条</span>
      <span class="tag hot-tag">热点追踪</span>  <!-- 仅热点追踪事件添加此标签 -->
      <span class="tag">{分类}</span>
      <span class="time-tag">{时效标签}</span>
      <span>{来源}</span>
    </div>
    <h3>{标题}</h3>
    <p>{摘要}</p>
    <p class="deep-background">【深度背景】{深度背景内容}</p>  <!-- 仅热点追踪事件添加此段 -->
    <div class="actions">
      <a class="source-link" href="{链接}" target="_blank">阅读原文 →</a>
      <button class="copy-btn" onclick="copyLink('{链接}')">复制链接</button>
    </div>
  </div>
</div>
```
4. 次条卡片结构（纯文字，左侧分类色条）：
```html
<div class="news-card" data-category="{分类}">
  <div class="card-color-bar" data-category="{分类}"></div>
  <div class="content">
    <div class="meta">
      <span class="tag hot-tag">热点追踪</span>  <!-- 仅热点追踪事件添加此标签 -->
      <span class="tag">{分类}</span>
      <span class="time-tag">{时效标签}</span>
      <span>{来源}</span>
    </div>
    <h3>{标题}</h3>
    <p>{摘要}</p>
    <p class="deep-background">【深度背景】{深度背景内容}</p>  <!-- 仅热点追踪事件添加此段 -->
    <div class="actions">
      <a class="source-link" href="{链接}" target="_blank">阅读原文 →</a>
      <button class="copy-btn" onclick="copyLink('{链接}')">复制链接</button>
    </div>
  </div>
</div>
```
5. 排名表格结构（v2.5: 6-10名默认隐藏，需加 `rank-hidden` 类）
```html
<table class="rank-table">
  <thead><tr><th>#</th><th>模型</th><th>分数</th><th>趋势</th></tr></thead>
  <tbody>
    <tr><td class="rank-num gold">1</td><td>GPT-5.6 Sol <span class="model-tag closed">闭源</span></td><td class="rank-score">1387</td><td class="trend-up">↑2</td></tr>
    <tr><td class="rank-num">2</td><td>Llama 4 <span class="model-tag open">开源</span></td><td class="rank-score">1362</td><td class="trend-same">→</td></tr>
    ...
    <!-- v2.5: 6-10名加 rank-hidden 类，默认隐藏，通过"展开更多"按钮显示 -->
    <tr class="rank-hidden"><td class="rank-num">6</td><td>DeepSeek R1 <span class="model-tag open">开源</span></td><td class="rank-score">1325</td><td class="trend-down">↓1</td></tr>
    ...
  </tbody>
</table>
```
6. 一周趋势结构（v2.5: 嵌入要点+趋势合并卡片内，无需独立trends-box）：
```html
<div class="trends-list">
  <div class="trend-item"><span class="trend-arrow up">↑</span>趋势内容</div>
  ...
</div>
```
7. 每日知识点结构
```html
<div class="tips-card">
  <div class="tips-header">每日AI知识</div>
  <div class="tip-item">
    <div class="tip-title">{知识点标题}</div>
    <div class="tip-desc">{3-5句通俗解释}</div>
    <div class="tip-scenario">实用场景：{1个实际应用场景}</div>
  </div>
  ...
</div>
```
8. 每日鸡汤结构（v2.5: 移至主内容区header下方，渐变色背景）
```html
<div class="main-quote">
  <div class="quote-icon">📖</div>
  <div class="quote-divider"></div>
  <div class="quote-text">{每日金句内容}</div>
  <div class="quote-source">人民日报 · 新闻早班车 · {M月D日}</div>
</div>
```
9. AI产业动态结构（v2.5: 融资速览+人才动态合并为一个卡片）
```html
<div class="industry-card">
  <div class="industry-header">🏢 AI产业动态</div>
  <div class="industry-section">
    <div class="industry-section-title">💰 融资速览</div>
    <div class="finance-item">
      <div class="finance-company">{公司名}</div>
      <div class="finance-detail"><span class="finance-amount">{金额}</span><span class="finance-round">{轮次}</span><span class="finance-time">{时间}</span></div>
    </div>
    ...
  </div>
  <div class="industry-section">
    <div class="industry-section-title">💼 人才动态</div>
    <div class="talent-item">
      <div class="talent-title">{要点标题}</div>
      <div class="talent-meta"><span class="talent-tag">{标签}</span><span>{补充说明}</span></div>
    </div>
    ...
  </div>
</div>
```
10. AI政策速递结构（位于侧边栏，紫色主题）
```html
<div class="policy-card">
  <div class="policy-header">✅ AI政策速递</div>
  <div class="policy-item">
    <div class="policy-title">{政策标题}</div>
    <div class="policy-meta"><span class="policy-tag">{发布机构}</span><span>{时间}</span></div>
  </div>
  ...
</div>
```
11. 运营商AI动态结构（位于侧边栏，绿色主题）
```html
<div class="carrier-card">
  <div class="carrier-header">📡 运营商AI动态</div>
  <div class="carrier-item">
    <div class="carrier-name"><span class="carrier-tag-telecom|carrier-tag-mobile|carrier-tag-unicom">{运营商}</span></div>
    <div class="carrier-desc">{动态描述}</div>
  </div>
  ...
</div>
```
12. AI工具推荐结构（位于侧边栏，青色主题）
```html
<div class="tool-card">
  <div class="tool-header">🔧 今日AI工具推荐</div>
  <div class="tool-body">
    <div class="tool-name">{工具名称}</div>
    <div class="tool-desc">{功能描述}</div>
    <div class="tool-scenario">实用场景：{应用场景}</div>
    <a class="tool-link" href="{链接}" target="_blank">了解更多 →</a>
  </div>
</div>
```
13. AI人才动态（v2.5: 已合并到AI产业动态卡片中，不再独立存在）
14. AI会议日历结构（位于侧边栏，棕色主题）
```html
<div class="event-card">
  <div class="event-header">📅 AI会议日历</div>
  <div class="event-item">
    <div class="event-name">{会议名称}</div>
    <div class="event-meta"><span class="event-date">{日期}</span><span class="event-tag-upcoming|event-tag-ongoing|event-tag-ended">{状态}</span><span>{地点}</span></div>
  </div>
  ...
</div>
```
15. 算力价格走势（v2.5: 已合并到AI市场行情卡片中，不再独立存在）

16. AI概念股行情（v2.5: 已合并到AI市场行情卡片中，不再独立存在）

17. AI市场行情结构（v2.5: 算力价格+概念股行情合并为一个卡片）
```html
<div class="market-card">
  <div class="market-header">📈 AI市场行情</div>
  <div class="market-section">
    <div class="market-section-title">⚡ 算力价格</div>
    <div class="chip-item">
      <div class="chip-name">{芯片型号}</div>
      <div class="chip-detail"><span class="chip-price">{价格}</span><span class="chip-trend-up|chip-trend-flat">{涨跌趋势}</span></div>
    </div>
    ...
    <div class="chip-note">{市场供需备注}</div>
  </div>
  <div class="market-section">
    <div class="market-section-title">📊 概念股行情</div>
    <div class="stock-index">
      <span class="stock-index-name">中证AI主题指数 (930713)</span>
      <span><span class="stock-index-value">{指数点位}</span> <span class="stock-index-change stock-up|stock-down">{涨跌幅}</span></span>
    </div>
    <div class="stock-item">
      <div class="stock-name">{股票简称} <span class="stock-tag">{细分领域}</span></div>
      <span class="stock-change stock-up|stock-down|stock-flat">{涨跌幅}</span>
    </div>
    ...
    <div class="stock-note">{北向资金/主力流向备注}</div>
  </div>
</div>
```
17. 将最终HTML写入 `.temp/` 目录
9. 将 `.temp/` 中的文件复制到工作目录根作为最终交付

### 步骤6：交付

- 输出文件名：`AI日报-YYYY-MM-DD.html`（从 `.temp/` 复制到工作目录根）
- 交付给用户，告知：
  - 可直接在浏览器打开，手机和电脑均适配
  - 支持暗色模式（手动切换 + 跟随系统）
  - 可按分类标签筛选新闻
  - 点击"复制链接"可快速分享单条新闻
  - 右侧排行榜可切换Arena/SuperCLUE双榜单，默认显示Top5，点击"展开更多"查看6-10名
  - 含今日要点+本周趋势合并渐变卡片
  - 含每日鸡汤，位于header下方，渐变色开场金句
  - 含每日AI知识点，每天学一点
  - 含AI产业动态（融资速览+人才动态合并）
  - 含AI政策速递，国内外AI法规/标准/备案动态
  - 含运营商AI动态，电信/移动/联通竞品情报
  - 含AI工具推荐，每日1个实用AI工具
  - 含AI会议日历，近期AI峰会/论坛/活动预告
  - 含AI市场行情（算力价格+概念股行情合并），A股红涨绿跌配色
  - **一键导出长图PNG**：点击右上角"导出长图"按钮，自动截取主内容区生成长图并下载，可直接发送到微信分享
    - 导出时自动展开被筛选隐藏的新闻卡片，确保内容完整
    - 导出时自动添加底部水印（日期+来源标注）
    - 导出时自动隐藏侧边栏和操作按钮，保持长图简洁
    - 长图文件名格式：AI日报-YYYY-MM-DD.png
    - 导出过程中显示加载遮罩，完成后自动下载并提示
  - **回到顶部按钮**：滚动页面后右下角出现回到顶部按钮，一键平滑回顶

## 跨技能协作

- 与 **中标大将军** 联动：如日报中出现招标/政企类AI新闻，在卡片底部提示"可使用 @中标大将军 进一步分析招标信息"
- 与 **定时任务** 联动：建议用户设置每日定时任务自动生成AI日报
- 与 **deep-research** 联动：如用户对某条新闻感兴趣想深入调研，可引导使用深度研究技能

## 自检 Checklist

**⚠ 组装完成后必须逐项核对，发现遗漏立即补全再交付。**

### 搜索与新闻
- [ ] 搜索覆盖至少6组关键词（含英文组）
- [ ] 去重后新闻条数在8-12条之间（如偏少已按降级策略处理）
- [ ] 头条1-2条，其余为次条
- [ ] 每条新闻标题≤15字
- [ ] 每条摘要100-150字
- [ ] 分类标签从9类中选择
- [ ] 头条新闻已完成交叉验证
- [ ] 热门事件已标记"热点追踪"并补充背景
- [ ] 每条新闻有时效性标签

### 侧边栏模块（v2.6全模块降级策略检查）
- [ ] 大模型排名数据已从在线搜索获取；如搜索失败已启用降级策略（缓存/占位提示）
- [ ] Arena榜单Top10数据完整，含开源/闭源标识，6-10名加了 `rank-hidden` 类
- [ ] SuperCLUE榜单Top10数据完整，含开源/闭源标识，6-10名加了 `rank-hidden` 类
- [ ] 排行榜数据时效性已校验（如距当天超7天已标注"⚠ 数据可能非最新"）
- [ ] 每日鸡汤已搜索并生成（`{{DAILY_QUOTE}}`），位于主内容区header下方，使用 `main-quote` 渐变色样式
- [ ] AI产业动态已生成（`{{AI_INDUSTRY}}`），融资速览3-5条+人才动态2-3条，合并为一个卡片；如失败已启用降级
- [ ] AI政策速递已生成（`{{AI_POLICY}}`），3-4条政策动态；如失败已显示占位提示
- [ ] 运营商AI动态已生成（`{{CARRIER_NEWS}}`），三家运营商各1条（v2.6与政策合并搜索）；如某家无数据已显示占位
- [ ] AI工具推荐已生成（`{{AI_TOOL}}`），1个实用工具含名称/描述/场景/链接；如失败已从备用列表轮换推荐
- [ ] AI会议日历已生成（`{{AI_EVENT}}`），2-4条近期会议活动；如失败已显示占位提示
- [ ] AI市场行情已生成（`{{AI_MARKET}}`），算力价格3-4款+概念股5-7只龙头股涨跌；如失败已显示占位提示；已附加"数据仅供参考"提示

### 知识点与趋势
- [ ] ⚠ 每日AI知识点1-2条已生成（`{{TIPS}}` 绝不可留空），内容通俗准确；从 `tips-pool.md` 读取，当前题库43个
- [ ] 知识点已使用领域标签与当天新闻分类联动匹配
- [ ] 今日要点+本周趋势已合并为 `summary-trends-box` 渐变色卡片
- [ ] 一周趋势回顾已从新闻结果提炼3-5条（v2.5优化：不再单独搜索）

### 前端功能
- [ ] 分类筛选按钮功能正常
- [ ] 排行榜双榜单切换功能正常
- [ ] 排行榜展开/折叠按钮功能正常（默认Top5，点击展开6-10名）
- [ ] 暗色模式手动切换功能正常
- [ ] HTML在浏览器中可正常打开，移动端适配正常
- [ ] 暗色模式下显示正常
- [ ] 长图导出功能正常（点击"导出长图"按钮可生成PNG并下载）
- [ ] 回到顶部浮动按钮功能正常（滚动超过400px显示，点击平滑滚动回顶部）
- [ ] 打印样式正常（侧边栏隐藏，单栏输出）

### v2.6 新增检查项
- [ ] 所有侧边栏模块搜索失败时均有降级占位提示，无空白卡片
- [ ] 灾难兜底路径已确认：全部搜索失败时生成最简版日报（仅知识点+日期）
- [ ] 搜索轮次为7轮（v2.6优化），无R8空位浪费
