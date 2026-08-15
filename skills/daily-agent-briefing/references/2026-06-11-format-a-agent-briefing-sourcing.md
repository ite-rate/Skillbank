# 2026-06-11 Format A sourcing notes

## What worked

- In cron/headless runs, `curl -Lsk --noproxy '*'` successfully fetched GitHub Trending and HN Algolia despite the proxy/SSL pitfall documented in the main skill.
- Use `date -v-3d +%s` in the shell, then percent-encode the HN `numericFilters` comparator as `%3E`:
  - `https://hn.algolia.com/api/v1/search_by_date?tags=story&numericFilters=created_at_i%3E$since&query=agent`
  - repeat with targeted queries like `MCP` and `AI%20workflow`.
- GitHub Trending HTML was large but parseable from saved HTML. Splitting on `<article` and extracting:
  - repo path from the `<h2><a href="/...">` block
  - description from the `col-9` paragraph
  - language from `itemprop="programmingLanguage"`
  - same-day heat from `([0-9,]+) stars today`
  produced enough signal for Format A.
- Repo README validation via GitHub REST raw README worked with:
  - `curl -Lsk --noproxy '*' 'https://api.github.com/repos/<owner>/<repo>/readme' -H 'Accept: application/vnd.github.raw'`
  - This avoided default-branch guessing and was enough to validate tools.
- Browser navigation was useful for `.dev` product pages that terminal security may flag as lookalike TLD. In this run, `https://www.cc.dev/` loaded in browser and `document.body.innerText` exposed the product claims cleanly.
- Mobile 天气网 pages worked for district weather:
  - `https://m.tianqi.com/wenfengqu/`
  - `https://m.tianqi.com/beiguanqu/`
  HTML stripping yielded current temp, condition, range, AQI, humidity, and wind. No explicit precipitation probability appeared, so output correctly said `降雨概率未获取到`.

## Useful candidate signals from this run

### Agent best-case / workflow candidates

- **Command Center** (`https://www.cc.dev/`)
  - HN exact-title validation: `Show HN: Command Center, the AI coding env for people who care about quality`
  - 2026-06-08, 65 points / 30 comments.
  - Product claims: local agentic coding environment; supports Claude Code, Codex, OpenCode; helps review large AI-generated diffs via walkthroughs, refactoring agent, feedback agents.
  - Good framing: not generic coding-agent news; it is a workflow for converting large AI diffs into readable, refactorable, production-quality changes.

- **Agent Skills / Superpowers workflow discipline**
  - GitHub Trending same-day heat:
    - `obra/superpowers`: +1,205 stars today.
    - `addyosmani/agent-skills`: +781 stars today.
  - Good framing: encode spec / plan / TDD / review / ship as mandatory agent workflows so agents do not skip quality gates.

- **/last30days as agent research context**
  - GitHub Trending: `mvanhorn/last30days-skill`, +2,561 stars today.
  - README says it searches Reddit, HN, Polymarket, GitHub immediately, and can unlock X, YouTube, TikTok; scores by social/market engagement rather than SEO.
  - Good framing: gives agents recent reality/community context before meetings, product research, content planning, or strategy.

### Tools section candidates

- **Agent Skills / Superpowers** — high-quality tool/workflow class for making agents follow process discipline.
- **/last30days** — high-quality, practical research skill for recent context.
- **kctx** (`https://github.com/lucasepe/kctx`)
  - HN exact-title validation: `Show HN: Kctx – A read-only Kubernetes context engine for SREs and AI Agents`
  - 2026-06-10, 5 points / 0 comments.
  - README framing: read-only Kubernetes context engine that normalizes entities, relations, signals, graphs, and deterministic namespace snapshots; avoids speculative root-cause claims and resource mutation.
  - Good tool-section framing: useful for AI SRE / MCP / incident review because it feeds agents compact factual Kubernetes context before reasoning.

### Lower-heat / watchlist candidates

- **Foyer** (`https://github.com/get-foyer/foyer`)
  - HN exact-title validation: `Show HN: Learn while you wait for your agents to code`
  - 2026-06-10, 5 points / 0 comments.
  - README framing: hooks into Claude Code/Codex sessions and turns 3–5 minute waits into in-context focus/research panels.
  - Interesting but low heat; mention only as optional/watchlist unless more signals appear.

- **holster-scan** (`https://github.com/nauta-ai/holster-scan`)
  - HN candidate: 2 points / 0 comments.
  - README framing: local-first scanner for hallucinated/typosquatted packages and agent boundary preflight.
  - Practical, but same-day heat was weak; avoid over-weighting unless future signals strengthen.

## Output lesson

For this user’s Format A cron briefing, the `可供智能体/个人工作流使用的 tools / skills` section should be treated as a quality-filtered recommendation section, not filler. It is acceptable to include fewer than 3 and explicitly say `高质量候选不足，只保留 N 个` when source-backed tools are weak. When 3 are included, each should say: what it is, what workflow problem it solves, where it fits, and how an agent/person would actually use it.
