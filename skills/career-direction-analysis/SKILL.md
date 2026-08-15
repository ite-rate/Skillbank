---
name: career-direction-analysis
description: Use when a user is exploring switching career directions.
level: manual
native_agent: Hermes
---

# Career Direction Analysis

## When to Use

- User says they want to switch directions but is vague about the target ("想转机器人测试", "不想做后端了")
- User expresses frustration with current direction's competitiveness ("卷不过")
- User asks about a specific role's market demand, salary, or entry barrier
- User asks "这个岗位需求咋样" about a role they're considering

## Core Principle

**Don't just answer the surface question.** When a user asks "ROS机器人测试岗位需求咋样", the real question is usually "我应该转这个方向吗，还是有没有更适合我的？" The analysis must:

1. Extract the user's **real differentiating assets** (not just tech stack — include projects, domain knowledge, academic background)
2. Compare candidate directions by **competitive fit**, not just market size
3. **Challenge wrong assumptions** — "门槛低" often means "天花板低" not "容易进"
4. Quantify the gap honestly: "门槛 5 分，你现在在 0 分" vs "门槛 7 分，你现在在 4 分"

## Workflow

### Phase 1: Extract Core Assets

Read the user's current resume. On macOS use `pdftotext` (Homebrew poppler) — `read_file` returns binary for PDFs. Use `search_files` with patterns like `*简历*` or `*resume*` to locate resume files.

Extract:
- **Technical stack**: languages, frameworks, databases, middleware
- **Domain experience**: what industry/product they worked on (VR, IoT, medical, etc.)
- **Project portfolio**: self-initiated vs work projects, complexity, completeness
- **Academic credentials**: degree, research area, publications
- **Communication protocols**: MQTT, WebSocket, HTTP — these are transferable signals
- **Deployment experience**: Docker, CI/CD, cloud

Group assets into:
- **Direct assets**: can be used as-is in a target role
- **Transferable assets**: need reframing but the underlying skill applies
- **Differentiators**: rare combinations that most candidates don't have

### Phase 2: Generate Candidate Directions

Based on the asset profile, generate 3-5 candidate directions. For each:
- What roles it covers
- Which of the user's assets are directly usable
- Which need reframing
- What the gap is (skills to learn)
- Estimated time to close the gap

### Phase 3: Market Reality Check

For each direction, assess:
- **Market size**: approximate job posting count in target city
- **Competition level**: how many candidates have similar or better profiles
- **Salary range**: for the user's experience level
- **Barrier to entry**: what's the minimum they need to pass interviews
- **Ceiling**: 3-5 year salary trajectory

Note: Chinese job sites (BOSS直聘, 拉勾, 51job) often block automated access with captcha/login walls. Use the `live-job-market-research` skill techniques, or rely on industry knowledge with honest caveats. Do NOT fabricate job counts.

### Phase 4: Challenge and Reframe

Present the analysis honestly. Key patterns to watch for:

**"门槛低" trap**: User thinks a direction is easier because the knowledge set is smaller. But if they're starting from zero, a smaller knowledge set they don't have is still harder than a larger knowledge set they already have 60% of.

**"逃离红海" trap**: User wants to leave a competitive field. But moving to a smaller field with fewer jobs doesn't reduce competition — it may increase it because there are fewer openings.

**"兴趣驱动" check**: Ask whether the user genuinely wants the target direction or is just trying to escape. If escaping, focus on directions where their existing assets create the most leverage.

### Phase 5: Recommend with Rationale

Rank directions by: (competitive fit × market demand × salary potential × gap-closing speed)

Present:
1. Top recommendation with specific rationale
2. Backup option
3. What to avoid and why

## Key Insight: "Find the direction where existing projects become credentials"

The best career pivot is NOT to a field with lower barriers — it's to a field where the user's existing projects and experience are directly recognized as qualifications.

Example from this session:
- User has GoModel AI Gateway (self-built, multi-model routing, SSE, Redis rate limiting, token auditing)
- ROS testing would require learning entirely new tooling from scratch
- AI Infrastructure / Model Gateway direction uses the Gateway project AS the portfolio piece
- Competition is scarce because few people combine Go engineering + AI model deployment
- Salary is 20-30% higher than pure Go backend

## Integration with Other Skills

- **resume-tailoring**: After direction is decided, use resume-tailoring to generate the actual tailored resume
- **live-job-market-research**: Use to gather actual JD data for candidate directions
- **session_search**: Use to find user's resume files and past career discussions

## Pitfalls

- **NEVER fabricate job counts or salary data.** If job sites are blocked, say "I can't get the data" and ask the user to search manually. Inflated/imagined numbers WILL be caught and destroy trust. The user's exact words: "拿不到数据不要瞎扯". This is the #1 pitfall.
- Do NOT recommend a direction just because the user asked about it — challenge the premise first
- Do NOT ignore the user's existing project portfolio — self-built projects are rare and valuable
- Do NOT assume "fewer requirements = easier to get in" — a 5-requirement JD where you know 0 is harder than a 15-requirement JD where you know 10
- ALWAYS ask about motivation: "escape" vs "genuine interest" leads to different recommendations

## Data Collection Techniques

### Reading PDF resumes on macOS
`read_file` returns binary garbage for PDFs. Use `pdftotext` (Homebrew poppler) instead:
```bash
pdftotext "/path/to/resume.pdf" -
```
Use `search_files` with patterns like `*简历*` or `*resume*` to locate resume files first.

### Job site access
Chinese job sites (BOSS直聘, 拉勾, 51job) block automated access with captcha/login walls. Options:
1. **Ask the user to search manually** — fastest, most reliable. Give them 2-3 keywords + city, they report back the counts.
2. **Chrome CDP cookie extraction** — start Chrome with `--remote-debugging-port=9222`, let user log in manually, then extract cookies via CDP `Network.getCookies` and call BOSS直聘's API directly with `requests`. See `references/boss-zhipin-cdp-cookie-extraction.md` for the full technique. Works but fragile — API rate-limits after 2-3 calls.
3. **Search engine snippets** — unreliable for job counts, only useful for discovering JD content.

Always prefer option 1 unless the user explicitly offers to help with browser access. If using option 2, space API calls 3+ seconds apart and cache results — BOSS直聘 returns empty results after a few consecutive calls.