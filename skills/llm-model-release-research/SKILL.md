---
name: llm-model-release-research
description: When an AI model released or which provider runs it.
level: manual
native_agent: Hermes
---

# LLM Model Release & Availability Research

Covers: "when was Qwen X released", "is model X available on OpenRouter / Ollama", "how hot is model Y". The user (telecom sales, exploring AI-infra/gateway direction, daily AI briefing) hits this repeatedly, so keep it fast and source-verified.

## Workflow

1. **Release date + heat** — use HN Algolia `search_by_date` (not relevance):
   ```
   https://hn.algolia.com/api/v1/search_by_date?query=<model>&tags=story&hitsPerPage=10
   ```
   - `created_at` on the hit whose URL is the official blog post IS the release day (Alibaba Qwen blogs at `qwen.ai/blog?id=qwen3.x`, e.g. "Qwen3.8-Max: A New Bar for Coding and Cowork").
   - `points` + `num_comments` give the heat signal; `front_page` tag means it trended on HN.
   - Try several spellings (space vs hyphen: `qwen3.7-max`, `Qwen 3.7 Max`) — Algolia tokenizes, and nbHits is small so scan all pages.

2. **OpenRouter availability (industry indicator, NOT the user's provider)** — `https://openrouter.ai/api/v1/models` returns a huge (~600KB) JSON. The browser snapshot lands in a cache file; do NOT dump it to context. Grep for the id:
   ```
   grep -oE 'qwen/qwen3[0-9.]*-[a-z0-9-]*' <cache_file> | sort -u | grep -E "3\.[78]"
   ```
   - Canonical slugs embed the release date: `qwen3.8-max-20260803` = released 2026-08-03.
   - If a model shows up here it's immediately usable via any OpenAI-compatible agent.
   - Fast single-model check: browse `https://openrouter.ai/<vendor>/<model>` — a 404 page means not listed yet (e.g. GLM-5.3 on launch day 2026-08-14 was 404; weights come 2 weeks later anyway).
   - NOTE: user's actual Hermes provider is `opencode-go` — OpenRouter/Ollama checks are ONLY to answer "how fast can anyone use this" / where it's hosted, not the user's own stack.

3. **Ollama cloud availability** — browse `https://ollama.com/search?q=<model>`. Ollama focuses on locally-runnable models, so flagship "Max"-class models are usually NOT in the official library; only community quantized uploads (e.g. `aratan/qwen3.7-35b-q4`) show up. Expect a lag.

## Pitfalls

- **Disambiguate the model name** — if the user names a model + a freshness signal (新发/登顶/刚发/trending), search recent context first, not the most famous same-name result. Release dates differ by weeks.
- **User's ACTIVE Hermes provider is `opencode-go`** (not Ollama cloud — that note was stale). Don't frame availability answers around the user's own provider; report industry availability (OpenRouter/HF/weights) instead, and only mention Ollama if the user asks about local running.
- **Don't fabricate release dates.** If no official blog hit / provider listing exists, say so rather than guessing (user explicitly rejects invented data: "拿不到数据不要瞎扯").
- OpenRouter's JSON is one giant line — `grep -oE` for id substrings is the fast path; `grep -c` on the whole file for exact strings often returns 0 because the file is one line.
