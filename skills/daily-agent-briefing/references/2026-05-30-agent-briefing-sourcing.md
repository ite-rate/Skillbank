# 2026-05-30 Agent Briefing sourcing notes

Session-specific details worth reusing for future Chinese daily agent briefings.

## Candidate discovery pattern that worked

- Start with GitHub Trending daily and extract article blocks via browser JS:
  - `Array.from(document.querySelectorAll('article')).slice(0,25).map(a=>a.innerText).join('\n---ARTICLE---\n')`
  - This cleanly surfaced same-day heat signals such as `stars today`.
- Use HN Algolia `search_by_date` with several overlapping agent terms to seed fresh practice/case candidates:
  - `agentic coding`, `AI agent`, `Claude Code`, `Codex`, `MCP`, `workflow agent`, `autonomous agent`, `agents`.
  - Then exact-title validate any item whose heat signal is quoted.
- For agent best cases, low HN point counts can still be usable if the source is within 24h and the practice is concrete. Label the signal honestly as low discussion rather than overstating heat.

## Useful 2026-05-30 sources/items

### Agent practice/case examples

- `My "blocked-by-default" approach to working with coding agents`
  - URL: `https://oscarswanros.com/2026/05/29/risk-management-lessons-from-cave-diving-applied-to-working-with-coding-agents/`
  - HN: 2026-05-29, about 2 points / 0 comments at retrieval.
  - Angle: default-deny permissions, red/yellow/green autonomy charter, hooks against dangerous agent behavior.
- `Teaching tmux to babysit my Claude Code agents`
  - URL: `https://blog.angeloff.name/post/2026/05/29/teaching-tmux-to-babysit-my-claude-code-agents/`
  - HN: 2026-05-29, about 2 points / 0 comments.
  - Angle: tmux status bar as lightweight multi-agent operations panel.
- `Show HN: Sverklo – repo memory for coding agents`
  - URL: `https://sverklo.com/`
  - HN: 2026-05-29, about 3 points / 0 comments.
  - Angle: local-first MCP repo memory, caller graph, diff-aware review, git-pinned decisions, 0 code upload.

### Trending projects/tools used

- `EveryInc/compound-engineering-plugin`
  - GitHub Trending: 354 stars today.
  - Latest commit visible as yesterday.
  - README angle: engineering loop of brainstorm → plan → work → review → compound learning.
- `run-llama/liteparse`
  - GitHub Trending: 680 stars today.
  - Latest commit visible as yesterday, including Rust/WASM docs update.
  - README angle: local PDF/document parser, OCR, screenshots, JSON/Text output, agent skill install path.
- `microsoft/markitdown`
  - GitHub Trending: 1,876 stars today.
  - Latest release/version bump visible within 3 days.
  - README angle: converts office docs, PDF, images, audio, HTML, ZIP, YouTube, etc. to Markdown for LLM pipelines.

### Skills/tools surfaced

- `cursor/plugins`
  - GitHub Trending: 129 stars today.
  - README lists continual-learning, cursor-team-kit, thermos, cli-for-agent, pr-review-canvas, docs-canvas, cursor-sdk, orchestrate.
- `Leonxlnx/taste-skill`
  - GitHub Trending: 2,066 stars today.
  - README angle: anti-slop frontend framework for AI agents; portable skills for layout, typography, motion, spacing, image reference boards.
- MCP runtime/tool-call security
  - HN exact-title result: `MCP Is Dead`, 2026-05-29, about 38 points / 24 comments.
  - Related low-signal but relevant item: `MCP: defending the runtime layer of agent security`, 2026-05-29.
  - Angle: MCP/tool-call layer needs guardrails, audit, least privilege, and prompt-injection defense.

## Weather extraction details

- `https://m.tianqi.com/wenfengqu/` browser snapshot was usable even though a later `document.body.innerText` call returned empty after parallel navigation.
  - Snapshot fields: 文峰, update 06:15, 空气质量良 52, 湿度 89%, 西南风 2级, life index: 穿衣 很热, 紫外线 中等, 过敏 极易发.
- `https://m.tianqi.com/beiguanqu/` snapshot fields: 北关, update 06:34, 空气质量良 62, 湿度 69%, 西南风 2级, life index: 穿衣 很热, 紫外线 中等, 过敏 极易发.
- `wttr.in` was used only to supplement precipitation/temperature range and should be labeled city-level reference when district pages lack explicit precipitation percentage.
  - `Wenfeng,Anyang,Henan,China` returned nearest area `Anyang`, sunny, 21–36°C, max hourly chance of rain 0%.
  - `Beiguan,Anyang,Henan,China` returned nearest area `Honghetun`, sunny, 21–36°C, max hourly chance of rain 0%.

## Output quality lesson

When live heat is thin, keep the briefing useful by:

1. Selecting concrete operational practices over generic AI news.
2. Quoting heat signals honestly, including low HN points/comments.
3. Marking weather precipitation as city-level reference when district pages do not expose a percentage.
4. Avoiding claims like “刷屏” unless the evidence actually supports broad discussion.
