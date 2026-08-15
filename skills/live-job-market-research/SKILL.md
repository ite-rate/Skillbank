---
name: live-job-market-research
description: Research current hiring trends from public recruitment sources when major job boards are partially blocked. Use search-engine indexing, employer career pages, and cautious extraction of visible JD details to avoid fabricated counts.
level: manual
native_agent: Hermes
---

# Live job market research

Use this skill when the user asks for current hiring trends, role requirements, salary bands, or job counts from public recruitment sources such as Boss直聘, 智联招聘, 拉勾, 51job, or employer career pages.

## Goal
Produce a grounded market summary from **verifiable, currently visible** sources, even when some platforms block direct access.

## Key principles
- Prefer **live, visible pages** over model memory.
- Do **not** invent counts, salaries, or JD requirements.
- If a site blocks access, report the limitation and pivot to accessible sources:
  - search-engine snippets
  - employer career pages
  - official campus recruitment pages
  - company blogs / hiring pages
- Separate **directly verified facts** from **inferred market trends**.

## Workflow

### 1) Frame the query
Use query bundles that capture the role family and likely synonyms.
Examples:
- `AI Agent`
- `大模型 应用`
- `LLM 应用开发工程师`
- `RAG 招聘`
- `智能体 工程师`
- `Agent 平台`

If needed, include `site:` filters for specific platforms or company career sites.

### 2) Probe accessibility early
Try the target platform directly.
If the page shows:
- security verification
- captcha
- login wall
- empty shell

then do not force the issue. Mark the source as blocked and switch to alternate sources.

### 3) Use search engines as a discovery layer
Search engine snippets are useful for:
- approximate visible result counts
- candidate URLs
- page titles
- recent dates in snippets

Treat these as discovery only. Do **not** claim they equal true posting counts on the job board.

### 4) Extract from accessible employer pages
When a direct job board is blocked, inspect employer career pages that are publicly accessible.
Extract:
- title
- company / business unit
- city
- role type (intern / full-time / research / algorithm / application / platform)
- update date
- responsibilities
- requirements
- nice-to-have items

### 5) Normalize requirements into buckets
Common buckets:
- LLM fundamentals
- Prompt / context engineering
- Tool calling / function calling
- RAG / knowledge base
- Agent workflows / multi-agent orchestration
- Evaluation / tracing / observability
- Backend / API / distributed systems
- Python / Java / JS / Go requirements
- AI infra (vLLM, Ollama, KV cache, inference optimization)
- Training / SFT / RLHF / DPO / multimodal

### 6) Summarize the market honestly
Recommended structure:
- What is directly verified
- What is inferred from sample JDs
- What is blocked / unavailable
- Practical implications for job seekers

## Pitfalls
- Do not mix search result counts from Bing/Google with actual job-board posting counts.
- Do not generalize from a single JD; sample at least a few postings when possible.
- Do not hide bot-protection or login barriers.
- Do not cite blocked sources as if they were fully inspected.

## Good output format
1. Source status table
2. Sample postings table
3. Repeated requirement themes
4. Role segmentation
5. Advice for candidates by background
6. Limitations / caveats

## Verification checklist
- Every JD claim should be backed by a visible page or snippet.
- Every count should have a clear origin and confidence level.
- Distinguish current observations from historical or general background knowledge.
