# 2026-06-25 — Open-ended agent workflow briefing correction

## User correction
The user corrected the personal 7:40 Feishu DM briefing prompt after an over-narrow update:

- Do **not** special-track a repository or example the user casually provides.
- Treat user-mentioned directions such as loop engineering, spec layers, skill/subagent collaboration, market feedback, `/goal`, harness/eval/loss, etc. as **reference directions**, not a fixed mandatory checklist.
- Keep the briefing more open: prioritize whatever is fresh, high-signal, and useful about AI-agent workflows.

## Skill implication
For Format A personal agent briefings:

1. Use user examples as seed examples only.
2. Do not repeatedly force the same named repo/tool into the report unless it naturally has strong current signal.
3. Keep `前沿范式雷达` broad: agent workflow, context/memory, collaboration, eval/validation, user feedback, browser/runtime, design/product workflows, operations, learning, and other timely patterns can all qualify.
4. If a user-provided direction has no strong 24–72h signal, skip it or mention that no strong signal was found; do not pad.
5. Market/user feedback should be real external signal (HN/GitHub issues/discussions/X/Reddit/product reviews/team writeups), not vendor claims.

## Good wording for cron prompts

Use wording like:

> 用户提到的方向只是参考，不是强制清单；不要特别跟踪用户随手举的某个仓库或例子。更开放地寻找“AI agent 前沿工作流”：凡是能说明人和 agent 如何更好协作、如何定义任务、如何验证结果、如何从真实用户反馈迭代的实践，都可以入选。每天优先“新鲜、有热度、有可迁移价值”的内容，而不是固定关键词命中。

## Anti-pattern

Avoid wording like:

> 必须特别跟踪 `<specific repo>`；必须覆盖 loop engineering/spec/harness/goal/eval/loss 每个方向。

That turns examples into rigid recurring slots and makes the briefing feel less frontier-aware.