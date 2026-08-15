# Feishu preview-layer Markdown rendering correction — 2026-06-11

## Trigger

During a discussion about the 7:40 personal daily briefing, the user objected to changing the report content to avoid Markdown markers:

- The user said all assistant replies naturally carry Markdown and that should not be changed.
- The complaint was specifically that Feishu preview/display showed Markdown source-like text (`---`, `##`, `**`, tables), making the delivered briefing hard to read.
- The user asked to solve this from the Feishu message preview/client-display layer rather than by weakening the report format.

## Durable lesson

For Feishu daily briefings, keep the report semantically rich and Markdown-friendly. Do not remove headings, emphasis, or other useful structure just because Feishu rendered a previous message poorly. Treat raw-Markdown readability as a platform adapter/rendering problem.

## What was observed in Hermes Feishu adapter

Relevant local adapter behavior observed during the session:

- Normal text content is sent as Feishu `text`.
- Markdown-looking content is sent as Feishu `post` using `md` elements.
- Markdown table-like content is detected and forced back to `text` because Feishu `post` `md` elements do not render Markdown tables reliably.
- When table-heavy Markdown falls back to `text`, Feishu displays Markdown syntax literally, causing the source-code-like preview problem.

## Implications for future fixes

Preferred fix order:

1. Keep daily briefing content quality and normal Markdown structure.
2. For the user's 7:40 briefing, include the requested overview table: `属于啥｜名字｜干啥的简介`.
3. Add `用户评价/社区口碑观察` to capture user-review signals for Reasonix/Codex/Claude Code/OpenCode/Cursor/Hermes/MCP skills.
4. Solve Feishu readability at send time:
   - Convert Markdown sections to Feishu rich `post` elements where possible.
   - For tables, prefer an interactive card or explicit rich layout/columns instead of relying on Markdown table rendering.
   - Consider applying this only to scheduled daily briefings first, leaving normal chat replies unchanged.
5. If source changes and gateway restart are required, ask before modifying/restarting, because the user prefers config-first fixes and explicit permission for source/restart actions.

## Anti-pattern

Do not instruct the LLM to avoid all `#`, `##`, `**`, `---`, or other Markdown markers as the primary solution. That makes the source content worse and does not address the Feishu rendering root cause.
