# 2026-06-08 Format A Agent Briefing Sourcing Notes

Session type: scheduled cron job, Chinese Format A daily agent briefing.

## What worked

- Loaded `daily-agent-briefing` and used Format A section order: agent cases → GitHub Trending → tools/skills → Anyang district weather → optional HN discussion.
- HN/GitHub network worked with terminal `curl --noproxy '*'`; browser also loaded GitHub Trending and official pages successfully in this run.
- HN candidate seeding via Algolia `search_by_date` over the last 72h with queries `agent`, `AI agent`, and `MCP` produced usable fresh agent/workflow items.
- Use a temp parser script written with `skill_manage`/file tools (not `python -c` or heredoc) to dedupe HN items and rank by `points + comments*2`.
- GitHub Trending extraction was reliable with:
  `Array.from(document.querySelectorAll('article')).slice(0,20).map(a=>({repo:a.querySelector('h2')?.innerText.trim().replace(/\s+/g,' '), desc:a.querySelector('p')?.innerText.trim(), text:a.innerText.match(/\d[\d,]* stars today/)?.[0]||''}))`
- Weather extraction for `m.tianqi.com/wenfengqu/` and `/beiguanqu/` was clean using `document.body.innerText.split('\n').slice(0,35)`.

## Concrete fresh candidates found

### HN / Show HN agent cases

- `Do agents.md files help coding agents?` — 42 points / 32 comments, useful as a high-signal discussion for AGENTS.md and repo-local agent instructions.
- `Show HN: Nightwatch, The open-source, read-only AI SRE` — 18 points / 7 comments, official repo: `github.com/ninoxAI/nightwatch`. Strong case study: read-only AI SRE that clusters alert storms, investigates root cause, and proposes human-gated fixes.
- `Show HN: Web Speed – A shared web-map registry for AI agents (MCP, open source)` — 5 points / 2 comments, official page: `getwebspeed.io`. Strong case study: deterministic web/DOM adaptation layer for agentic execution.
- `EMILIAProtocol-an open standard for human sign-off on irreversible agent actions` — 2 points / 0 comments, official spec: `emiliaprotocol.ai/spec`. Useful governance case: pre-action trust enforcement using Trust Receipt / Trust Profile / Trust Decision.

### GitHub Trending Today candidates

- `mvanhorn / last30days-skill` — AI agent skill for cross-source research and synthesis; 1,111 stars today.
- `Panniantong / Agent-Reach` — CLI giving agents read/search access across Twitter, Reddit, YouTube, GitHub, Bilibili, Xiaohongshu; 961 stars today.
- `santifer / career-ops` — Claude Code powered job-search automation with skill modes, dashboard, PDF generation, batch processing; 665 stars today.
- Other strong candidates: `google / skills` — 481 stars today; `CopilotKit / CopilotKit` — 578 stars today; `MemPalace / mempalace` — 452 stars today.

### Weather values captured

- 文峰区: `33°C`, `晴 20~33°C`, `良 53`, `湿度 27%`, `南风 3级`; no explicit precipitation probability shown.
- 北关区: `33°C`, `晴 19~34°C`, `优 48`, `湿度 28%`, `南风 3级`; no explicit precipitation probability shown.

## Pitfalls / command patterns

- Do not place `$(date -v-3d +%s)` inside single-quoted URLs; it will not expand and can make `curl` fail. Safer pattern:
  ```sh
  since=$(date -v-3d +%s)
  curl -sk --noproxy '*' --max-time 20 "https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=created_at_i%3E${since}&query=agent" -H 'User-Agent: Hermes/1.0' -o /tmp/daily_brief/hn_agent.json
  ```
- Browser snapshots on `m.tianqi.com` may omit current condition details in the compact view; `document.body.innerText.split('\n').slice(0,35)` recovered the full current temp / condition / humidity / wind block.
- When picking agent cases, a low HN score can still be acceptable if it is a concrete operational workflow with official docs and there are not three higher-signal fresh items; label the heat honestly.
