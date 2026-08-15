# Feishu 群聊科技早报 — 输出格式与溯源笔记

用于 Feishu 群聊可直接转发的科技早报，纯编号短新闻，无分栏无标题无天气。

## 输出格式模板

```
YYYY年M月D日 星期X，农历X月X日，工作顺利！
在这里，60秒读懂科技世界！
1. 第一条新闻……
2. 第二条新闻……
……
```

## 内容规则

- 8–12 条编号短新闻，每条尽量一句话
- 格式：「某公司/某人 + 发生了什么 + 结果/进展」
- 无分栏、无小标题、无案例分析、无工具清单、无天气、无 GitHub Trending、无 HN 引用
- 语气：群聊晨报感，简洁自然，信息密度高
- 优先最近 24h，热点不够放宽到 72h
- 热点少就少写，不凑数；不确定的宁可不写
- 覆盖：科技、互联网、AI、商业、航天、硬件、汽车、创业

## 推荐溯源流程

### 第一步：打开 36kr「9点1氪」日汇总（主源）

1. 搜索 36kr 关键词「9点1氪」，按发布时间排序
2. 打开最新的 9点1氪文章
3. 用 browser_console 提取全文：
   ```
   document.querySelector('article')?.innerText?.slice(0, 6000)
   ```
4. 9点1氪已汇总当日科技/商业头三条 + AI最前沿 + 大公司/大事件，是理想种子源

### 第二步：补充 36kr 快讯

- 快讯页：`https://www.36kr.com/newsflashes`
- AI 资讯：`https://www.36kr.com/information/AI/`
- 用 `browser_console` 提取标题列表快速扫描热点

### 第三步：HN Algolia 交叉验证与补充

针对 9点1氪中提及的国际科技话题，到 HN Algolia 做精确标题搜索确认热度：
```
curl -sk --noproxy '*' --max-time 15 \
  'https://hn.algolia.com/api/v1/search?tags=story&query=<exact+title>' \
  -H 'User-Agent: Hermes/1.0' -o /tmp/hn_check.json
```

同时拉取最近 72h 高热度故事做补充（特别关注 tech/AI/startup/space 方向）：
```
curl -sk --noproxy '*' --max-time 15 \
  'https://hn.algolia.com/api/v1/search_by_date?tags=story&hitsPerPage=30&numericFilters=created_at_i%3E<72h_ago_timestamp>' \
  -H 'User-Agent: Hermes/1.0' -o /tmp/hn_recent.json
```

### 第四步：筛选与撰写

1. 从 9点1氪提取 5–7 条国内/Tech 热点
2. 从 HN 补充 3–5 条国际消息
3. 去重，按重要性和时效排序
4. 每条压缩到一句话，严格遵循「谁 + 干什么 + 结果」公式
5. 无对应热度信号的条目直接删除，不编造

## 环境注意事项（cron/headless）

- **Proxy 绕过**：`curl` 到 `hn.algolia.com` / `github.com` 必须加 `--noproxy '*'`，否则 SSL_ERROR
- **Pipe 安全拦截**：禁止 `curl | python3 -c`，改为 `curl -o /tmp/file.json` → `execute_code` 解析
- **36kr** 通常走代理直通，Browser navigate 即可
- **农历日期**：用 `zhdate` 库，`ZhDate.from_datetime(datetime.datetime(Y, M, D))`

## 2026年6月7日 示例输出

```
2026年6月7日 星期日，农历四月廿二，工作顺利！
在这里，60秒读懂科技世界！
1. 美股周五暴跌，纳指跌超4%，费城半导体指数跌10%，英伟达跌超6%、英特尔跌超11%。
2. Anthropic 呼吁全球 AI 实验室放缓研发，警告当前 AI 系统可能很快能在无人类干预下自我改进。
3. 豆包推出付费订阅后 5 月月活减少 610 万，分析认为字节跳动在 AI 领域商业化操之过急。
4. 黄仁勋确认 SK 海力士、三星、美光通过 HBM4 认证，将为英伟达 Vera Rubin 芯片量产供货。
5. 腾讯高管称今年公司大部分代码由 AI 生成，TokenHub 日 Token 消耗突破 5 万亿。
6. SpaceX 将日本 IPO 融资目标上调至 25 亿美元，日本散户认购本周五启动。
7. GitHub Copilot 宣布弃用 GPT-5.2 系列模型，开发者需迁移至新模型。
8. Cursor 宣布降价并新增企业支出管控，AI 编程工具进入价格战。
9. 丰田叫停雷克萨斯 LF-ZC 纯电轿跑量产计划，回应称系根据市场需求调整，并非放弃纯电车。
10. 苹果宣布 2025 年全球 App Store 生态销售额超 1.4 万亿美元，创历史新高。
```
