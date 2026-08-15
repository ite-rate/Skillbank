# 2026-06-01 agent briefing sourcing notes

Reusable sourcing lessons from the 2026-06-01 scheduled Chinese agent briefing.

## Fresh agent-case seeding

HN Algolia broad searches around `AI agent`, `coding agent`, `MCP agent`, `Claude Code`, `Codex agent`, `workflow agent`, and `AGENTS.md` produced low-score but timely practice-oriented items. For this briefing style, low HN scores can still be usable when the item is clearly a concrete workflow/tool and is within 24h; label the heat honestly rather than overstating it.

Examples that fit the “case/workflow” requirement:
- `Show HN: Ouijit, an open-source task and terminal manager for coding agents` — useful as a case about managing multiple coding agents through task/status UI.
- `Sandboxes and Worktrees: My Secure Agentic AI Setup` — useful as a practice case even when the underlying article is older, if it has a fresh HN discussion/re-submission signal.
- `Show HN: Agents, run any coding agent on your subscription not API costs` — useful as a tool/skill item for multi-agent CLI orchestration.

## GitHub Trending picks

The live Trending page exposed strong same-day agent/workflow/context candidates:
- `microsoft/markitdown` — 2,759 stars today; document-to-Markdown ingestion for LLM/agent pipelines.
- `nesquena/hermes-webui` — 320 stars today; Web UI/control plane for Hermes Agent, with very recent commits.
- `EveryInc/compound-engineering-plugin` — 243 stars today; engineering workflow skills for Claude Code/Codex/Cursor.
- `revfactory/harness` — 318 stars today; generates domain-specific Claude Code agent teams and skills.
- `supermemoryai/supermemory` — 236 stars today; memory/context layer for AI agents.

Validation pattern: open the repo page and extract the README via `document.querySelector('article.markdown-body')?.innerText.slice(0,N)`, plus inspect latest commit age from the repo file table when visible.

## Anyang district weather fallback

`tianqi.com` mobile district pages were reliable for current district-level condition, current temp, humidity, wind, and range:
- `https://m.tianqi.com/wenfengqu/` showed 文峰：阴 23~35°C, humidity 56%, 南风 2级.
- `https://m.tianqi.com/beiguanqu/` showed 北关：阴 23~35°C, humidity 54%, 南风 2级.

The pages did not expose district-level precipitation probability. `wttr.in/Anyang,Henan,China?format=j1` timed out in this run. A robust secondary fallback for precipitation probability is Open-Meteo using approximate Anyang coordinates:

```text
https://api.open-meteo.com/v1/forecast?latitude=36.10&longitude=114.35&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&hourly=precipitation_probability,temperature_2m,weather_code&timezone=Asia%2FShanghai&forecast_days=1
```

Label Open-Meteo values as “安阳市级参考” rather than district-confirmed data. On 2026-06-01 it returned daily max precipitation probability 0%, min 23.5°C, max 36.2°C.
