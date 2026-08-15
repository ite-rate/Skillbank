# 2026-06-24 Feishu Morning Briefing — 36kr Newsflash Fallback Pattern

## Session context
- Cron job running `daily-agent-briefing` skill, Format B (Feishu 群聊科技早报).
- Date: 2026-06-24.
- Goal: produce 8–12 numbered short news items and send to Feishu group chat `oc_4d28fe1641ca214746ed49c02a4ee3d8`.

## What went wrong with 9点1氪
1. 36kr site search for "9点1氪" returned result titles, but the article links were stale/404 (e.g. `https://www.36kr.com/p/4067805` returned "数据不存在或已被删除").
2. The AI section (`https://www.36kr.com/information/AI/`) gave article headlines but not the curated daily roundup.
3. HN Algolia API (`search_by_date`) returned very low-signal results (1–2 points, mostly old Show HN posts) for the 24–72h window, so it was not useful as a primary seed for Chinese tech news.

## What worked: 36kr newsflashes page
- URL: `https://www.36kr.com/newsflashes`
- Method: `browser_navigate` → `browser_console(expression="document.body.innerText")` → parse the first 15–20 news items.
- The page is public, requires no login, and updates in real time.
- Each item includes: title, timestamp (e.g. "12秒前", "2分钟前"), and a short description paragraph.
- The body text is clean enough to extract directly without needing `document.querySelector('article')`.

## Concrete news items extracted (2026-06-24)
1. 英伟达发布 BioNeMo Agent 工具包 — AI 智能体 + 生命科学协同加速科学发现。
2. Meta 推出 299 美元 "Meta Glasses" 智能眼镜新系列，比 Ray-Ban 入门款便宜 80 美元。
3. 微软威斯康星州首座数据中心全面投运，2024–2028 年预计投入 47 亿美元。
4. Alphabet 6 月 29 日纳入道琼斯指数，取代威瑞森通信。
5. Baird 预测特斯拉 Q2 交付约 39.29 万辆，认为 SpaceX 与特斯拉合并"很有可能"。
6. SpaceX 将发行 250 亿美元债券分五期，最长期限 30 年。
7. 港股上半年预计 83 家企业 IPO，募资总额有望超 2000 亿港元。
8. 美银警告纳斯达克 100 逼近泡沫水平，AI 主题仍有拓展空间。
9. 芝加哥期权交易所推出预测市场首批产品（小型标普 500 二元期权）。
10. 锂电行业景气度回升，板块今年累计涨幅超 17%。

## Key lessons
- When 9点1氪 articles are unreachable (stale links, 404, paywall, gated login), **skip them immediately** and go straight to the newsflashes page. Do not waste time trying to guess article IDs or deep-linking.
- The newsflashes page is a **first-class source** for Format B, not just a supplement. It provides real-time, continuously updated headlines with short descriptions — exactly what the group-chat format needs.
- HN Algolia is useful for cross-validating international stories, but for Chinese tech news the 36kr newsflashes page is the dominant signal.
- For cron runs, avoid `python3 -c` / heredoc / pipe patterns. Use `write_file` to create temp scripts, then `terminal('python3 /tmp/script.py')`.

## Delivery
- Used `scripts/send-feishu-group-msg.py` with `FEISHU_APP_ID` and `FEISHU_APP_SECRET` env vars.
- Message sent successfully: `message_id=om_x100b6c85fd19f0a4c1000ca60228467`.
