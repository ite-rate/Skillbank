# 2026-05-29 Agent Briefing Sourcing Notes

Reusable sourcing patterns observed in this run:

## Fresh agent-case discovery

- HN Algolia broad `search_by_date` queries were useful for candidate seeding: `AI agent`, `coding agent`, `autonomous agent`, `MCP agent`, `agent workflow`, `Claude Code`, `Codex CLI`, `OpenAI Codex`, `agents SDK`, `agentic coding`, `Show HN agent`.
- After candidate discovery, exact-title HN Algolia searches gave cleaner heat citations. Examples:
  - `Show HN: Ktx – Open-source executable context layer for data agents` → 2026-05-28, about 50 points / 9 comments.
  - `Show HN: VAEN – Package and import portable AI coding-agent Harnesses` → 2026-05-27, about 8 points / 3 comments.
  - `Show HN: AG2B – Run the agent loop in the browser, expose your tools via WebMCP` → 2026-05-28, low points but very fresh and workflow-relevant.
- Low HN points can still be worth including when the item is a concrete agent workflow/practice and the broader day is thin; explicitly label the heat signal instead of overstating it.

## GitHub Trending extraction

- `https://github.com/trending?since=daily` plus `Array.from(document.querySelectorAll('article')).slice(0,25).map(a=>a.innerText).join('\n---\n')` cleanly produced repo name, description, and `stars today`.
- For project/tool summaries, validate the selected repo by opening the repo page and extracting README text with `document.querySelector('article.markdown-body')?.innerText.slice(0,N)`.
- Same-day acceleration examples from this run: Understand-Anything (~3,766 stars today), taste-skill (~2,235), ECC (~1,388), markitdown (~1,263), superpowers (~1,726), anthropics/skills (~791). Prefer relevance to agent/workflow/productivity over raw count.

## Weather extraction

- For Anyang district weather, mobile tianqi pages worked:
  - `https://m.tianqi.com/wenfengqu/`
  - `https://m.tianqi.com/beiguanqu/`
- `document.body.innerText.split('\n').slice(0,40)` captured update time, current temp, condition/range, AQI, humidity, and wind.
- District pages did not expose precipitation probability; supplementing with `https://wttr.in/Anyang,Henan,China?format=j1` gave city-level hourly `chanceofrain`. In the briefing, label it as city-level reference rather than district-confirmed data.
