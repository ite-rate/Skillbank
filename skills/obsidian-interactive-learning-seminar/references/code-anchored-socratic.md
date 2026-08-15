# Code-Anchored Socratic Learning

Use when the user wants deep technical learning about a system (AI Gateway, database internals, distributed systems, etc.) and has access to a real open-source codebase.

## Technique

1. Pick ONE real codebase as the anchor (e.g. GoModel for AI Gateway).
2. Start with the deepest design tension — a concrete architectural decision visible in the code, not a warm-up question about definitions.
3. Each question targets a specific line of code or a specific module boundary. Show the code snippet first, then ask the question.
4. After the user answers, correct precise errors (not just "wrong direction"), then immediately connect to the next module.
5. At module close: reading packet summary (clean paragraphs, no markdown tables), then closed-book oral compression challenge.
6. Every code-level claim MUST be verified against actual source files before stating it. If the user challenges a claim ("对比源码确定一下"), re-read the source immediately and correct honestly.

## Module Structure

Each module covers one subsystem:
- Module 1: Request lifecycle / translation layer
- Module 2: Provider routing and model resolution
- Module 3: Cache design (exact + semantic + stream)
- Module 4: Guardrails (prompt injection + LLM-based rewriting)
- Module 5: Fallback + circuit breaker

## Pitfalls

- Never present final summaries as markdown tables or heavy bullet-point dumps. Clean paragraphs, one design point per paragraph, line breaks between them.
- Never extrapolate code details from memory. If the user asks "is X in the code?", read the file.
- Don't let a module drag beyond 6-7 questions. The user wants depth, not volume.
