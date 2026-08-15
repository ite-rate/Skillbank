---
name: paper-guardrails
description: Use as a lightweight orchestration layer for multi-step, ambiguous, or scope-sensitive research-paper tasks involving experiments, writing, review, figures, or submission cleanup. Do not invoke for simple isolated edits that can be completed safely by one specialized skill. This skill does not perform literature review, experiment design, writing, peer review, or figure design; it guides Codex toward the right proven skill, prevents scope drift, triages suggestions before execution, and prompts for clarification only when ambiguity affects cost, scientific content, artifact roles, or paper identity.
level: manual
native_agent: ClaudeCode
---

# Paper Guardrails

This is a lightweight runtime guide for research-paper work. It must not replace specialized paper skills. Use it to keep the agent aligned with the user's current direction while selecting and applying other skills.

## Purpose and Non-Goals

Do:

- identify the current research-paper stage;
- preserve the user's latest direction as the active workflow constraint;
- identify the source-of-truth manuscript, results, figures, and task state before changing them;
- route to the smallest useful set of proven skills;
- triage reviewer, advisor, or skill suggestions before execution;
- continue the user's task after routing unless a high-risk ambiguity blocks safe execution;
- verify that the result still matches the evidence, build state, and user constraints.

Do not:

- replace `deli-autoresearch` state management;
- replace paper-writing, literature-survey, experiment-design, peer-review, or figure-design skills;
- stop after merely naming a skill;
- expand the research scope during submission cleanup;
- invent missing citations, data, experiments, implementation details, or venue requirements.

## Runtime Protocol

Use this loop for nontrivial paper tasks:

1. Inspect the current artifacts and recent user direction.
2. Infer the primary stage, objective, locked constraints, source of truth, and scope risk.
3. Select the smallest proven skill set that covers the task.
4. Execute the requested work in the same turn.
5. Verify outputs against source files, evidence, references, build state, and user constraints.
6. Report completed work, unresolved risks, and intentionally deferred items.

Routing is an internal control step, not the final deliverable. Do not stop after naming or selecting a skill unless an expensive, irreversible, or science-changing ambiguity genuinely blocks execution.

## Runtime State

Maintain this state internally when a task is multi-step or scope-sensitive:

```text
Primary stage:
Current objective:
Source of truth:
Locked constraints:
Selected skill(s):
Scope risk:
Completion criteria:
```

The user's latest explicit direction is the primary workflow constraint unless it conflicts with verified evidence, research integrity, safety, or explicit submission requirements. Surface such conflicts instead of silently overriding either side.

If the user corrected the agent in the previous 1-3 turns, restate that correction as an active constraint before proceeding.

## Research Integrity

- Never invent citations, datasets, experimental results, statistical significance, implementation details, completed experiments, or venue requirements.
- Do not change reported numbers unless they are verified against the source of truth.
- Distinguish observed results, derived interpretations, and speculative recommendations.
- Do not strengthen a claim beyond available evidence.
- Treat reviewer, advisor, and skill outputs as proposals or risk signals, not facts.
- Do not adjust an experiment's interpretation rule after seeing results without explicit justification.

## Artifact Safety

- Prefer minimal, localized, recoverable edits.
- Edit source files rather than generated outputs whenever possible.
- Inspect relevant manuscript, result files, figures, bibliography, and task state before proposing changes.
- Do not infer the current paper state from an earlier summary when newer artifacts are available.
- Do not delete figures, tables, labels, bibliography entries, or source files until references are verified.
- Inspect diffs after nontrivial modifications.

## Guardrails

1. Determine stage before choosing action.
2. Use the user's latest direction as the active constraint.
3. Do not run experiments without a named claim.
4. Triage review suggestions before executing them.
5. Clarify before changing paper identity, method definition, experiment scope, or figure/table role.
6. During submission cleanup, do not introduce new science.
7. Use `humanizer` only after scientific content is stable.
8. Keep limitations honest, but do not repeatedly weaken the paper's own contribution.

## Proven Skill Stack

Prefer these already-validated skills for research-paper work before trying new tools. This list is not a capability hierarchy; it is practical routing memory from prior successful paper iterations.

### Long-Horizon State

- `deli-autoresearch`: Multi-iteration research tasks that need durable state, task specs, progress tracking, findings logs, stale-count handling, heartbeat checks, and verification agents.

### Research Paper Core

- `research-paper-writing`: Paper writing and revision once scientific content is mostly defined; useful for abstract, introduction, contribution framing, claim calibration, writing polish, and submission-readiness wording.
- `paper-structure-logic`: Argument repair, contribution structure, related-work positioning, novelty claims, paragraph logic, and claim boundaries.
- `paper-experiment-design`: Empirical support for a named claim, baseline/stress scenario/seed planning, and experiment scoping before execution.
- `paper-literature-survey`: Venue fit, related work, citation coverage, arXiv-to-venue upgrades, and domain positioning.
- `paper-peer-review`: Simulated reviewer criticism across novelty, experiments, claims, structure, and writing.

