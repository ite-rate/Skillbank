---
name: hermes-session-token-accounting
description: Use when estimating Hermes conversation token usage, costs, rounds, or excluding a later segment such as vault/documentation cleanup when per-message token counts are missing.
level: manual
native_agent: Hermes
version: 1.0.0
license: CC0-1.0
---

# Hermes Session Token Accounting

Use this when the user asks “how many tokens/rounds did that session take?”, especially when they want to exclude a later phase such as整理沉淀, file writing, or retries.

## Core principle

Hermes `sessions` has reliable **whole-session** totals, but `messages.token_count` may be null. For partial-session accounting, combine DB totals with JSONL/request-dump replay and report uncertainty.

## Workflow

1. **Identify the session and cutoff**
   - Start with `session_search` or recent sessions.
   - Inspect `~/.hermes/state.db` and `~/.hermes/sessions/<session_id>.jsonl`.
   - Define the cutoff from the user’s wording, e.g. exclude from “本次会话...沉淀到...” onward.

2. **Count rounds before cutoff**
   - Count `role='user'` before cutoff.
   - Count visible assistant replies before cutoff.
   - Prefer “effective Q-A rounds” = user turns that receive a visible assistant reply; mention raw user message count if it differs.

3. **Get whole-session token totals**
   ```sql
   SELECT input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens
   FROM sessions WHERE id='<session_id>';
   ```

4. **Estimate partial tokens when per-message token_count is null**
   - Find latest `~/.hermes/sessions/request_dump_<session_id>_*.json`.
   - Extract `request.body.instructions`, `tools`, and `input`.
   - Use `tiktoken` (`o200k_base` is a good default for GPT/Codex-style sessions) to estimate:
     - static prompt/tools tokens
     - cumulative history tokens at each assistant call
     - assistant output/reasoning/tool-call text tokens
   - Compute ratios: `estimated_pre_cutoff / estimated_full`.
   - Scale the DB whole-session totals by those ratios.

5. **Check failed/retried API calls that are not in DB totals**
   - `sessions` totals only reflect successful API responses with usage. Failed 429/retry attempts may still send a large context but are not persisted as token usage.
   - Search logs for the session around the relevant time, especially `~/.hermes/logs/gateway.log` / `agent.log` lines like:
     - `API call failed after 3 retries... msgs=N tokens=~X`
     - `Context: N msgs, ~X tokens`
   - If the user asks “花了多少 token” rather than strictly “成功计费 tokens”, report a second inclusive estimate: `successful persisted total + retry_attempts * logged_context_tokens`.
   - Call out this distinction explicitly; otherwise users may correctly object that the number is too low.

6. **Report clearly**
   - Separate `input`, `output`, `reasoning`, and `cache_read`.
   - Give at least two totals: persisted successful usage including cache-read, and excluding cache-read.
   - If retries/failures occurred, also give “含失败重试/上下文尝试”的 total.
   - State that partial-session tokens are estimates if no per-message token accounting exists.

## Useful commands

```bash
sqlite3 -header -column ~/.hermes/state.db \
  "SELECT id, message_count, tool_call_count, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens FROM sessions ORDER BY started_at DESC LIMIT 10;"
```

```bash
sqlite3 -header -column ~/.hermes/state.db \
  "SELECT id, role, datetime(timestamp,'unixepoch','localtime') t, substr(replace(content,char(10),' '),1,160) snippet FROM messages WHERE session_id='<sid>' ORDER BY timestamp;"
```

Python sketch for ratios:

```python
import json, tiktoken
enc = tiktoken.get_encoding('o200k_base')
def toks(s): return len(enc.encode(s or ''))
# static = toks(instructions) + toks(json.dumps(tools, ensure_ascii=False))
# replay JSONL up to cutoff and full session; scale DB totals by estimated ratios
```

## Provider Usage Check (when the provider has no usage API)

Some providers (e.g. Ollama Cloud) do not expose a usage/billing API endpoint. The API key only authorizes model inference (`/v1/models`, `/v1/chat/completions`), not account/usage queries. In this case, the Hermes `sessions` table is the best available usage source.

### Workflow

1. Identify the provider name from `~/.hermes/config.yaml` (`model.provider` and `model.base_url`) or `hermes status`.
2. Query the `sessions` table grouped by `billing_provider` and `model`:

```sql
SELECT
    billing_provider,
    model,
    COUNT(*) as sessions,
    SUM(input_tokens) as input_tokens,
    SUM(output_tokens) as output_tokens,
    SUM(cache_read_tokens) as cache_read_tokens,
    SUM(cache_write_tokens) as cache_write_tokens,
    SUM(reasoning_tokens) as reasoning_tokens,
    SUM(estimated_cost_usd) as est_cost,
    SUM(actual_cost_usd) as actual_cost
FROM sessions
WHERE billing_provider = '<provider_name>'
GROUP BY billing_provider, model;
```

3. For a per-session breakdown, select `id, started_at, message_count, input_tokens, output_tokens, title` ordered by `started_at DESC`.
4. For "last 24h" or "today" filtering, use `started_at > strftime('%s', 'now', '-1 day')`.
5. Note that `estimated_cost_usd` may be $0 for providers that bill by GPU time rather than per-token (e.g. Ollama Cloud). State this explicitly.

### Ollama Cloud specifics

- Provider name in Hermes: `ollama-cloud`
- API key env var: `OLLAMA_API_KEY` (stored in `~/.hermes/.env`)
- Auth status: check with `hermes auth status ollama-cloud`
- **No usage API exists.** Endpoints `/v1/usage`, `/v1/billing`, `/v1/credits`, `/v1/quota`, `/api/usage`, `/api/me`, `/api/account`, etc. all return 404 or 405.
- The web dashboard at `https://ollama.com/settings` shows usage but requires OAuth web login (redirects to `signin.ollama.com`), not API key bearer auth.
- Ollama Cloud bills by **GPU time**, not tokens. Session limits reset every 5 hours; weekly limits reset every 7 days. Plans: Free / Pro (50× Free) / Max (5× Pro).
- Usage level per model is shown on the model's page on ollama.com (level 1 small → level 4 extra heavy).

See `references/ollama-cloud-usage-check.md` for the full endpoint probe log and fallback approach.

## Pitfalls

- Do not treat `messages.token_count` as reliable without checking; it is often null.
- Do not confuse raw user messages with effective Q-A rounds; consecutive user corrections may collapse into one answered round.
- Do not include later vault/documentation/file-writing phases if the user explicitly excludes “最后整理沉淀”.
- Cache-read tokens can dominate totals; always say whether they are included.
- Failed/retried 429 calls may not update `sessions` totals; use logs to account for context attempts when the user cares about actual consumption/usage pressure.
- Whole-session totals in `sessions` are authoritative for successful persisted usage; partial splits and retry-inclusive totals are estimates.

## Verification

Before answering, verify:
- session id and cutoff line/message
- raw user count and visible assistant/effective round count
- whole-session DB totals
- whether the partial token number is exact or estimated
