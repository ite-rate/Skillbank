---
name: research-kickoff
description: Use when the user wants to start an open-ended research-paper direction discovery task, especially from a vague idea, cross-domain mechanism transfer, or "help me find a paper direction" request. Do not use for already-scoped paper edits, final submission cleanup, direct manuscript writing, or runtime task orchestration.
level: manual
native_agent: ClaudeCode
---

# Research Kickoff

Use this skill to turn a vague research intention into a strong first prompt for open-ended research direction exploration. The output is a kickoff prompt, not a research plan, paper draft, execution workflow, or final direction choice.

## Purpose and Boundary

This skill does:

- collect the user's existing research base;
- clarify the external mechanism or field the user wants to borrow from;
- capture what must not be misunderstood;
- preserve room for broad early exploration;
- ask for multiple candidate directions before narrowing;
- include lightweight scientific caution without over-constraining the next agent;
- produce a copy-ready kickoff prompt for a new agent/session.

This skill does not:

- decide the final research direction;
- write the paper;
- design full experiments;
- run literature review;
- prescribe internal files or procedures for downstream workflow skills;
- replace `paper-guardrails`;
- front-load execution-stage constraints such as detailed workspace layout, fixed venues, strict kill criteria, or mandatory workflow routing unless the user explicitly asks for a later-stage prompt.

## Conversation Protocol

Ask at most 3 questions per turn. Prefer one focused question when possible.

Resolve low-risk gaps with reasonable assumptions. Ask only when the answer materially changes the kickoff prompt.

Do not ask the user to know final methods, baselines, figures, venues, or exact validation plans at kickoff time. The goal is to gather enough context to let the next agent explore.

If the user asks to start from scratch, ask only the missing parts from this set:

1. What is your existing research base: domain, methods, available code/data/simulator, and prior results?
2. What external idea family or mature engineering practice do you want to borrow from, and what should the agent not misunderstand?
3. What boundaries should the next agent avoid crossing, such as pure trend-chasing, high-cost experiments, abandoning existing artifacts, or changing domains too aggressively?

## Information to Gather

Gather five categories:

- **Research base:** domain, methods, prior work, code, data, simulators, hardware, or constraints.
- **External idea source:** field, method family, engineering practice, or system pattern to borrow from.
- **Forbidden interpretation:** the most likely wrong framing the next agent must avoid.
- **Exploration latitude:** how far the agent may roam from the user's current base.
- **Loose direction criteria:** what feels promising, too expensive, too incremental, too theoretical, or too trend-driven.

Do not require all details before drafting. Use assumptions when the user has given enough context.

## Stage Discipline

Default to an early-stage exploration prompt. At this stage, avoid heavy process requirements that can reduce idea quality.

Include only light guardrails:

- explore before converging;
- do not start writing the paper;
- do not force the idea into a trendy label;
- do not claim confirmed novelty before nearby-work checking;
- keep validation descriptions minimal and provisional;
- recommend next exploration or low-cost validation targets without treating them as final.

Only add runtime handoff, detailed workspace organization, screening matrices, fixed kill criteria, or `paper-guardrails` instructions when:

- the user explicitly asks for a stricter second-stage prompt;
- the user's direction is already narrowed to 1-2 candidates;
- the user asks to begin execution, validation, experiment design, or paper planning.

## Direction Discovery Requirements

The generated kickoff prompt should ask the next agent to freely explore before converging. Prefer 5-8 candidate directions when the user is at the beginning of ideation. Use 3 directions only when the user already supplied a narrow topic.

Each direction should include:

1. core idea;
2. borrowed mechanism or analogy;
3. possible task background;
4. possible paper contribution;
5. minimal validation sketch;
6. largest risk;
7. nearby work areas to check.

For cross-domain mechanism transfer, the prompt should ask the next agent to reason about the underlying transferable structure, not just copy the surface label. Examples:

- budget management may transfer as adaptive allocation of compute, sensing, communication, exploration, or coordination effort;
- MoE may transfer as expert policies, role-conditioned controllers, scenario routers, or risk-aware subpolicies;
- verifier/self-evaluation may transfer as failure detection, policy selection, safety checks, or correction triggers;
- adaptive inference may transfer as spending more decision resources on hard states and less on easy states.

The prompt should ask the next agent to sort candidates into:

- most worth exploring further;
- interesting but high-risk;
- likely just concept-stacking or trend-chasing.

The prompt should recommend 1-2 directions for deeper literature checking or low-cost validation, without treating them as final.

## Scientific Caution

Keep this light in first-stage prompts:

- Do not claim confirmed novelty before nearby-work checking.
- Do not overstate that a direction is a "research gap"; mark it as a hypothesis.
- Do not start writing the paper.
- Do not force the user's idea into a trendy label.
- Do not require full baselines, metrics, venues, or kill criteria unless the user asks for a stricter second-stage prompt.
- Ask the user before shifting completely away from their existing research base or proposing high-cost experiments as the main path.

## Output Format

After enough information is gathered, output:

1. **Assumptions**
   - Briefly list assumptions used because the user did not specify details.

2. **Copy-Ready Kickoff Prompt**
   - Provide one prompt the user can paste into a new agent/session.
   - Write in the user's language unless asked otherwise.
   - Focus on broad direction discovery, mechanism transfer, and early candidate sorting.
   - Avoid over-prescribing workflow internals, workspace layout, exact venues, baselines, or kill criteria.

3. **Optional Follow-Up Questions**
   - Include at most 3 optional questions only if they would materially improve the prompt.
   - Make clear the prompt is usable without answering them.

## Prompt Skeleton

Use this structure when drafting:

```text
I want to start an open-ended research direction exploration task.

My existing research base is: [domain, methods, available artifacts].

The broad theme is: [rough topic or research area].

I am interested in borrowing ideas from: [external idea family or mature practice].

Do not misunderstand this as: [forbidden interpretation]. Focus on the transferable structure behind the mechanism, not just the surface label.

Please explore freely first. Do not immediately converge to one method, write a paper, or design a full experiment.

Please:

1. Analyze which mechanisms from [external idea family] may genuinely transfer to [target domain], and why.
2. Propose 5-8 candidate research directions. They may be bold, but explain why each could plausibly work.
3. For each direction, include:
   - core idea;
   - borrowed mechanism;
   - suitable task background;
   - possible paper contribution;
   - minimal validation sketch;
   - largest risk;
   - nearby work areas to check.
4. Do not claim confirmed novelty before nearby-work checking.
5. Sort the directions into:
   - most worth exploring further;
   - interesting but high-risk;
   - likely just concept-stacking or trend-chasing.
6. Recommend 1-2 directions for the next round of deeper literature checking or low-cost validation. Do not treat them as final paper topics.

Keep the exploration open. It is acceptable to move beyond my current domain if there is a shared abstract structure, such as multi-agent competition, scarce shared resources, communication-limited coordination, dynamic budget allocation, or distributed decision-making.
```

## Quality Check

Before finalizing the generated prompt, check:

- Does it make the user's research base explicit?
- Does it preserve enough creative latitude for first-stage exploration?
- Does it prevent the main likely misunderstanding without over-constraining the next agent?
- Does it ask for several candidate directions before narrowing?
- Does it ask the next agent to reason about transferable mechanism structure?
- Does it avoid premature workspace, venue, baseline, and kill-criterion requirements?
- Does it recommend 1-2 next exploration targets without pretending they are final?
