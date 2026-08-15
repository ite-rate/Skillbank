# 2026-07-16 Feishu 群聊科技早报 sourcing

## 任务
按 daily-agent-briefing skill 的「Alternate format: Feishu 群聊科技早报（可转发）」格式，向飞书群聊 `oc_4d28fe1641ca214746ed49c02a4ee3d8` 发送 7:40 中文科技早报。

## 日期
- 2026年7月16日 星期四，农历六月初二
-  Cron 环境用 `date +"%Y年%m月%d日 星期%u"` 获取公历；农历手动核对填充。

## 内容源与验证
- 主源：36kr 快讯页面 `https://www.36kr.com/newsflashes`（不需要登录，实时更新）。提取方式：
  - `browser_navigate` 加载页面后，`browser_console(document.body.innerText)` 抓取前 12000 字符即可获取当天主要快讯。
  - 页面标题、摘要、发布时间、来源均清晰列出。
- AI 深度文章补充：`https://www.36kr.com/information/AI/`，同样用 `document.body.innerText` 提取。
- HN 交叉验证：国际新闻（Meta / DeepSeek / Apple / Nvidia）用 HN Algolia `search_by_date` 验证近期热度。
  - 关键教训：`numericFilters=created_at_i>...` 中的 `>` 必须 URL 编码为 `%3E`，否则会 400。
  - 在 cron 中必须先把 Python 脚本写到 `/tmp/fetch_hn.py` 再执行，不能用 `python3 -c` 或管道。
- 当日 9点1氪 站内搜索仍未返回可用结果，直接依赖 36kr 快讯 + AI 频道是稳定路径。

## 本次选取的 12 条新闻
1. 亚马逊云科技计算与机器学习高级副总裁 Dave Brown 将离职，Dave Treadwell 8 月 1 日接掌团队。
2. 苹果被曝正寻求收购 AI 芯片公司，以加强自研服务器芯片能力。
3. 英伟达黄仁勋否认 Vera Rubin 制造延期，称下一代 AI 加速系统已量产并将按计划交付。
4. 英伟达与丰田扩大合作，推进物理 AI 在汽车、机器人和城市领域的应用。
5. Meta 遭 26 名员工起诉，指控用 AI 标记病假/产假员工并纳入裁员名单。
6. DeepSeek 被曝最快年内启动 IPO，估值瞄准约 700 亿美元。
7. 国行苹果 AI 据称已通过备案，将接入阿里通义千问。
8. 面壁智能端侧大模型将搭载三星手机上市。
9. 微软安全部门裁员数百人，新任安全负责人重组团队并加码 AI 驱动安全产品。
10. 宇树 IPO 注册获证监会同意，叠加特斯拉 Optimus 临近量产，机器人赛道 7-8 月进入催化窗口。
11. 锂电产业链上半年业绩大面积预喜，35 家公司中多数预增或扭亏。
12. 苹果上调 AppleCare+ 价格，仅影响新用户。

## 发送
- 使用 `scripts/send-feishu-group-msg.py`，传入显式 `chat_id`：`oc_4d28fe1641ca214746ed49c02a4ee3d8`。
- 成功返回 message_id：`om_x100b6ab5ffa190a4b1ff95d9a20eb57`。

## 格式注意
- 用户明确要求：不要 Markdown pipe table、不要分栏、不要小标题、不要 HN 来源标签、不要天气/GitHub Trending 专区。
- 消息为单条可转发文本，首行日期+次行口号，后续 1.-12. 编号短句。
