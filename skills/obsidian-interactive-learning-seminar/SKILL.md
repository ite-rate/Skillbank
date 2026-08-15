---
name: obsidian-interactive-learning-seminar
description: Guide a user through an Obsidian-based interactive learning vault by extracting the reading sequence, converting notes into mobile-friendly study prompts, and coaching seminar answers.
level: manual
native_agent: Hermes
---

# Obsidian Interactive Learning Seminar

Use this when the user has an Obsidian vault organized as a learning/research workflow (for example: Topic -> Source Pack -> Evidence -> Seminar) and wants help deciding what to study, wants the materials sent in reading order, or wants their seminar answers critiqued.

## When to use
- User says they created an Obsidian vault for study / interactive research.
- User is away from their computer and wants reading materials sent in chat.
- User has already answered seminar questions and wants feedback, grading, or a stronger rewritten answer.
- Vault contains staged notes such as `01-Research-Topics`, `02-Sources`, `03-Research-Notes`, `04-Seminars`.
- User is doing code-anchored system-design learning with a real codebase (e.g. GoModel, Hermes).

## Feishu formatting
- Keep chat messages flat and scannable. No big code blocks, no nested ASCII diagrams.
- Full detail, code snippets, and comprehensive notes go to vault — NOT to chat.
- Prefer short tables, single-level lists, and inline code (not fenced blocks) in Feishu.
- When user says "太浅了" or "直接进入核心", skip ontology/prediction warm-up gates entirely.
- Jump to concrete architectural questions anchored in the actual codebase being studied.

## Writing to vault
- Prefer terminal `cat` heredoc for writing to vault files. write_file may not persist reliably.
- Verify writes with `ls` after creation.
- User may have multiple vaults (e.g. interactive-learning-vault and interactive-system-design-vault).
- ALWAYS confirm which vault the user is looking at before claiming files exist there.

## Workflow

### 1. Locate the vault and relevant notes
Use `search_files(target='files')` to find the vault and study files by filename keyword.
Common sequence to look for:
- `01-Research-Topics/<topic>.md`
- `02-Sources/<topic>-source-pack.md`
- `03-Research-Notes/<topic>-evidence-*.md`
- `04-Seminars/<topic>-seminar-*.md`

### 2. Read in dependency order
Always read the notes in this order before advising the user:
1. Topic page
2. Source pack
3. Evidence notes
4. Seminar note

Reason: the seminar questions often depend on distinctions introduced in the evidence notes; do not jump straight to seminar critique.

### 3. Produce a mobile-friendly reading packet
If the user is on phone / away from computer:
- Do **not** dump raw markdown with file paths and frontmatter unless asked.
- Convert each note into a short readable section with headings like:
  - Topic
  - Current research question
  - Key hypothesis
  - Evidence 1 / 2
  - Seminar prompt
- Preserve the intended reading order.
- End each section with a one-sentence takeaway such as “What to remember from this page”.

### 4. Recommend what to study today
When the user asks what to read today:
- Prefer the smallest coherent unit that completes one loop of understanding.
- Usually that means: topic page -> source pack -> first 1-2 evidence notes -> current seminar.
- Tell the user what **not** to read yet if the vault itself is trying to avoid premature synthesis or comparison.

### 5. Critique seminar answers like a tutor
When the user submits answers:
- Evaluate whether they identified the model’s core distinction correctly.
- Separate:
  - correct direction
  - missing nuance
  - over-hasty conclusions
- Provide:
  1. brief overall assessment
  2. per-question corrections
  3. a stronger rewritten answer the user could submit

### 6. Persist the result back into the vault
If the user wants the work "held onto", "saved", or "persisted", do not leave the improved answer only in chat.
- Read the current seminar note section first.
- Patch the corresponding `04-Seminars/<topic>-seminar-*.md` file.
- Preserve both:
  - the user's original answer (summarized or quoted as raw answer)
  - the corrected / strengthened rewritten answer
- Add a short "current takeaway" or "this round takeaway" section if useful.
- Re-read the edited section to verify the write actually landed.

