---
name: go-interview-rapid-project-design
description: Fast-track interview prep by co-designing a minimal Go project in chat, using a request pipeline (Request/Response/Workflow/RequestContext) and iterative bug-story/answer generation.
level: manual
native_agent: Hermes
---

# Go Interview Rapid Project Design

Use this skill when the user wants to sound like they have real hands-on experience in a Go backend / gateway / LLM-routing interview, but needs a fast, guided way to build that story in chat.

## Goal
Turn abstract architecture into a small, believable Go project that the user can explain naturally in an interview.

## Best-fit scenario
- The user says they need to "speed-run" interview prep.
- The user wants to define structs, functions, input/output, and variable names collaboratively.
- The user prefers Go and wants to talk about a request chain: middleware → handler → workflow resolution → provider adapter → audit/usage.
- The user wants to practice by describing pieces and receiving immediate design feedback.

## Workflow

### 1) Start from the smallest credible system
Prefer a minimal Go request pipeline with these layers:
- HTTP server
- middleware
- handler
- budget check
- cache lookup
- workflow resolution
- provider adapter
- audit/usage logging

Keep it small enough to explain in 3 minutes, but rich enough to support follow-up questions.

### 2) Define four core data types first
Always establish these before writing functions:
- `ChatRequest`: external input
- `ChatResponse`: external output
- `Workflow`: internal strategy decision
- `RequestContext`: full request lifecycle state

If needed, also define:
- `ProviderRequest`
- `ProviderResponse`
- `Usage`

### 3) Design the flow in terms of data movement
For each function, answer:
- What does it take in?
- What does it return?
- What state is mutated?
- What should *not* be stored there?
- What can fail?

Prefer this order for the main handler flow:
1. middleware prepares request metadata (`RequestMeta`) and stores it in `context.Context`
2. handler parses body into `ChatRequest` and builds `RequestContext`
3. handler checks budget
4. workflow resolution picks a strategy
5. cache lookup runs after workflow if the cache key depends on model/provider/policy
6. provider adapter executes
7. audit/usage are finalized once at the end

Mention the cache/workflow ordering tradeoff explicitly: simplified diagrams may put cache before workflow, but in realistic gateways the final model/provider/policy often affects cache key, so resolving workflow first is more defensible.

### 4) Use the "one exit point" mindset
A common interview-grade design is to avoid scattered returns that bypass audit/usage finalization.

Recommended pattern:
- record start in middleware
- execute business steps
- always finalize audit/usage in one shared exit path

This gives a believable explanation for cache hits, provider failures, and fallback paths.

### 5) Build bug stories intentionally
Ask the user to imagine or add 2–3 realistic failures, then explain how they would detect and fix them:
- cache hit returns early and misses usage/audit finalization
- fallback causes duplicate usage or billing
- workflow selection and provider request construction become inconsistent
- audit failure should not block the main response path
- in-memory cache map is read/written concurrently without `sync.RWMutex`
- cache returns a stored `*ChatResponse` pointer and later code mutates it, polluting cached data

For each bug, walk through:
- symptom
- root cause
- how it was found
- how it was fixed
- what changed in the design

### 5.5) Explain budget as a reusable reserve/commit pattern
When the user asks about budget beyond a static check, frame it as a general backend resource-preallocation model:
- simple `check then deduct` fails under concurrency because multiple requests can all see the same available balance
- `reserve`: atomically move estimated resource from `available` to `reserved` before doing expensive work
- `commit`: after provider returns actual usage, settle from the reserved amount and refund unused quota
- `rollback`: if provider/request fails, release the reserved amount back to `available`
- use `reservation_id` to tie a commit/rollback to a specific in-flight request
- use reservation `status` (`reserved`, `committed`, `rolled_back`, `expired`) for idempotency and retry safety
- add `expire_at` or a cleanup worker so abandoned reservations do not leak capacity

Interview wording: reserve solves concurrent oversell, commit solves final settlement, rollback solves failure release, status solves idempotency, and expiry solves leaked reservations. This applies to LLM tokens, inventory, coupons, account balance, seats, and API quotas.

### 6) Convert design into interview wording
Transform each component into a short explanation:
- middleware = entry governance / context initialization
- handler = request orchestration
- budget = early rejection of invalid requests
- cache = latency/cost reduction
- workflow resolution = strategy selection
- provider adapter = execution against upstream
- audit = observability and traceability

## Chat collaboration pattern
When the user sends a struct/function, respond with:
- recommended fields or parameters
- improved types
- where it belongs in the chain
- possible bugs
- a one-line interview explanation
- optional naming suggestions

