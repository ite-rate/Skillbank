---
name: job-market-research
description: Use when comparing career directions or job market demand.
level: manual
native_agent: Hermes
---

# Job Market Research Skill

## Overview

Research job market data for career direction decisions: 岗位数量、薪资范围、市场需求对比。Core principle: **never fabricate market data** — if you can't access real data, say so and ask the user to help.

## When to Use

- User asks about job market demand for a specific role/方向
- User wants to compare career directions (e.g., "Go后端 vs 机器人测试 vs AI网关")
- User asks about salary ranges or hiring volume
- User wants to know if a direction is "卷" (competitive) or has low barriers

## When NOT to Use

- User just wants a resume tailored to a specific JD (use resume-tailoring instead)
- User asks about a specific company's culture (use web search)

## Core Rules

### Rule 1: Never Fabricate Market Data

**CRITICAL**: Do not invent job counts, salary ranges, or market trends. If you cannot access real hiring platform data, explicitly say "我拿不到数据" and ask the user to check directly.

User correction: "拿不到数据不要瞎扯" — fabricating data destroys trust instantly.

### Rule 2: Ask User to Verify

When platforms are inaccessible (login walls, CAPTCHAs), ask the user to search directly:
- "你在BOSS直聘APP里搜这三个关键词，告诉我每个搜出来多少个岗位"
- This takes the user 30 seconds and gives real data

### Rule 3: Prefer DOM Parsing Over Screenshots

When scraping platforms, use HTML/DOM extraction, not visual analysis. User correction: "用html解析dom不行吗 视觉太不准了"

## Technique: Scraping Job Platforms via Chrome CDP

For login-walled platforms like BOSS直聘:

1. **Launch Chrome with remote debugging** (MUST include `--remote-allow-origins=*` or WebSocket gets 403 Forbidden):
   ```
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --remote-debugging-port=9222 \
     --remote-allow-origins=* \
     --user-data-dir="/tmp/chrome-debug-profile" \
     --no-first-run --no-default-browser-check "https://www.zhipin.com"
   ```

2. **Ask user to log in** through the opened Chrome window

3. **Connect via CDP** using raw WebSocket on port 9222 (see `references/cdp-job-platform-scraping.md` for implementation)

4. **Navigate and extract** via `Runtime.evaluate` JS injection:
   - BOSS直聘 renders job lists as Canvas + dynamic JS
   - Use `document.querySelectorAll('a[href*="/job_detail/"]')` to count unique job links
   - Check `document.cookie` to verify login state before scraping
   - Generic card selectors return duplicates; use href-based deduplication

5. **Common pitfalls**:
   - BOSS直聘 job cards are Canvas-rendered — `document.body.innerText` may not contain job text
   - Unlogged state limits results to ~17 per page
   - `read_file` cannot parse PDF binary — use `pdftotext` command instead
   - Search engines (Google/Bing) often blocked by CAPTCHA or return irrelevant results for Chinese job queries

## Career Direction Analysis Framework

When comparing career directions for a user:

1. **Collect real data first** — job counts, salary ranges from platforms
2. **Assess user's existing assets** — what skills/experience transfer directly
3. **Identify the real choice** — often not "A vs B" but "which direction makes my existing experience a competitive advantage"
4. **Be honest about trade-offs** — don't sugarcoat a direction just because the user expressed interest
5. **Don't push back if user has valid concerns** — "卷不过" is a legitimate reason to explore alternatives

## Pitfalls

- **Fabricating data**: Never guess job counts or salaries. Always verify or ask user.
- **Sugarcoating**: Don't pretend a direction is better than it is. If robot testing jobs include "日薪150" and "不体检", say so.
- **Ignoring user's real constraint**: If user says "Go后端要回的知识太多了", that's a real concern, not just ignorance.
- **Using read_file on PDFs**: `read_file` returns binary garbage for PDFs. Use `pdftotext` via terminal instead.
- **Screenshot-based analysis**: Users find visual analysis of screenshots unreliable for data extraction. Always prefer DOM/HTML parsing.
- **Chrome CDP 403 Forbidden**: Chrome 111+ requires `--remote-allow-origins=*` flag for WebSocket connections. Without it, all CDP connections fail with 403.
- **boss-zhipin-scraper Python version**: The scraper uses `int | None` type syntax requiring Python 3.10+. macOS system Python may be 3.9 — use conda's 3.12 instead: `/opt/homebrew/Caskroom/miniconda/base/bin/python3.12`.
- **Multiple Chrome profiles don't share login**: If user logs in via their own Chrome (not the CDP-launched one), the CDP session won't have login cookies. User must log in within the CDP Chrome window specifically.
- **boss-zhipin-scraper tool**: For full scraping (salary, skills, pagination), install `eatmoreduck/boss-zhipin-scraper` (924 stars, GitHub) — it handles font anti-scraping and outputs明文薪资 JSON/CSV. See `references/cdp-job-platform-scraping.md` for setup details.