### 7. Follow the vault's research-flow protocol before choosing the next step
If the user asks "what next" or asks for the correct next stage, inspect the vault protocol files (for example `99-Protocols/research-flow.md`) instead of guessing.
Typical rule pattern:
- Topic -> Source Pack -> Evidence -> Seminar -> Deliberation -> Synthesis -> Permanent Note
Important consequence:
- Do not jump from seminar straight to synthesis when the current seminar has raised a strong, contestable claim with unresolved boundary questions.
- If the seminar contains meaningful controversy, practical stakes, or open boundary disputes, the next step is usually **Deliberation**.

### 8. Persist full research progression, not just seminar feedback
Once the user explicitly wants the work persisted into the vault, do not stop at patching the seminar note if the protocol has already advanced.
Use the protocol stage to decide which files should now exist and create/update them in order:
- boundary dispute after seminar -> create `05-Deliberations/<topic>-deliberation-01.md`
- stable stage conclusion after deliberation -> create `06-Synthesis/<topic>-synthesis-01.md`
- transferable conclusions only -> create one or more `07-Permanent-Notes/<topic>-*.md`

Rules:
- seminar stores the user's answer + improved answer + current takeaway
- deliberation stores the contested claim, both sides, blind spots, boundary conditions, and tightened ruling
- synthesis stores the current most-stable judgment, dependencies, strongest counterexamples, practical use, and unresolved questions
- permanent notes must keep only durable, reusable judgments — no process recap, no chat transcript, no temporary coaching commentary
- after each write, re-read the target file section to verify the content actually landed

### 9. When the user asks for “original-text-based” clarification, create a new evidence note
If the user asks a focused conceptual question such as “what does the third factor really mean” or asks for a judgment "based on the original text":
- go back to the source document, not just existing vault notes
- extract the relevant original wording / anchor passages
- answer the question from those anchors
- then persist the result as a new `03-Research-Notes/<topic>-evidence-0N.md` when it materially extends the topic

Use this especially when the new question resolves one of the unresolved edges already listed in synthesis, such as:
- concept boundary clarification
- variable-role distinction
- mapping between model and implementation recipe
- edge cases or misreadings

**Practical source-handling rule:** if the primary source is a local `.mobi` / ebook and ordinary text extraction is flaky, do not give up and do not stay at the vault-note level.
Use a fallback like this:
- search the ebook bytes for stable anchor keywords (`prompt`, `Anchor`, `Celebration`, chapter titles, etc.)
- extract a byte window around the match
- when the text looks mojibaked, decode with `latin1 -> utf-8` recovery
- use the recovered snippet only as a short anchor passage, not a long dump
- explicitly distinguish `原文` vs `推测` in the new evidence note

This is worth doing when conversion tools fail but the user explicitly wants an answer grounded in the source text.

### 10. Add learner-turn gates when the vault devolves into passive LLM outlining
If the user says the vault is becoming “LLM keeps pushing, I just click continue” or that they only retain outlines but not details, treat this as an interaction-protocol failure, not a content-volume problem.

Before adding more notes or expanding more nodes, recommend or add a lightweight gate protocol:
1. **Prediction gate** — before explanation, ask the learner to guess why the mechanism/design exists.
2. **Recall gate** — after a small explanation, require the learner to restate it in their own words; never accept “懂了/continue” as evidence.
3. **Counterexample gate** — ask where the explanation breaks, what it does not solve, or what boundary case exposes the tradeoff.
4. **Transfer gate** — give a small scenario that requires applying the concept outside the exact note wording.
5. **Closed-book compression gate** — before settling, require the learner to write a 30-second answer first; then critique and rewrite.

Persist learner traces, not only polished synthesis. For each stabilized node or seminar, prefer sections such as:
- `学习者预测`
- `学习者原始复述`
- `纠偏记录`
- `迁移题`
- `闭卷 30 秒答案`
- `下次召回问题`

