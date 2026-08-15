# openai-codex Cron Model Name Discovery

**Date:** 2026-06-08  
**Context:** Switching daily briefing cron jobs from `deepseek-v4-pro` to local `openai-codex` provider.

## Problem

When using `openai-codex` as a cron job provider, the model name parameter is NOT free-form. The Codex Responses API (backed by a ChatGPT account) validates model names and rejects unsupported slugs.

## Model names tested (all REJECTED)

| Model | Error |
|-------|-------|
| `codex` | `The 'codex' model is not supported when using Codex with a ChatGPT account.` |
| `gpt-4o` | `The 'gpt-4o' model is not supported when using Codex with a ChatGPT account.` |
| `auto` | `The 'auto' model is not supported when using Codex with a ChatGPT account.` |

## Resolution

The `codex` CLI stores its active model in `~/.codex/config.toml`:

```toml
model = "gpt-5.5"
```

Using the exact value from the CLI config (`gpt-5.5`) as the cron job model name succeeds.

## Root cause

Hermes uses the `codex_responses` API mode (not chat completions) when `provider = "openai-codex"`. This is the same API that the Codex CLI and ChatGPT web interface use. The model catalog for this API differs from the standard OpenAI chat completions catalog — it's gated by the ChatGPT subscription tier and account type.

## Cron job configuration pattern

```python
cronjob(action="update", job_id="...", 
    model={"model": "gpt-5.5", "provider": "openai-codex"})
```

## Key takeaway

**Do not guess model names for `openai-codex` provider.** Always read `~/.codex/config.toml` first. The active model slug is the only reliable value — aliases like `codex`, `auto`, or standard OpenAI names like `gpt-4o` will NOT work.