Prefer incremental, conversational co-design rather than dumping a full codebase.

If the user asks whether to read source or design in chat, recommend a hybrid: use source for real naming/order, then have the user restate the design in their own words and correct it into interview wording. For rapid confidence-building, chat-based co-design is usually faster than dumping code.

When the user struggles with Go mechanics, slow down and explain with concrete relationships:
- `context.Context` = per-request carrier/bag
- custom `contextKey` = typed key to avoid collisions; same string value with a different key type is not the same key
- `RequestMeta` = the value stored in context under `requestMetaKey`
- middleware `Chain` = nested wrapping; reverse iteration makes request execution order match the declared order
- `defer audit.Finish(...)` = register finalization now, execute when the handler returns, after downstream modules have filled `RequestContext`
- `chan AuditEvent` = a small in-process queue/basket for async audit events; `Finish` builds an event snapshot and enqueues it, while a worker goroutine writes slowly in the background

For audit confusion, emphasize: modules usually do not call audit at every step; they update `RequestContext`. `Finish` later reads the final `RequestContext`, builds an immutable `AuditEvent` snapshot, and sends that snapshot to a recorder/logger. Do not send the mutable `*RequestContext` pointer directly to an async goroutine.

## Suggested skeleton
```go
type ChatRequest struct {
    RequestID string `json:"request_id,omitempty"`
    UserID    string `json:"user_id"`
    Prompt    string `json:"prompt"`
    Model     string `json:"model,omitempty"`
    Stream    bool   `json:"stream,omitempty"`
    Tools     []string `json:"tools,omitempty"`
    Params    map[string]any `json:"params,omitempty"`
}

type Usage struct {
    PromptTokens     int `json:"prompt_tokens"`
    CompletionTokens int `json:"completion_tokens"`
    TotalTokens      int `json:"total_tokens"`
    CostCents        int `json:"cost_cents,omitempty"`
}

type ChatResponse struct {
    RequestID string `json:"request_id"`
    TraceID   string `json:"trace_id,omitempty"`
    Model     string `json:"model"`
    Source    string `json:"source"`
    Content   string `json:"content"`
    Usage     Usage  `json:"usage"`
    Error     string `json:"error,omitempty"`
}

type Workflow struct {
    Name           string
    ProviderName   string
    ModelName      string
    UseCache       bool
    EnableAudit    bool
    EnableFallback bool
    TimeoutMs      int
    Policy         string
}

type RequestContext struct {
    RequestID string
    TraceID   string
    UserID    string
    StartAt   time.Time

    Request  ChatRequest
    Workflow Workflow

    CacheHit bool
    Source   string
    Usage    Usage
    Err      error
}
```

## Saving notes to the user's vault
When the user asks to save or “沉淀” the session, clarify and respect the requested fidelity:
- If they say “原文”, “一字不要改”, “verbatim”, or emphasize preserving high-value phrases, do **not** rewrite into summaries. Save User/Assistant text as原文 blocks.
- Prefer one Markdown file per question/answer or topic, plus an `INDEX.md` organized by module.
- The index should be navigation only: clear question-style link labels, grouped by modules. Do not put rewritten summaries in the index unless asked.
- Preserve high-value original sections such as “一句话记忆”, “坑”, “面试话术”, “绕点解释”, code snippets, and analogies inside the linked原文 files.
- If the current chat transcript is available in Hermes `state.db`, extract original messages by session rather than reconstructing from memory. Verify a sample note after writing.

Good structure:
```text
gomodel-llm-gateway-interview-verbatim/
  INDEX.md              # module-organized links only
  README.md
  notes/
    01-问题标题.md       # User 原文 + Assistant 原文
    02-问题标题.md
```

## Pitfalls
- Don’t stuff every field into `ChatRequest`; keep runtime state in `RequestContext`.
- Don’t let audit be the thing that decides success/failure of the main path unless the user explicitly wants that.
- Don’t let workflow selection and provider request building drift apart.
- Don’t over-design; the point is interview credibility, not production completeness.
- Don’t summarize when the user requested 原文沉淀; make an index and link to verbatim note files instead.

## Interview framing
A good answer sounds like:
> I split external input, internal strategy, and runtime state into separate structs so the request lifecycle stays clear. Middleware initializes context, handler orchestrates the flow, workflow chooses the strategy, provider executes it, and audit/usage are finalized at the end.

## Use this skill when
- The user wants to build a believable story around Go backend or gateway work.
- The user wants to design structs/functions live in chat.
- The user wants a reusable framework for rapid interview prep.
