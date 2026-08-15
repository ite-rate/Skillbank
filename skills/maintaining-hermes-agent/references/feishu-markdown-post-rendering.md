# Feishu Markdown rendering: preserve Markdown in `post` payloads

## Symptom

Feishu/Lark messages that should be readable Markdown (headings, separators, ordered lists, bullets, bold text, links, or briefing overview tables) display as raw source such as `|---|`, `##`, and `**...**`.

## Durable lesson

Treat this as a Feishu outbound payload/rendering-layer problem first, not as a prompt-format problem. Do **not** fix it by stripping normal Markdown from the generated message, wrapping the whole message in a code block, or globally escaping Markdown punctuation.

For user-facing briefings/research messages, preserve normal Markdown and send it through Feishu `post` content with an `md` element so the Feishu client can render/preview it.

## Investigation path

1. Classify the failure as outbound rendering, not content generation, if the generated text already contains the desired Markdown.
2. Inspect `gateway/platforms/feishu.py` around `_build_outbound_payload()` and the Markdown detection rules.
3. Check whether any special-case rule downgrades Markdown to `msg_type="text"`, especially Markdown tables.
4. Add a regression test in `tests/gateway/test_feishu.py` that captures the desired payload shape before changing production code.

## Known pitfall

A previous Feishu adapter rule downgraded Markdown tables to `text` because of concerns that Feishu post `md` table rendering might be imperfect. For this user's use case, that downgrade is worse: it exposes Markdown source and breaks readability. Markdown tables such as the daily briefing overview table should remain `post` + `md`.

Expected behavior for a simple table:

```md
| 属于啥 | 名字 | 干啥的简介 |
|---|---|---|
| 工具 | Reasonix | DeepSeek-first coding agent |
```

Expected outbound shape:

- `msg_type == "post"`
- post content contains an element like `{"tag": "md", "text": original_markdown}`

## Verification

Run focused Feishu adapter tests first, then broader platform tests if practical:

```bash
source venv/bin/activate
python -m pytest tests/gateway/test_feishu.py::TestAdapterBehavior::test_send_preserves_markdown_table_as_post_markdown -q
python -m pytest tests/gateway/test_feishu.py::TestAdapterBehavior -q
```

Ask before restarting `hermes gateway`; source changes will not affect the running launchd gateway process until it is restarted/refreshed.

## Formatting preference captured

For Feishu briefings, keep messages flat and scannable, but preserve normal Markdown. Do not use prompt-level bans like “no headings”, “no separators”, or “avoid bold” merely to work around Feishu preview issues. Fix the send layer instead.