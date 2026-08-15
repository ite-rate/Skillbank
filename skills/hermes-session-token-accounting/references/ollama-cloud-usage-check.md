# Ollama Cloud Usage Check — Fallback to Local DB

## Problem

User asked to check Ollama Cloud (GLM-5.2) usage. Ollama Cloud does not expose a usage/billing API endpoint. The API key (`OLLAMA_API_KEY` in `~/.hermes/.env`) only authorizes model inference, not account queries.

## Endpoints probed (all failed)

| Endpoint | Method | Result |
|---|---|---|
| `/v1/usage` | GET | 404 `path not found` |
| `/v1/billing` | GET | 404 |
| `/v1/credits` | GET | 404 |
| `/v1/quota` | GET | 404 |
| `/v1/limits` | GET | 404 |
| `/v1/balance` | GET | 404 |
| `/v1/me` | GET | 404 |
| `/v1/user` | GET | 404 |
| `/v1/profile` | GET | 404 |
| `/v1/plan` | GET | 404 |
| `/v1/entitlements` | GET | 404 |
| `/v1/subscription` | GET | 404 |
| `/api/usage` | GET | 404 |
| `/api/billing` | GET | 404 |
| `/api/account` | GET | 404 |
| `/api/me` | GET | 405 Method Not Allowed |
| `/api/me` | POST | 401 `invalid credentials` (bearer, basic, and body-key all rejected) |
| `/api/user` | GET | 404 |
| `/api/plan` | GET | 404 |
| `/api/credits` | GET | 404 |
| `/api/quota` | GET | 404 |
| `/api/limits` | GET | 404 |
| `/dashboard/api/usage` | GET | 404 |
| `/dashboard/api/me` | GET | 404 |

## Web dashboard

`https://ollama.com/settings` redirects to `signin.ollama.com` (OAuth login page). The API key does not work as a bearer token for web pages. Usage is only visible after web OAuth login.

## Pricing page findings

From `https://ollama.com/pricing`:
- Plans: Free / Pro (50× Free) / Max (5× Pro)
- Session limits reset every 5 hours; weekly limits reset every 7 days
- Usage is measured by **GPU time**, not tokens
- Model usage levels: level 1 (small, e.g. `gpt-oss:20b`) → level 4 (extra heavy, e.g. `deepseek-v4-pro`)
- "Check your usage here anytime" links to `/settings`

## Fallback: Hermes local session DB

The `sessions` table in `~/.hermes/state.db` records per-session token counts and `billing_provider`. This is the best available usage source when the provider has no API.

### Query: aggregate by provider+model

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
WHERE billing_provider = 'ollama-cloud'
GROUP BY billing_provider, model;
```

### Query: per-session breakdown

```sql
SELECT
    id,
    model,
    started_at,
    ended_at,
    message_count,
    input_tokens,
    output_tokens,
    estimated_cost_usd,
    title
FROM sessions
WHERE billing_provider = 'ollama-cloud'
ORDER BY started_at DESC;
```

### Query: last 24h

```sql
SELECT
    COUNT(*) as sessions,
    SUM(input_tokens) as input_tokens,
    SUM(output_tokens) as output_tokens
FROM sessions
WHERE billing_provider = 'ollama-cloud'
  AND started_at > strftime('%s', 'now', '-1 day');
```

### Python helper

```python
import sqlite3, os
from datetime import datetime

db_path = os.path.expanduser("~/.hermes/state.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
    SELECT id, model, started_at, message_count,
           input_tokens, output_tokens, title
    FROM sessions
    WHERE billing_provider = 'ollama-cloud'
    ORDER BY started_at DESC
""")

for row in cur.fetchall():
    sid, model, started, msgs, inp, out, title = row
    dt = datetime.fromtimestamp(started).strftime("%Y-%m-%d %H:%M") if started else "?"
    print(f"{dt} | msgs={msgs or 0} | in={inp or 0:,} | out={out or 0:,} | {title or ''}")

conn.close()
```

## Caveats

- `estimated_cost_usd` is $0 for Ollama Cloud because it bills by GPU time, not per-token.
- The DB totals reflect only successful API calls recorded by Hermes; failed/retried calls may not be captured.
- The DB is a lower bound on actual usage — the provider's own accounting (visible on the web dashboard) is authoritative.
- `hermes auth status ollama-cloud` confirms login state but does not return usage data.