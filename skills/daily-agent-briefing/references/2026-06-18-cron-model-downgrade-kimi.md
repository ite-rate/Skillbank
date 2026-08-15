# Cron Job Model Downgrade: codex → OpenRouter kimi-latest

**Date:** 2026-06-18  
**Context:** Daily briefing cron jobs failing with `openai-codex` provider (network issues), need to downgrade to kimi via OpenRouter.

## Problem

Two daily briefing cron jobs were configured with:
- Provider: `openai-codex`
- Model: `gpt-5.5`

Both jobs failed with `last_status: error`. The user reported "网络不通不可用" (network unreachable). Need to downgrade to an alternative provider/model that works.

## Discovery: OpenRouter kimi model list

Queried OpenRouter API for available kimi models:

```bash
curl -s https://openrouter.ai/api/v1/models | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('data', [])
kimi_models = [m for m in models if 'kimi' in m.get('id', '').lower()]
for m in kimi_models:
    print(f\"{m.get('id')} | {m.get('name', 'N/A')}\")
"
```

Results:
```
moonshotai/kimi-k2.7-code | MoonshotAI: Kimi K2.7 Code
~moonshotai/kimi-latest | MoonshotAI Kimi Latest
moonshotai/kimi-k2.6 | MoonshotAI: Kimi K2.6
moonshotai/kimi-k2.5 | MoonshotAI: Kimi K2.5
moonshotai/kimi-k2-thinking | MoonshotAI: Kimi K2 Thinking
moonshotai/kimi-k2-0905 | MoonshotAI: Kimi K2 0905
moonshotai/kimi-k2 | MoonshotAI: Kimi K2 0711
```

## Strategy: use `kimi-latest` instead of pinned version

Instead of pinning to a specific version like `kimi-k2.5` or `kimi-k2.7-code`, use `~moonshotai/kimi-latest` (or just `kimi-latest` in the cron model field). This automatically resolves to the latest stable kimi model on OpenRouter, avoiding manual updates when new versions release.

## Cron job update pattern

```python
# List current jobs first
cronjob(action="list")

# Update each job to use kimi via OpenRouter
cronjob(action="update", job_id="...",
    model={"model": "kimi-latest", "provider": "openrouter"})
```

## Verification

After update, verify with `cronjob(action="list")`:
- `provider` should show `openrouter`
- `model` should show `kimi-latest`
- `next_run_at` should be the next scheduled time

## Key takeaways

1. **Model degradation path**: When `openai-codex` fails (network, auth, quota), OpenRouter + kimi is a reliable fallback for Chinese-language tasks.
2. **Use `kimi-latest` for auto-updates**: Pinning to specific versions (`kimi-k2.5`, `kimi-k2.7-code`) requires manual updates. `kimi-latest` always points to the current best stable model.
3. **Query before pinning**: When unsure which model is latest on a provider, query the provider's model list API rather than guessing. OpenRouter exposes all models at `/api/v1/models`.
4. **Check `last_status` in cron list**: `cronjob(action="list")` shows `last_status` (error/success) and `last_run_at` — use this to confirm failures before attempting fixes.
