# Code-Anchored Socratic Learning

A variant of the Feishu-style project-first coaching pattern where a **production
codebase** (not curated notes) serves as the primary learning anchor. The
learner and assistant both operate on real source code — the assistant asks
design-decision questions rooted in concrete code, and the learner answers
from architectural reasoning.

## When to use

- Learner has a local checkout of a relevant production project (e.g. GoModel
  for AI Gateway learning).
- The project has a structured overview document (CODE_WIKI.md, ARCHITECTURE.md)
  that maps the module/layer hierarchy.
- Learner wants deep architectural understanding, not API-surface familiarity.
- Learner explicitly rejects warm-up questions ("太浅了", "直接进入核心").

## Setup

Minimal vault entry — just enough to anchor the session:

```
Projects/<topic>/
├── README.md     — goal + learning style
├── MAINLINE.md   — module sequence with brief notes
└── STATE.yaml    — current module, current question, last assessment
```

No NODES/, DRILLS/, NOTES/ unless the learner asks.

## Question design rules

1. **Start from the codebase's own module boundary, not from category definitions.**
   Wrong: "What is X?"
   Right: "This layer does Y. Why does it exist as a separate module? What
   breaks if it's merged into the layer above?"

2. **Every question must be answerable from the code itself plus architectural
   reasoning.** The assistant reads the relevant source before asking.

3. **Anchor every question in a concrete code artifact** — a file, a function
   signature, a struct, a data flow, a config key. The learner should be able
   to point to the code that proves or disproves their answer.

4. **Follow the module chain in dependency order.** In GoModel: Server →
   Gateway (translation layer) → Provider (protocol adaptation) → llmclient
   (resilience) → Cache → Observability.

5. **After each answer, correct only 1–2 key points, then supply a compressed
   "improved version" (30-second summary).** Don't dump full explanations.

## Handling learner signals

- "太浅了/直接进入核心" → skip prediction gate. Jump to design-tension
  questions anchored in specific code modules.
- "先解释一下相关的基础知识" → pause the Socratic flow. Read the relevant
  source/docs, give a concise factual explanation, then resume with the
  original question.
- Learner gives a partial answer → "方向对了 X%: correct → missing →
  improved 30s version."
- "继续主线" → advance to the next module in MAINLINE.md.

## Module structure (proven example from GoModel 9-module deep-dive)

| # | Module | Core question | Code anchor |
|---|--------|--------------|-------------|
| 0 | Auth system | Two user_path injection paths — which wins? | internal/server/auth.go, internal/authkeys/service.go |
| 1 | Request lifecycle | Why translate all ingress protocols to internal ChatRequest? | internal/core/interfaces.go, internal/anthropicapi/ |
| 2 | Provider routing & user_path | What breaks when model names overlap across providers? Trust boundary? | internal/providers/router/, internal/core/user_path.go |
| 3 | Two-layer cache | Exact + semantic — why guardrail must run before cache? Streaming replay? | internal/responsecache/simple.go, semantic.go |
| 4 | Guardrail | System prompt vs LLM altering — injection paradox? Pipeline serial/parallel? | internal/guardrails/ |
| 5 | Fallback + circuit breaker | What happens when the fallback chain exhausts? 422 excluded? 429 not counted? | internal/gateway/fallback.go, internal/llmclient/circuit_breaker.go |
| 6 | Workflow strategy engine | Compile at request time or background? Why atomic.Value.Store? | internal/workflows/compiler.go, service.go |
| 7 | Full-chain function-level trace | Every function on the critical path, annotated with file:line | internal/server/, internal/gateway/ |
| 8 | Observability three-line separation | Audit/Usage/Budget — two async, one sync. Why? SSE observers? | internal/auditlog/, internal/usage/, internal/budget/ |
