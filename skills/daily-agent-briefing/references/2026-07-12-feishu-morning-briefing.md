# 2026-07-12 Feishu 群聊科技早报 cron run

- **Date:** 2026-07-12 (Sunday)
- **Format:** Feishu 群聊科技早报（可转发） — "60秒读懂科技世界"
- **Target chat_id:** `oc_4d28fe1641ca214746ed49c02a4ee3d8`
- **Delivery:** final response (cron job auto-delivered)

## Sourcing path

1. 36kr site search for `9点1氪` returned the latest article on 2026-07-11 successfully; extracted full article text via `document.body.innerText.slice(0, 8000)`.
2. Cross-checked 36kr AI section (`/information/AI/`) and newsflashes page for additional items.
3. Validated international stories on HN Algolia (`search_by_date` with `numericFilters=created_at_i>1752172800`) using `--noproxy '*'` terminal curl.
4. Confirmed Apple-vs-OpenAI story on BBC article page.

## Selected items (10)

1. Apple 起诉 OpenAI 窃取商业秘密
2. OpenAI 发布 ChatGPT Work（GPT-5.6 驱动，跨应用持续执行）
3. SK 海力士 7/10 纳斯达克上市，收盘涨约 12.8%
4. 大众汽车计划最高裁员 10–12 万人
5. MiniMax 完成 160 亿港元股权融资
6. 智谱唐杰发内部信，明确 AGI 下一阶段方向
7. 蚂蚁灵波发布 LingBot-VA 2.0 具身原生世界动作模型
8. Meta 扎克伯格称算力不过剩，探索出租 AI 基础设施
9. 联合国自动驾驶全球统一技术法规（ADS GTR）正式发布
10. 三星李在镕计划 7 月底赴美会晤英伟达黄仁勋

## Format notes

- Single flat message, no section headers, no weather, no GitHub Trending.
- No Markdown pipe tables (`| A | B |`, `|---|---|`); used plain numbered list.
- Kept each item to one sentence: who + what + result/impact.

## Validation signals

- Apple/OpenAI: HN Algolia `Apple sues OpenAI` — multiple posts from 2026-07-11.
- ChatGPT Work: HN Algolia post `ChatGPT Work` pointing to openai.com/chatgpt-work/ (Cloudflare-gated, but 36kr article text provided summary).
- MiniMax: HN Algolia `MiniMax shares for Hong Kong investors as lock-ups end` (SCMP, 2026-07-07).
