# Agora Shared Deliberation Protocol (8-Step)

> This protocol is referenced by every Room SKILL.md. Read it once at session start; do NOT re-read per round.

## Overview

Agora uses an 8-step deliberation sequence with evidence gathering, two strategic AskUserQuestion interaction points, adaptive depth, and Hegelian synthesis. This is an evolution of the Council 7-step protocol.

**Council (7 steps)**: Parse → Routing → Restate → R1 → R2 → Enforcement → R3 → Verdict
**Agora (8 steps)**: Parse → Evidence → Restate+★AskUser → R1 → ★AskUser+AdaptiveGate → [R2 or Skip] → Synthesis → Verdict

---

## STEP 0: Parse Mode + Select Panel

**Determine mode:**
- If `--quick` → QUICK MODE (2 rounds, no AskUser interactions, abbreviated)
- If `--duo` → DUO MODE (2-member dialectic, 3 rounds)
- Otherwise → FULL MODE (continue below)

**Select panel members:**
1. If `--triad [domain]` → look up triad from the Room's triad table
2. If `--members name1,name2,...` → use those members (2-6)
3. If `--full` → all members defined in the Room
4. If none → **Auto-Triad Selection**: read the problem, match against triad keywords, select best fit. State reasoning.
5. `--depth auto|full` → controls adaptive depth behavior (default: `auto`)

`[CHECKPOINT]` State selected members, mode, and Room identity before proceeding.

---

## STEP 1: Evidence Gathering (NEW — Room-Specific)

Each Room defines its own **Evidence Strategy** (mandatory vs optional, tool types).

**Execution:**
1. Read the Room's evidence strategy section
2. Execute the specified tool calls (Read, Grep, Glob, git log, WebSearch, etc.)
3. Compile an **Evidence Brief** — factual summary, max 500 words
4. If the Room marks evidence as "no external evidence" (e.g., /oracle, /hearth), the Coordinator writes a **Context Summary** from the user's problem statement instead

**Evidence Brief format:**
```
### Evidence Brief
- **Sources**: {list of tools used and what was found}
- **Key Facts**: {bulleted factual findings}
- **Gaps**: {what we looked for but couldn't find}
- **Relevance**: {how this evidence connects to the question}
```

`[CHECKPOINT]` Present Evidence Brief. If evidence is thin, note this — it affects confidence.

---

## STEP 2: Problem Restate + ★AskUserQuestion #1

### 2a: Agent Problem Restatement

**IMPLEMENTATION: Use the Agent tool — one call per panel member, all in a single message (parallel).**

```
Agent tool call per member:
  subagent_type: "{agent-name}"
  prompt: |
    The problem under deliberation:
    {problem}

    Evidence Brief:
    {evidence brief from Step 1}

    Restate this problem in TWO parts:
    1. **Your restatement**: One sentence capturing the core question through your analytical lens.
    2. **Alternative framing**: One sentence reframing the problem in a way the original statement may have missed.

    50 words maximum total. Do NOT begin analysis yet.

Fallback: if agent-name not a registered subagent_type, use "general-purpose" and prepend:
  "Read your agent definition at ~/.claude/agents/{agent-name}.md. Follow it precisely."
```

### 2b: ★AskUserQuestion — Dissolve or Confirm

**Skip conditions:** `--quick` mode

**Before presenting options, the Coordinator runs a silent problem quality check:**

