# 2026-06-20 Feishu 群聊科技早报溯源实录

## 任务
按 daily-agent-briefing skill 的「Feishu 群聊科技早报（可转发）」格式，生成并发送中文科技早报。

## 36kr 9点1氪提取教训

- 36kr 站内搜索 `9点1氪` 可以返回文章列表，但点击文章进入详情页后，`document.querySelector('article')` 返回 **null**。
- 文章内容实际上仍在 `document.body.innerText` 中，使用 `document.body.innerText.slice(0, 8000)` 可以完整提取到：
  - 今日热点导览
  - TOP3大新闻
  - AI最前沿
  - 大公司/大事件
  - 上市进行时 / 投融资 / 酷产品
- **Action item**: 在 skill 的 Feishu 早报格式和溯源流程中，将 `document.body.innerText` 作为 `document.querySelector('article')` 的 fallback 明确写入。

## 提取到的 2026-06-13 9点1氪内容摘要

- SpaceX 6月12日纳斯达克上市，市值2.1万亿美元，马斯克身家约1.05万亿美元。
- 胖东来回应降薪谣言：从未有任何降薪决定。
- FIFA联名款labubu世界杯销量暴涨30倍。
- OpenAI遭起诉：加拿大母亲称ChatGPT设计缺陷致女儿自杀。
- SK海力士CEO考虑引入ChatGPT等外部AI服务，本月发生第二起火灾。
- 谷歌追加5000万美元培训美国技工，满足AI基础设施建设需求。
- Kimi与国有银行合作推出全球首张AI原生信用卡。
- 腾讯云下调MiniMax-M3与Hy-MT2-Pro模型价格。
- 阿里拟15亿美元竞购朴朴超市。
- 韩美半导体投资500亿韩元于SpaceX。
- 滴滴出行App 8.0上线，更名为「滴滴」，新增AI语音打车等功能。
- 恒生港美科技指数将纳入SpaceX。
- 众擎机器人据悉将向港交所提交IPO申请。
- 长鑫科技IPO审核状态变更为注册生效。
- AI机器人企业Theker获8500万美元融资。
- 晶核能源发布全球首款专为机器人场景定制的高性能固态电池。

## HN Algolia 交叉验证

- `SpaceX IPO` 相关：HN 上 `search_by_date` 返回 30p/16c 的 "The average SpaceX buyer post-IPO is almost under water after two-day slide"（2026-06-19）。
- `OpenAI ChatGPT suicide` 相关：HN 上 2-3p/0c 的加拿大母亲起诉 OpenAI 报道（2026-06-11 至 06-14）。
- `Kimi credit card`：HN 上未找到对应热度，主要热度在国内 36kr。
- `Claude Design`：HN 上无直接对应，36kr 有相关文章但非今日热点。
- `Google AI training workers`：HN 上无直接对应，36kr 有报道。

## 最终输出

采用 10 条编号短新闻，覆盖 SpaceX、OpenAI、Kimi、谷歌、滴滴、SK海力士、阿里云、阿里、韩美半导体、Theker 等热点。

## 格式合规检查

- ✅ 第1行：`YYYY年M月D日 星期X，农历X月X日，工作顺利！`
- ✅ 第2行：`在这里，60秒读懂科技世界！`
- ✅ 编号短新闻 1. 2. ... 10.
- ✅ 无分栏、无小标题、无案例分析、无工具清单、无天气、无 GitHub Trending 专区、无 HN 引用
- ✅ 语气自然、信息密度高
- ✅ 未编造，不确定的已跳过