For project-style learning vaults with runtime state files, add an interaction cursor when useful:
```yaml
interaction:
  mode: coaching
  current_gate: learner_prediction | learner_recall | transfer_test | closed_book_compression | settle
  learner_turn_required: true
  instruction_to_ai: "不要继续讲解；先等待用户产出。"
```

Hard rule: when `learner_turn_required: true`, the assistant may only wait, simplify the prompt, or give a tiny hint. It must not continue the full explanation, auto-summarize, settle, or advance to the next node.

### 10. Important coaching heuristic
Watch for the user collapsing all failures into “motivation problems.”
If a framework like Fogg distinguishes motivation / ability / prompt, explicitly check whether the user has confused:
- wanting to do the target behavior
- being able to execute the action chain in context
- being triggered at the right time

In scenario analysis, avoid over-classifying too early. If the visible facts do not isolate one variable, answer: **“not suitable for direct judgment; needs further decomposition.”**

### 11. Add interaction gates when the vault turns into passive outline pushing
Use this when the user says the learning vault is becoming “LLM pushes, I click continue,” or when polished notes exist but the learner is not retaining details.

Do **not** solve this by adding more outlines, more topic nodes, or rewriting old notes. Prefer a new isolated test project/folder first.

Recommended gated-learning structure:
- keep the proven runtime skeleton: `WORKSPACE.md`, `WORKSPACE.yaml`, `STATE.yaml`, `CURRICULUM/MODEL.md`, `METHOD/PROTOCOL.md`, `NODES/INDEX.md`, `RUNTIME/events.ndjson`
- add `METHOD/INTERACTION_GATES.md` as the central protocol
- add `METHOD/TEMPLATES/gated-node.md` for nodes that preserve learner evidence
- keep legacy projects untouched unless the user explicitly asks for migration

Core gate sequence:
1. **Prediction gate** — before explanation, ask the learner to predict why the mechanism exists.
2. **Minimal explanation gate** — explain one small mechanism only; no broad outline dumping.
3. **Recall gate** — require the learner to restate in their own words; then critique right part / missing part / improved version.
4. **Transfer gate** — require applying the mechanism to a scenario, boundary, or counterexample.
5. **Closed-book compression gate** — learner writes the 30-second answer first; assistant critiques after.

Add an explicit `interaction` brake to `STATE.yaml`:
```yaml
interaction:
  mode: gated_coaching
  current_gate: prediction
  learner_turn_required: true
  no_auto_continue: true
  last_prompt_to_user: null
  last_user_answer: null
  last_gap: null
```

Hard stop rule: if `learner_turn_required: true`, the assistant may only wait, make the prompt smaller, or give one small hint. It must not continue the explanation, start a new node, settle, generate a full outline, or fill in the learner’s answer.

Node templates should preserve learning traces, not only polished conclusions:
- `学习者预测`
- `学习者原始复述`
- `纠偏记录`
- `迁移题`
- `闭卷 30 秒答案`
- `稳定版本`

## Output patterns

### A. Reading recommendation
Use this structure:
- Today’s focus
- Reading order
- Main question to keep in mind
- What not to branch into yet

### B. Mobile reading packet
Use this structure:
- 1) Topic page
- 2) Source pack
- 3) Evidence 01
- 4) Evidence 02
- 5) Seminar

### C. Seminar feedback
Use this structure:
- Overall assessment
- What you got right
- What needs correction
- Revised answer

## Feishu-style project-first coaching for code/system-design interview vaults

Use this variant when the user says a Feishu/chat learning thread felt successful, wants the terminal/vault experience to match that style, or the goal is interview-ready programming/system-design understanding rather than research-note progression.

Key lesson: the successful pattern is often **not** more protocol. It is a stable mini-project mainline plus adaptive coaching. Do not expose gates/protocols to the learner unless they explicitly ask. Avoid letting vault maintenance interrupt the learning flow.

Default approach:
1. First inspect the successful chat/session if available and identify why it worked.
2. If the success pattern is project-first and code-anchored, create or switch to a very small project folder instead of adding more METHOD/GATE files.
3. Minimal structure is usually enough:
   - `README.md` — goal and learning style
   - `MAINLINE.md` — the project request/module chain
   - `STATE.yaml` — current module, current coaching mode, next prompt
   - optional `NODES/INDEX.md` only if the user still wants later stable module cards