**Problem Dissolution Check** — ask yourself:
- Is this a **pseudoproblem**? (A question framed as a choice that isn't really a choice, e.g., "Should I be happy?" "Should I care about what others think?")
- Is this an **XY problem**? (User asks about solution Y, but the actual problem is X — e.g., "How do I optimize this SQL query?" when the real problem is wrong schema design)
- Is the stated question a **symptom** of a deeper question? (e.g., "Should I change jobs?" when the real question is "I don't feel respected anywhere I go")
- Is the question **unanswerable as stated** due to missing context? (e.g., "Should I invest in crypto?" with no information about financial situation, goals, or risk tolerance)

**If any of these flags are raised**, the Coordinator must surface this BEFORE asking confirmation. Structure the AskUser presentation as:

```
We noticed: [specific issue — pseudoproblem / XY problem / symptom / missing context]

Before we begin deliberation, we want to check: is this the real question?

Panel members restated the problem differently:
- [Agent A]: [their restatement]
- [Agent B]: [their restatement — especially if diverges from original]

[If XY problem]: The real question might be: [state it directly]
[If pseudoproblem]: This question may dissolve when examined: [explain briefly]
[If symptom]: There may be a deeper question here: [name it]
```

**Tacit Signal Detection** — before presenting any options, scan the problem statement for: 就是那种感觉 / 说不清楚 / 像X那种风格 / 你懂的那种 / 不想要那种 / 感觉不对但说不出 / 差那么一点点...

If triggered: invoke `protocol/tacit-knowledge.md` flow. State to the user: "我注意到你的描述包含难以直接说清楚的感受，先把它变得清晰，审议会更准确。" Run the 3-step extraction (Exemplar → Anti-exemplar → Behavioral). Fold the resulting Tacit Knowledge Brief into the Evidence Brief and use the Articulated Requirement as the confirmed problem statement going forward. The tacit extraction does NOT consume one of the 2 AskUser interactions.

**Then offer options:**
1. "你说的对，真实问题是X，以X继续" (Reframe to the real question)
2. "不，我的问题就是我问的那个，继续" (Proceed with original)
3. "补充背景，帮你更准确理解" (Add context first)
4. "先告诉我你们看到了什么" (Show me the restatements — I'll decide)
5. "我说不清楚，但我知道一个'对的'例子" → triggers Polanyi tacit extraction protocol (see `protocol/tacit-knowledge.md`)

**If no flags are raised**, present normally:
- The Evidence/Context Brief summary (3 bullet points max)
- Each agent's problem restatement (1 line each)
- Question: "我们的理解准确吗？有需要补充的上下文吗？"
- Options:
  1. "理解准确，继续"
  2. "需要补充信息"
  3. "重新表述问题"

**Critical rule**: If a panel member's restatement diverges significantly from the original question, this MUST be surfaced to the user. A restatement divergence is often the most valuable signal — it reveals what the question looks like from outside the asker's frame.

If user selects any reframing option, integrate their input into the problem statement for all subsequent steps.

If Tacit Signal Detection was triggered and extraction was run, ensure the **Tacit Knowledge Brief** is recorded in the confirmed problem statement below.

`[CHECKPOINT]` Record confirmed/updated problem statement. Note whether the original question was dissolved, reframed, confirmed, or clarified via tacit extraction.

---

## STEP 3: Round 1 — Informed Independent Analysis (PARALLEL, BLIND)

Emit to user:
> **审议开始**: {member names}. Round 1 — 独立分析（含证据）.

**IMPLEMENTATION: Use the Agent tool to spawn all members IN PARALLEL in a single message.**

For each panel member, launch one Agent tool call simultaneously:

```
Agent tool call per member:
  subagent_type: "{agent-name}"   ← use the agent's registered name (e.g. "council-aurelius", "agora-frankl")
  prompt: |
    You are operating as a panel member in a structured Agora deliberation.

    The problem under deliberation:
    {confirmed problem statement}

    Evidence Brief:
    {evidence brief}

    Member restatements:
    {all restatements from Step 2a}

    Produce your independent analysis using your Output Format (Standalone).
    Ground your analysis in the Evidence Brief where relevant.
    Do NOT try to anticipate what other members will say.
    Limit: 400 words maximum.
```

**All Agent calls must be emitted in a SINGLE message to run in parallel.**
Wait for all to complete before proceeding.

**Fallback (if an agent-name is not a registered subagent_type):**
Use `subagent_type: "general-purpose"` and prepend to the prompt:
```
Read your agent definition at ~/.claude/agents/{agent-name}.md.
Follow it precisely. Then respond to the deliberation below.
```

`[CHECKPOINT]` Confirm all Round 1 outputs collected. Verify ≤400 words each.

---

## STEP 4: Adaptive Depth Gate + ★AskUserQuestion #2

### 4a: Consensus Assessment

The Coordinator evaluates Round 1 outputs:
- **HIGH consensus (>80%)**: Most members converge on same recommendation
- **MEDIUM consensus (60-80%)**: General direction aligned but meaningful disagreements
- **LOW consensus (<60%)**: Fundamental disagreements on approach or framing

### 4b: ★AskUserQuestion — Depth Decision

**Skip conditions:** `--quick` mode OR `--depth full`

**The Coordinator's presentation must be honest about what Round 1 actually produced.** Do NOT just list positions — tell the user what kind of question this is:

**If HIGH consensus**: "The panel largely agrees on X. The disagreements are about Y (detail/implementation/emphasis), not about the core direction. Accepting now is reasonable."

**If MEDIUM consensus**: "The panel splits between X (majority) and Y (minority). The minority position has merit: [state it honestly in 1-2 sentences]. Going deeper is likely to surface something useful."

**If LOW consensus**: "The panel is genuinely divided. This is not a question with a clear answer — it's a question with real tradeoffs that deserve examination. Skipping Round 2 here means accepting one side without understanding the other."

Present:
- Round 1 summary: each member's core position in 1 sentence (honest, not sanitized)
- The strongest dissenting view (even if it's a minority of 1)
- Consensus assessment with honest framing (see above)
- Question: "怎么继续？"
- Options (label them with what they actually mean):
  1. "够了，接受主流方向" — Accept the majority direction, skip to verdict
  2. "有真正的张力，深挖" — Something important is unresolved, go to Round 2
  3. "直接给我结论" — I want a verdict now, using Round 1 data as-is
  4. "我有新信息要补充" — I have context that changes the picture; I'll share it, then continue

**Auto-decision (when `--depth auto` and no user interaction):**
- HIGH consensus → default to option 1 (Accept)
- MEDIUM consensus → default to option 2 (Deep dive)
- LOW consensus → default to option 2 (Deep dive)

`[CHECKPOINT]` Record depth decision.

---

## STEP 5: Round 2 — Hegelian Cross-Examination

> Only reached if Step 4 selects "Deep dive" or `--depth full`.

Emit to user:
> **Round 2 — 黑格尔正反合交叉审查开始.**

### Coordinator Framing

Before dispatching, the Coordinator MUST:
1. Identify **Thesis** (majority position from Round 1)
2. Identify **Antithesis** (strongest minority/dissenting position)
3. State both clearly to all members

### Dispatch to Members

**IMPLEMENTATION: Use the Agent tool — one call per panel member, all in a single message (parallel).**

```
Agent tool call per member:
  subagent_type: "{agent-name}"
  prompt: |
    You are in Round 2 of an Agora deliberation.

    **The Dialectic:**
    - THESIS (majority): {thesis statement}
    - ANTITHESIS (minority): {antithesis statement}

    Here are the Round 1 analyses from all panel members:
    {all Round 1 outputs}

    Respond using your Output Format (Council Round 2) with one CRITICAL addition:

    ### Synthesis Proposal
    {You MUST propose a synthesis that transcends both thesis and antithesis.
    You may NOT simply pick a side. Find the higher truth that integrates both.}

    Rules:
    - You MUST engage at least 2 other members by name
    - You MUST propose a synthesis (not just pick thesis or antithesis)
    - Limit: 300 words maximum

Fallback: if agent-name not a registered subagent_type, use "general-purpose" and prepend:
  "Read your agent definition at ~/.claude/agents/{agent-name}.md. Follow it precisely."
```

### Enforcement Scan

Run all checks on Round 2 outputs:

**`[VERIFY]` Dissent quota**: ≥2 members must articulate non-overlapping objections. If fewer → send dissent prompt (150 words).

**`[VERIFY]` Novelty gate**: Each response must contain ≥1 new claim/test/risk/reframe not in their Round 1. If missing → send back for revision.

**`[VERIFY]` Synthesis check** (NEW): Each member must have a Synthesis Proposal section. If missing → send back:
```
Your Round 2 response picks a side without proposing synthesis. How can both thesis and antithesis be partially right? What higher-order principle integrates them? 100 words.
```

**`[VERIFY]` Agreement check**: If >70% agree → trigger counterfactual to 2 likely dissenters.

`[CHECKPOINT]` Confirm all Round 2 outputs collected and verified.

---

## STEP 6: Coordinator Synthesis

> The Coordinator synthesizes directly (no Round 3 — unlike Council).

The Coordinator produces:
1. **Hegelian Arc**: Thesis → Antithesis → Synthesis (3-5 sentences each)
2. **Convergence Points**: Where most members agreed
3. **Irreconcilable Tensions**: Genuine disagreements that can't be resolved
4. **Confidence Assessment**: Based on evidence quality + consensus level + argument strength

`[CHECKPOINT]` Synthesis complete.

---

## STEP 7: Room-Specific Verdict

Each Room defines its own Verdict template. The Coordinator fills it using:
- Evidence Brief (Step 1)
- Confirmed problem statement (Step 2)
- Round 1 analyses (Step 3)
- Round 2 syntheses (Step 5, if reached)
- Coordinator synthesis (Step 6)

At the end of every verdict, append:

```
### 相关审议室
{Suggest 1-2 other Rooms that might offer complementary perspectives. E.g., "Also consider: /bazaar (商业维度) or /clinic (心理韧性)"}

### 后续追踪
实施后回顾：这个裁决有帮助吗？采取了什么行动？结果如何？
```

---

## Quick Mode Sequence

Abbreviated 2-round flow. No AskUser interactions. No evidence gathering.

### QUICK STEP 0: Select Panel
Same as full mode Step 0.

### QUICK STEP 1: Round 1 — Rapid Analysis (PARALLEL)
```
You are a panel member in a rapid Agora deliberation.
Read your agent definition at ~/.claude/agents/{agent-name}.md.

The problem: {problem}

In ONE sentence, restate this problem through your lens. Then:
- Essential Question (1-2 sentences)
- Core analysis (key insight only)
- Verdict (direct recommendation)
- Confidence (High/Medium/Low)

Limit: 200 words maximum. Be decisive.
```

### QUICK STEP 2: Round 2 — Final Positions (PARALLEL)
```
Here are the other members' analyses:
{all Round 1 outputs}

Final position in 75 words or less. Note key disagreements. Be direct.
```

### QUICK STEP 3: Synthesize Quick Verdict
Use Room's Quick Verdict template.

---

## Duo Mode Sequence

Two-member dialectic, 3 rounds.

### DUO STEP 0: Select Pair
1. If `--members name1,name2` → use those two
2. Otherwise → match against Room's polarity pairs, select best fit
3. State the pair and the tension

### DUO STEP 1: Opening Positions (PARALLEL)
```
You are one half of a structured dialectic.
Read your agent definition at ~/.claude/agents/{agent-name}.md.

The problem: {problem}

Restate in ONE sentence through your lens. Then state your position using Output Format (Standalone).
Limit: 300 words.
```

### DUO STEP 2: Direct Response (PARALLEL)
```
Your opponent ({other}) argued:
{other's Round 1}

1. Where are they wrong? Engage specific claims.
2. Where are they right? Concede what deserves it.
3. Restate your position, strengthened.

Limit: 200 words.
```

### DUO STEP 3: Final Statements (PARALLEL)
```
Final statement. 50 words maximum. No new arguments.
```

### DUO STEP 4: Synthesize Duo Verdict
Use Room's Duo Verdict template.
