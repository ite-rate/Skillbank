# AI Gateway / GoModel Routing Strategy Interview Prep

Use this reference when the user says an interviewer asked about AI Gateway / GoModel routing strategy, provider selection, fallback, streaming, or "what optimizations did you do", especially when their project is a simplified GoModel-like implementation and they feel exposed on details.

## Coaching stance: do not stop at the routing table

The user's correction from this session is important: shallow talking points like "do not query model inventory on every request" are not enough for interview prep and should not be saved as a main question. Treat them as implementation hygiene, not the core story.

The better coaching target is:

```text
OpenAI-compatible request
-> selector resolution: model + provider hint, including slash-shaped model ambiguity
-> workflow/policy context: resolved route + endpoint + cache/usage/audit/fallback/guardrails flags
-> execution: primary provider call through adapter
-> fallback decision: only for recoverable availability/rate/model errors, not invalid requests
-> return: JSON or SSE stream, with audit/usage attributed to the resolved route
```

Warn against over-claiming. If the project is simplified, phrase it as **model-based routing with governance hooks**, not full intelligent load balancing unless weights, health checks, circuit breakers, and latency/cost-aware selection actually exist.

## Minimal source-reading path for GoModel-like projects

For the deeper GoModel route, read the smallest closure that supports the answer:

```text
internal/gateway/inference_prepare.go
  PrepareChatRequest / PrepareResponsesRequest
  ensureTranslatedRequestWorkflow
  ApplyResolvedSelector
  WithCacheRequestContext

internal/gateway/inference_execute.go
  ExecuteChatCompletion / StreamChatCompletion
  ResolveChatRoute
  CanFastPathStreamingChatPassthrough

internal/gateway/fallback.go
  FallbackSelectors
  tryFallbackResponse / tryFallbackStream
  ShouldAttemptFallback

internal/gateway/interfaces.go
  ModelResolver / ModelAuthorizer / WorkflowPolicyResolver / FallbackResolver / TranslatedRequestPatcher

internal/server/translated_inference_service.go
  handleTranslatedJSON
  dispatchChatCompletion
  handleWithCache
  audit enrichment around resolved route / failover
```

If working with the user's persisted notes, the relevant local answer bank is usually under:

```text
/Users/ss/Documents/main_store/xzs/GoModel学习仓库
```

## Deep 1-minute answer

> My GoModel-style gateway is not just a model-to-provider map. A request first comes in as an OpenAI-compatible Chat or Responses request. The gateway resolves the requested `model` plus optional `provider` hint into a concrete selector, being careful with slash-shaped model IDs so it does not blindly split `provider/model`. After resolution, it builds a workflow context that carries the resolved model, provider type/name, endpoint operation, and policy features like cache, usage, audit, fallback, and guardrails. Execution then calls the primary provider through an adapter. If the call fails, fallback is controlled by workflow policy and error taxonomy: 5xx, 429, and model unavailable/not_found/deprecated can switch; invalid parameters or auth errors should not. For streaming, there is a fast path only when no selector/body rewrite or forced usage injection is needed. Finally, audit and usage should record the resolved route and failover target, not only the requested model.

## Real optimization talking points

1. **Selector ambiguity control**
   - `provider/model` can mean a provider-qualified selector, but many raw model IDs also contain `/`.
   - Explicit `provider` field should win.
   - Without explicit provider, only treat a prefix as provider if it matches configured provider name/type; otherwise keep the raw model ID.

2. **Workflow/policy as a shared execution context**
   - Avoid scattering `cacheEnabled`, `usageEnabled`, `fallbackEnabled`, and `guardrails` checks through handlers.
   - Build a workflow that binds resolved selector, provider metadata, endpoint, and policy version/features.
   - Cache, usage, audit, fallback, and guardrails all read the same context.

3. **Fallback error taxonomy**
   - Do not fallback on every error.
   - Fallback candidates are appropriate for recoverable availability or capacity problems: 5xx, 429, model unavailable/not_found/unsupported/deprecated/retired/disabled.
   - Do not fallback on invalid request bodies, invalid parameters, auth, or permission errors.
   - Candidate selectors should still pass model authorization.

4. **Streaming fast path and stream fallback boundary**
   - Stream requests are expensive to mediate and hard to recover after bytes have been written.
   - Fast path is safe only when provider is compatible and no selector/body rewrite or forced usage injection is required.
   - Fallback is safest before first byte; after partial token output, switching providers can duplicate or contradict content and corrupt usage attribution.

5. **Resolved-route observability**
   - Requested model, resolved model, response model, and pricing model may differ.
   - Audit and usage must record actual provider/model and failover target for debugging, cost attribution, and SLA analysis.

6. **Adapter/orchestrator boundary**
   - Orchestrator owns workflow, fallback, usage/audit/cache coordination.
   - Adapter owns provider-specific HTTP shape, auth headers, parameter translation, error normalization, and stream chunk parsing.
   - Router/selector logic should not become a dumping ground for provider quirks.

## Strong follow-up questions to drill

Prefer these over shallow inventory-cache questions:

```text
1. Why can requested model, resolved model, response model, and pricing model differ?
2. Why is slash-shaped model parsing dangerous?
3. Why should workflow policy be separate from handlers and adapters?
4. Which errors should trigger fallback, and which must not?
5. Why is streaming fallback unsafe after tokens have been sent?
6. What conditions allow streaming fast path?
7. What should audit/usage record after fallback?
8. Which logic belongs in the provider adapter versus the orchestrator?
```

## If asked: "Is this load balancing?"

Do not overstate it.

> Strictly speaking, the base version is model-based routing, not full load balancing. It selects a provider based on a resolved model/provider selector. A more advanced version would add candidate provider sets, health checks, priority/weight, latency/cost windows, circuit breakers, and error-aware fallback. The honest current value is that the routing path is structured so those governance features have a clean place to attach.

## Future routing strategy answer

A mature answer can propose this progression:

```text
static selector resolution
-> workflow policy context
-> fallback by error type
-> provider health and latency windows
-> priority/weight/cost-aware routing
-> circuit breaker and degraded-mode policy
-> observability-driven tuning
```