4. Delete or avoid `NOTES/`, `DRILLS/`, protocol directories, and gate templates unless the user wants them. If the user says “align with Feishu,” bias toward fewer files.
5. Use a code/interview module card when the user says “继续主线”:
   - module role
   - chain position
   - inputs and outputs
   - interface / struct / function shape
   - minimal code skeleton
   - common wrong implementation
   - failure cases / real bugs
   - tradeoffs
   - interview wording
   - next module
6. Switch modes implicitly from the user's message:
   - "没听懂/黑话多" -> analogy + term translation + one-line memory anchor
   - "太浅了/直接进入核心" -> **skip all warm-up and prediction gates.** Jump to an architectural design question anchored in concrete code: "why does X layer exist? What breaks without it?" not "what is X?" The user already knows the category; the coaching value is in the design tension.
   - "先解释一下相关的基础知识/我不知道这个概念" -> **pause the Socratic flow.** Give a concise factual explanation grounded in the codebase, then resume with the original question. Don't force the learner to guess a concept they haven't seen.
   - user gives their understanding -> correct only 1-2 key points, then interview wording
   - "具体怎么做" -> bad implementation -> robust design -> code shape -> failure path -> tradeoff
   - "面试怎么说" -> 30-second / 1-minute / follow-up versions
7. Persist only after a module stabilizes. During live learning, conversation continuity beats note completeness.
8. Full code-anchored Socratic pattern: see `references/code-anchored-socratic-learning.md`.
9. Annotated pipeline diagram: when the learner asks for a \"chain\" or \"pipeline\" with function-level detail, produce a clean vertical flow diagram using `──` Unicode box-drawing, annotated with file:line references. Avoid nested ASCII art. Prefer this format:

```
Layer Name
──────────────────────────────────────────────────
Description
──────────────────────────────────────────────────
functionName() — file.go:line
  ├─ substep
  └─ substep
```

Push the final diagram to vault as a numbered module file (e.g. `07-完整链路函数级.md`). See `references/ai-gateway-gomodel-learning-map.md` § 模块 7 for the worked example.

Example minimal mainline for a mini agent runtime:
```text
message entry
-> request/session context
-> context builder
-> model call
-> tool dispatch
-> observation loop
-> memory/skills persistence
-> audit/usage/logs
-> response delivery
```

## Redis engineering scenario drills for interview/system-design vaults

Use this variant when the user wants Redis learning to include high-frequency 牛客/面经/NeetCode-style interview topics while avoiding shallow “Redis = cache / hot data” memorization.

Detailed reference: `references/redis-engineering-scenarios.md`.

## AI Gateway 深度学习

Use this variant for code-anchored, Socratic deep-dives into AI Gateway architecture (GoModel as reference). Detailed learning map with module breakdown, key questions, and architecture quick-reference: `references/ai-gateway-gomodel-learning-map.md`.

Default approach:
1. Prefer a separate project folder such as `Projects/redis-engineering-scenarios/` instead of adding more concept nodes to an already-completed Redis core project.
2. Convert interview-bank themes into engineering scenario cards rather than copying raw question text.
3. Each card must require: business pressure, Redis role, concrete key/value/TTL, data structure choice, read path, write path, failure modes, and a 30-second oral interview answer.
4. When creating or updating a `主线地图` / interview mainline file, do **not** leave it as a bare table of contents. For each topic, include at least: `5关键词`, `20–30秒口语版`, `常见追问`, and `易错点`. The user may treat “主线没有内容啊” as a correction that the map is not usable for review.
5. During live review, start with a small closed-book learner turn: ask for the 5 keywords or a short answer first, then correct only the missing pieces and compress into a 20–30 second answer. Do not dump the full polished answer before the learner's first attempt unless they explicitly ask.
6. After correction, persist the stable version back into the scenario note or mainline file when the repo/vault is the source of truth.

