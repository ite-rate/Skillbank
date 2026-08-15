# Feishu Markdown preview debugging note

Session lesson: when Hermes messages in Feishu show raw Markdown, first distinguish normal Markdown from Markdown pipe tables before changing code.

Observed routing in `gateway/platforms/feishu.py`:
- Plain text routes as Feishu `text`.
- Common Markdown hints such as `**bold**`, inline code, headings, lists, links, and blockquotes route as `post` with an `md` element and can preview/render normally.
- Markdown pipe tables matching a header plus separator line, e.g. `| A | B |` followed by `|---|---|`, are deliberately forced to `text` because Feishu post `md` does not reliably render tables and may appear blank.

No-source-change workaround:
- Do not output Markdown pipe tables for Feishu messages.
- Preserve readable 3-column overviews using full-width separators and no Markdown separator row:
  `属于啥｜名字｜干啥的简介`
  `工具｜Reasonix｜DeepSeek-first coding agent`
- Or use list-style rows:
  `**工具｜Reasonix** — DeepSeek-first coding agent`

Workflow pitfall:
- If the user prefers config-first fixes, do not patch Hermes source just because the source-level fix is obvious. Investigate, report the root cause, propose config/prompt/content-shape workarounds first, and ask before editing source.