### Supervisor Review Series

- `pre-submission-reviewer`: Broad submission-facing review across macro logic, writing details, grammar, LaTeX formatting, figure quality, and reviewer-style severity triage.
- `figure-designer` / Figure Design Advisor: Figure narrative planning, especially motivated examples, system/framework overviews, mechanism diagrams, and experimental trade-off figures.

Supervisor-style outputs are review evidence, not direct instructions. Triage them before execution.

### Figures, Tables, Tone, and Verification

- `paper-figures-tables`: Publication-quality tables, captions, visual inventories, table/figure consistency, and decisions to add, simplify, move, or delete figures/tables.
- `humanizer`: Final tone cleanup only after scientific content is stable; reduce AI-like phrasing and excessive defensive wording without changing claims.
- `superpowers:receiving-code-review`: External review/advisor feedback when suggestions are costly, ambiguous, or technically questionable.
- `superpowers:verification-before-completion`: Before claiming completion; require evidence from build, tests, references, figures, and consistency checks.

If a named skill is unavailable, use the nearest equivalent capability or perform the narrow task directly under these guardrails. Do not stop solely because a preferred skill is missing.

## Suggested Routing

These are suggestions, not mandatory sequences. Choose the smallest skill set that fits the current stage, user constraint, and risk.

- New research direction: consider `deli-autoresearch` for state, `paper-literature-survey` for positioning, and `paper-experiment-design` only if empirical claims are needed.
- Claim needs evidence: consider `paper-experiment-design` before running anything; after results stabilize, use `research-paper-writing` to integrate evidence into the narrative.
- Draft logic feels weak: consider `paper-structure-logic` for argument repair, then `research-paper-writing` for targeted language and section revision.
- Reviewer/advisor feedback arrives: triage first; if feedback is complex or risky, consider `superpowers:receiving-code-review`; then route to the relevant paper skill.
- Submission-readiness review: consider `pre-submission-reviewer`, targeted `research-paper-writing`, and `paper-figures-tables` for figure/table consistency.
- Figure narrative unclear: consider `figure-designer` for figure role and narrative, then `paper-figures-tables` for captions, placement, consistency, and manuscript integration.
- Final cleanup: consider `pre-submission-reviewer`, LaTeX/build/reference checks, `superpowers:verification-before-completion`, and `humanizer` only after the science is stable.

## Scope and Experiment Gates

Before executing nontrivial reviewer or advisor feedback, classify it:

- P0: Must fix before submission because it directly affects novelty, evidence, correctness, or venue fit.
- P1: Low-cost and high-impact; should fix if feasible.
- P2: Useful but not blocking.
- Revision reserve: Technically reasonable but costly, changes method definition, or requires major new experiments.
- Reject: Misaligned with the paper's direction or lower value than its complexity.

For experiments, fill this row mentally or visibly before proposing or running anything:

| Claim | Experiment | Baseline | Metric | Decision rule | Cost | Risk |
|---|---|---|---|---|---|---|

If the row cannot be filled, do not run the experiment. Ask for direction or use `paper-experiment-design`.

The decision rule must define how both positive and negative outcomes affect the claim. It must not be changed after seeing results without explicit justification.

## Submission Cleanup Mode

When the user asks for final cleanup, submission readiness, consistency pass, or camera-ready-style polish:

Allowed:

- spelling, grammar, terminology, references, citations;
- number consistency across abstract, tables, figures, and conclusion;
- LaTeX build, overfull boxes, cross-references, figure/table placement;
- code-like wording converted to academic analysis wording;
- concise restoration of necessary reproducibility details.

Not allowed unless user explicitly approves:

- new research questions;
- new methods;
- new baselines;
- new experiments;
- major restructuring;
- changing the central claim.

## Clarification Policy

Resolve low-risk ambiguity using the least disruptive reasonable assumption and proceed.

Ask one concise question only when the ambiguity affects an expensive, irreversible, or science-changing action, such as:

- new experiments, baselines, or methods;
- changing the central claim, paper identity, or method definition;
- deleting or replacing key results, figures, or tables;
- changing whether a figure/table is added, replaced, or removed;
- final cleanup where the proposed action would add new scientific content.

## Avoid Unvalidated Tool Drift

Do not introduce new research-management, writing, review, or figure tools when the proven stack covers the task, unless:

- the user explicitly asks for a new tool;
- the proven skill is missing or fails;
- the task requires a capability not covered by the proven stack.

If a new tool is considered, state why the proven stack is insufficient before using it.

## Minimal Visible Output

When useful, state only:

- current stage;
- active constraint;
- chosen skill or action;
- what will not be done;
- verification performed or still needed.

Example:

"Current stage: submission cleanup. Active constraint: no new experiments or method changes. I will use pre-submission review and LaTeX checks, execute the cleanup now, and verify the build before reporting completion."