Good seed topics include: device online state and massive reconnect, session runtime progress, message dedup/idempotency, Redis distributed lock design, cache breakdown/penetration/avalanche, MySQL-Redis consistency, rate limiting, seckill stock pre-deduct, ZSet leaderboard, hot-key governance, delayed task with ZSet/Stream, WebSocket connection map, and payment callback idempotency.

## Gated learning workspaces for system-design / interview vaults

Use this variant only when the user explicitly wants learner-turn gates, closed-book checks, or the Feishu-style project-first approach still devolves into passive clicking. Do not use it as the default for programming/interview coaching.

Default approach:
1. Do **not** rewrite or batch-migrate existing projects first.
2. Create a new isolated project folder, e.g. `Projects/<topic>/`, to test the improved protocol.
3. Borrow the lightweight runtime structure from existing successful projects when present:
   - `WORKSPACE.md`
   - `WORKSPACE.yaml`
   - `STATE.yaml`
   - `CURRICULUM/MODEL.md`
   - `METHOD/PROTOCOL.md`
   - `METHOD/INTERACTION_GATES.md`
   - `METHOD/TEMPLATES/<node-template>.md`
   - `NODES/INDEX.md`
   - `RUNTIME/events.ndjson`
4. Keep global/system prompts short. Put the anti-auto-continue behavior in project-local `INTERACTION_GATES.md` and `STATE.yaml.interaction` instead of bloating old global instructions.
5. Add a hard stop field to `STATE.yaml`:
   ```yaml
   interaction:
     mode: gated_coaching
     current_gate: prediction
     learner_turn_required: true
     no_auto_continue: true
     last_prompt_to_user: ...
     last_user_answer: null
     last_gap: null
   ```
6. If `learner_turn_required: true`, the assistant may only wait, shrink the question, or give one small hint. It must not continue explanation, generate a broad outline, start a new node, or settle the node.
7. A node should not become stable until the learner has produced evidence for these gates. If the user says the protocol still feels like feature-listing rather than first-principles learning, upgrade the gate order from `prediction -> explanation` to:
   - ontology: learner identifies what kind of system/object this is, e.g. LLM vs Agent
   - pressure: learner explains what breaks if the system stays in the weaker/previous form
   - mechanism: assistant explains the smallest mechanism that grows out of that pressure
   - recall: learner restates in their own words
   - transfer: learner applies it to a scenario/boundary/counterexample
   - closed-book compression: learner writes the 30-second answer first
   Example: for Hermes, do not start with “session/tools/skills/memory.” Start with `LLM = context-conditioned generator/reasoner` vs `Agent = stateful action system using an LLM inside a runtime loop`; then derive why runtime, tools, memory, skills, and session must exist.
8. For implementation, use the Superpowers-style sequence when available:
   - brainstorm/spec first
   - write an implementation plan
   - execute the plan exactly
   - verify file scope and gate state
   - avoid committing if the vault already has unrelated dirty changes unless the user asks

## Pitfalls
## Pitfalls
- **Feishu / chat brevity rule:** When coaching on messaging platforms (Feishu, Telegram, etc.), keep each message short — one question, one correction, or one short explanation. Never dump long code blocks or multi-paragraph explanations in chat. Push full module notes, code excerpts, and detailed explanations to the Obsidian vault. The chat is for live Socratic interaction; the vault is for reading/review.
## Pitfalls
- Don't jump straight to "summary of the whole book" if the vault is designed as staged inquiry.
- Don't flatten evidence and seminar into generic self-help advice.
- Don't assume "has equipment" means "has ability"; ability may fail at an earlier action in the chain.
- Don't turn every ambiguous case into a clean single-variable diagnosis.
- Don't respond to "LLM is pushing me to click continue" by adding more outline templates.
- Don't automatically add hard gates for programming/interview learning if the user points to a successful Feishu-style conversation; first try a minimal project-first mainline with implicit coaching modes.
- Don't keep `NOTES/`, `DRILLS/`, or extra protocol folders just because they seem useful; if the user wants Feishu alignment, remove unnecessary structure.
- Don't refactor old vault material when the user asks to test a new protocol in a fresh folder.
- Don't dump dense code blocks or nested diagrams into Feishu chat. Full detail goes to vault.
- Don't open with shallow prediction gates ("what do you think X is") if the user signals they want depth. Jump to architectural questions anchored in real code.
- Don't assume which vault the user is looking at. Verify with `ls` or ask before claiming files are visible.

