# Grilling-style plan stress-test

Use when the user wants a scheme/design/implementation approach challenged before execution, especially phrasing like:
- "grill this"
- "拷问这个方案"
- "评估方案会不会有坑"
- links to `https://www.skills.sh/mattpocock/skills/grilling`

External source note: Matt Pocock's `grilling` skill says to interview the user relentlessly about every aspect of a plan until shared understanding is reached; walk down each branch of the design tree, resolve dependencies one by one, ask one question at a time, provide a recommended answer for each question, and inspect the codebase when inspection can answer the question.

## Hermes adaptation

For this user's workflow, treat `grilling` as an extension of `receiving-code-review` beyond code:

1. Start with the decision under review, not a broad essay.
2. Ask one high-leverage question at a time.
3. Include a recommended/default answer after each question.
4. Use tools to inspect code/config/docs when the answer is retrievable; do not make the user restate facts that can be checked.
5. Track hidden dependencies and risks: compatibility, migration, observability, failure modes, rollback, cost, complexity, ownership, and YAGNI.
6. Close with:
   - accepted assumptions
   - unresolved assumptions
   - major risks
   - recommended path
   - smallest safe next step

## Prompt shapes

User can trigger with:

```text
用 grilling 的方式拷问这个方案：...
```

```text
Grill this design. Ask one question at a time and give your recommended answer for each question.
```

```text
站在上下文校验角度 review 一下这个设计，重点找副作用、隐含假设和 YAGNI。
```

## Distinguish from related skills

- Ponytail: primarily anti-overengineering / minimal implementation ladder.
- Grilling: plan interrogation and design-tree dependency resolution.
- Receiving-code-review: context validation and pushback discipline; use it as the umbrella for grilling-style reviews.
- Requesting-code-review: post-implementation diff review before commit.
