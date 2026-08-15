# Provider Retry, Fallback, and Error Classification Pipeline

A reference for debugging Hermes Agent provider failures — the actual retry loop,
error classifier, and fallback chain mechanics. Based on source-code trace of
`agent/conversation_loop.py`, `agent/error_classifier.py`, and
`agent/chat_completion_helpers.py`.

## Key Files

| File | Role |
|------|------|
| `agent/conversation_loop.py` | Retry loop, recovery actions, fallback triggers |
| `agent/error_classifier.py` | `classify_api_error()` — 8-step priority pipeline |
| `agent/chat_completion_helpers.py` | `try_activate_fallback()` — chain advance + client swap |
| `agent/agent_runtime_helpers.py` | `restore_primary_runtime()`, transport recovery |

## Critical: No Circuit Breaker

Hermes Agent has **no circuit breaker** for provider calls. The retry mechanism is a
simple `for retry_count in range(max_retries)` loop with exponential backoff
(`2 ** retry_count` seconds). There is no half-open probe, no async health check,
no state machine tracking provider health across calls.

The only "circuit breaker" mention in source is in `agent/tool_guardrails.py` —
unrelated to provider routing.

If the user references "circuit breaker" or "breaker open/closed/half-open" in the
context of provider calls, they are likely thinking of a different system (e.g.,
Go's `net/http`, Istio, or a client library like `llmclient`). Correct this gently.

## Retry Loop Structure

```
for retry_count in range(max_retries):        # max_retries defaults to 3
    try:
        response = client.chat.completions.create(...)
        return response
    except Exception as api_error:
        classified = classify_api_error(api_error, ...)

        # 1. Credential pool rotation (auth/billing/rate_limit)
        # 2. Specialized recovery (image shrink, tool content strip, context compress)
        # 3. Eager fallback for 429/402 (don't burn retries on rate limiting)
        # 4. Non-retryable client error → try fallback, abort if exhausted
        # 5. Max retries → try transport recovery → try fallback → abort
```

`retry_count` is reset to 0 on successful fallback or transport recovery.
`compression_attempts` and `primary_recovery_attempted` are separate counters.

## Error Classification (8-Step Priority Pipeline)

`classify_api_error(error, provider, model, approx_tokens, context_length, num_messages)`
returns a `ClassifiedError` with `reason: FailoverReason`, `retryable: bool`,
`should_compress: bool`, `should_rotate_credential: bool`, `should_fallback: bool`.

Priority order (first match wins):

1. **Provider-specific patterns** — thinking signatures, long-context tier gates,
   OAuth beta rejections, llama.cpp grammar errors, Grok subscription errors
2. **HTTP status code** — see status-code mapping below
3. **Error code** (from body: `error.code`)
4. **Message pattern matching** — billing vs rate_limit vs context vs auth
5. **SSL/TLS transient alerts** → `FailoverReason.timeout`
6. **Server disconnect + large session** → `FailoverReason.context_overflow`
7. **Transport error types** (`ReadTimeout`, `ConnectTimeout`, `RemoteProtocolError`, etc.) → `timeout`
8. **Fallback** → `FailoverReason.unknown` (retryable with backoff)

## HTTP Status Code → FailoverReason Mapping

| Status | Reason | retryable | should_fallback | Notes |
|--------|--------|-----------|-----------------|-------|
| 400 | See `_classify_400()` | varies | varies | Context overflow, image too large, multimodal tool content, thinking signature, request validation |
| 401 | `auth` | False | **True** | Credential rotation first; fallback if exhausted |
| 402 | `billing` or `rate_limit` | varies | **True** | Disambiguated by transient signals ("try again", "resets at") |
| 403 | `auth` or `billing` | False | **True** | "key limit exceeded" → billing; otherwise auth |
| 404 | `model_not_found` or `unknown` | False/True | **True**/False | Policy-blocked 404s don't fallback |
| 413 | `payload_too_large` | True | False | Compress instead |
| **422** | `format_error` | **False** | **True** | Falls into "other 4xx" bucket — **triggers fallback** |
| 429 | `rate_limit` | True | **True** | Eager fallback before retry loop burns through |
| 500, 502 | `server_error` | True | False | Unless body contains request-validation signals → `format_error` |
| 503, 529 | `overloaded` | True | False | Retry with backoff |
| Other 4xx | `format_error` | False | **True** | Non-retryable, try fallback first |
| Other 5xx | `server_error` | True | False | Retryable |

## 422 Handling — Common Misconception

**422 DOES trigger fallback** (contra intuitive expectation). It's classified as
`format_error` with `should_fallback=True`, which means:

1. Retry loop sees `retryable=False` → marks as `is_client_error`
2. Before aborting, tries `_try_activate_fallback()` to switch providers
3. If fallback succeeds → `continue` with new provider
4. If fallback chain exhausted → abort with user-facing error

The intuition "422 means my request is wrong, don't bother retrying" is only
half-right — Hermes won't retry the *same* provider, but it WILL try a different
provider that may accept the request format.

## Fallback Chain Mechanics

`try_activate_fallback()` in `agent/chat_completion_helpers.py`:

1. If `_fallback_index >= len(_fallback_chain)` → return False (exhausted)
2. Advance index, read next entry `{provider, model, base_url?, api_key?}`
3. Skip invalid entries (missing provider/model)
4. Skip entries matching current provider+model (would loop)
5. Skip entries matching current base_url+model (same backend, different name)
6. Resolve client via `resolve_provider_client()`
7. Normalize model name for provider
8. Determine `api_mode` (chat_completions, codex_responses, anthropic_messages, bedrock_converse)
9. Swap agent state: `model`, `provider`, `base_url`, `api_mode`, `client`, clear transport cache
10. Set `_fallback_activated = True`, return True

On rate_limit/billing: sets `_rate_limited_until = now + 60s` for primary.

## Why "Last Error Only"

When the fallback chain is exhausted, Hermes surfaces only the **last** `api_error`
— not a collection of all errors across the chain. Reasons:

- Single variable: `api_error` is overwritten on each failed API call
- Actionability: the last error tells you why the *final* fallback also failed,
  which is the blocking reason. A list of N heterogeneous errors (timeout + 503 +
  401 + billing) is confusing — which is root cause vs. cascade?
- The chain is a priority-ordered degradation, not a voting pool

For debugging all chain errors, check logs (INFO level) — each `Error classified`
line records the reason, status, and provider/model.

## Per-Turn Primary Restoration

`restore_primary_runtime()` is called at the start of each turn via
`run_conversation()`. Without it, a transient failure in one turn would pin the
session to the fallback provider for all subsequent turns.

It restores: `model`, `provider`, `base_url`, `api_mode`, `api_key`, client,
prompt caching, context compressor state, credential pool provider affinity,
and resets `_fallback_activated` and `_fallback_index`.

Rate-limit cooldown can block restoration — if `_rate_limited_until > now`,
restoration returns False and the agent stays on fallback.