## Code-anchored learning project structure

When anchoring a learning topic on a real production codebase (e.g. GoModel for AI Gateway), use this minimal project structure:

```
Projects/<topic>/
├── README.md        — goal + learning style + code anchor path
├── MAINLINE.md      — module checklist (✅/🔄/⏳)
├── STATE.yaml       — {module, topic, status, current_question}
├── 01-<module>.md   — one per module
├── 02-<module>.md
└── ...
```

See `references/ai-gateway-learning-project-structure.md` for a worked example. This pattern was validated on a 5-module deep-dive into GoModel covering request lifecycle, model discovery, caching, guardrails, and fallback+circuit-breaking.
- **Don't start with shallow warm-up questions** (e.g. "what's your intuition about X"). The user may respond "太浅了直接进入核心" — this is a correction, not a negotiation. Start with the deepest design tension immediately. Use a real codebase as anchor (e.g. GoModel source) and ask about the specific architectural decisions visible in the code.
- **Stay on the learner's current question, not the module outline.** When the learner says "我疑惑的是 X 为啥要根据 Y, 你给我一直讲 Y 的规则" — stop. They're telling you that YOU expanded the scope when they wanted a focused answer. Answer the narrow question first, then ask if they want the broader topic. Do not preemptively dump the full module.
- **When the learner asks "先解释下 X" before a challenge question, keep the explanation grounded in the actual codebase.** If learning is anchored on a real project (e.g. GoModel), point to the specific source file and line. Don't give textbook definitions — show what the code does and why.
- **Don't present summaries in markdown tables or heavy bullet-point dumps.** The user may call this out as "格式不对 重新返回 看着很难受". Prefer clean paragraph-based summaries with minimal formatting — one or two short sentences per design point, line breaks between points, no tables, no fenced code blocks, no ASCII diagrams. The final module summary should read like a concise explainer, not a reference table.
- **Never claim a code-level detail without verifying it against actual source files.** The user may challenge "你刚才可没说...在对比源码确定一下" — this is a serious workflow correction. If you assert something is in the code, you must have read the relevant file. Extrapolating from memory or general principles is not acceptable. When challenged, immediately re-read the source and correct yourself honestly.
- **Don't start with soft warm-up / "what do you think X is" questions when the user signals they want code-level depth immediately** (e.g. "太浅了 直接进入核心" / "skip the basics / go straight to the core"). Drop the Socratic warm-up and open with a concrete, code-anchored question that assumes prior context.
- **Don't use `write_file` to write into an Obsidian vault; it may report success but not actually persist to disk.** Instead use `terminal` with `cat > path << 'ENDOFFILE' ... ENDOFFILE`. Always verify with `ls` after writing. If the user says "根本没有" after you claimed the files exist, re-verify immediately and rewrite with terminal.
- **Before writing learning notes to a vault, confirm which vault the user is actually looking at in Obsidian.** The user may have multiple vaults (e.g. `interactive-learning-vault` and `interactive-system-design-vault`) and files written to the wrong one won't appear. Ask or check the Obsidian window title / current vault name before writing.
- **When the user asks "先解释一下 X 的基础知识" before a challenge question, explain first then challenge.** Don't push a Socratic question when the learner explicitly says they lack the prerequisite concept. The "预测 → 解释" gate only works when the learner HAS a mental model to predict from.

## Verification
Before finishing, check:
- Did you preserve the vault’s study sequence?
- Did you keep distinctions introduced by the source/evidence notes?
- Did you provide actionable, phone-readable content if the user lacked computer access?
- Did your critique improve the user’s answer instead of merely judging it?
