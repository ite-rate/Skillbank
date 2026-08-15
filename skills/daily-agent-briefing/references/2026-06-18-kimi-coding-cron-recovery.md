# 2026-06-18 — Recover daily briefing cron by switching to native Kimi provider

## Context

The personal 07:40 daily briefing cron and the 07:45 Feishu group briefing failed with:

`RuntimeError: No LLM provider configured. Run hermes model to select a provider, or run hermes setup for first-time configuration.`

The jobs were pinned to:

- `provider: openrouter`
- `model: kimi-latest`

But the live Hermes environment only had `KIMI_API_KEY` and no `OPENROUTER_API_KEY`. The main interactive Hermes config was `openai-codex / gpt-5.5`, so normal chat could work while the cron jobs failed.

## Durable lesson

Before moving a scheduled daily briefing to OpenRouter + Kimi, verify `OPENROUTER_API_KEY` exists. If only `KIMI_API_KEY` exists, use Hermes' native Kimi provider instead:

- `provider: kimi-coding`
- `model: kimi-k2.6` (or the current supported Kimi model from Hermes' provider model list)

Confirmed minimal smoke test:

```bash
hermes chat -q '只回复 OK' --provider kimi-coding -m kimi-k2.6 -Q
```

Expected output includes `OK`.

## Cron update pattern

Use the cronjob tool to update all daily briefing jobs:

```python
cronjob(action="update", job_id="d8aaf6a9745b", model={"provider": "kimi-coding", "model": "kimi-k2.6"})
cronjob(action="update", job_id="1537ba5b02ff", model={"provider": "kimi-coding", "model": "kimi-k2.6"})
cronjob(action="list")
```

Then verify the underlying persisted jobs if needed:

```bash
python3 - <<'PY'
import json, pathlib
p=pathlib.Path.home()/'.hermes/cron/jobs.json'
data=json.loads(p.read_text())
for j in data['jobs']:
    if j['name'].startswith('daily-0740'):
        print(j['id'], j['provider'], j['model'], j['next_run_at'], j['enabled'])
PY
```

## Same-day manual recovery pattern

`cronjob(action="run")` schedules a run for the next scheduler tick; it may not be a good enough user-facing recovery path if the user asks "execute today's briefing now" and the job status/output does not update promptly.

Reliable fallback:

1. Extract the saved cron prompt from `~/.hermes/cron/jobs.json`.
2. Run it directly with `hermes chat --provider kimi-coding -m kimi-k2.6 --skills daily-agent-briefing --toolsets web,browser,terminal,file -Q -q "$(cat /tmp/prompt.txt)"`.
3. Save stdout, extract the final briefing marker (for Format A, e.g. `## YYYY-MM-DD 中文 Agent 早报`).
4. Send the extracted final Markdown to Feishu.

Important send pitfall: `send_message` does **not** execute shell interpolation. Passing `message="$(cat /tmp/file.md)"` sends the literal string. Read the file content first and pass the actual string.

## What not to overgeneralize

Do not save a rule that cron is broken or that `cronjob(action="run")` never works. The durable lesson is: for urgent same-day recovery, verify actual output/status and use a direct `hermes chat` run if the scheduler path does not produce promptly.
