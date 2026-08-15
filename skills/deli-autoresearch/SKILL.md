---
name: deli-autoresearch
description: Long-horizon autonomous research framework protocol for running multi-iteration tasks with durable task state, fresh agent sessions, append-only findings, stall detection, forced pivots, heartbeat watchdogs, verification agents, and zero-interaction orchestration. Use when setting up or operating autonomous research loops, paper-writing campaigns, multi-agent research tasks, or unattended workflows that must coordinate with paper-literature-survey, paper-structure-logic, paper-experiment-design, paper-figures-tables, and paper-peer-review.
level: manual
native_agent: ClaudeCode
---

# Deli_AutoResearch

Use this skill as a protocol, not as executable code. It defines how to structure long-horizon autonomous research work so that progress survives context loss, stalls are detected mechanically, workers do not judge their own success, and scientific-paper workflows route cleanly into the paper-writing skills.

## Operating Rules

- Run zero-interaction loops once a task is accepted: do not ask whether to proceed, submit, monitor, fix, or retry. Resolve ambiguity conservatively and log the reason as `level=decision`.
- Treat ready as execute: preparation exists to be followed by execution, validation, monitoring, and repair.
- Persist all task memory to files. Do not depend on conversation history or resumed context for progress.
- Start each work iteration in a fresh agent session. Inject only the necessary state files for that iteration.
- Separate worker, orchestrator, heartbeat, and verifier duties. A heartbeat patrol may liveness-check, restart, or nudge; it must not inspect task evidence or rewrite task state for another role.
- Prefer direction diversity over deeper digging when progress stalls.

## Task Directory

Create one task directory per autonomous objective:

```text
{task}/state/
|-- task_spec.md
|-- progress.json
|-- findings.jsonl
|-- directions_tried.json
`-- iteration_log.jsonl
{task}/logs/
|-- work.jsonl
|-- orchestrator.jsonl
`-- heartbeat.jsonl
```

`state/task_spec.md` records goal, background, constraints, milestones, success criteria, verification requirements, and paper-track routing if relevant.

`state/progress.json` should include at least:

```json
{
  "iteration": 0,
  "status": "initialized",
  "total_findings": 0,
  "last_new_findings": 0,
  "stale_count": 0,
  "last_seen": null,
  "active_direction": null,
  "next_role": "work",
  "verification_due": false
}
```

`state/findings.jsonl` is append-only. Each line should be a self-contained finding with evidence references, not a vague progress note.

`state/directions_tried.json` stores directions and why they differ structurally from previous attempts.

`state/iteration_log.jsonl` stores per-iteration summaries: direction, files read, actions, validation run, finding delta, next recommendation.

All logs use JSON Lines:

```json
{"ts":"2026-06-19T12:00:00Z","source":"orchestrator","level":"decision","event":"pivot","detail":"stale_count reached 2; switching from citation expansion to taxonomy stress test"}
```

## Orchestrator Loop

For each iteration:

1. Read only the necessary state: usually `task_spec.md`, `progress.json`, `directions_tried.json`, and the tail or indexed subset of `findings.jsonl` / `iteration_log.jsonl`.
2. Select a structurally distinct direction. After a stall, change a structural constraint, not only parameters.
3. Launch a fresh work agent session with explicit deliverables, working directory, file/line caps, validation command, and completion criteria.
4. Require the worker to append findings to `findings.jsonl` and append a summary to `iteration_log.jsonl`.
5. Compare total findings and quality metrics against the previous iteration.
6. Update `progress.json` and append an orchestrator log line.
7. Trigger verification when due or when claims are citation-like, experimental, or central to the paper.

Stall detection:

- If an iteration produces zero new findings, increment `stale_count`.
- If the primary metric drops, increment `stale_count`.
- If new findings are duplicates or unsupported, treat the iteration as stale.
- At `stale_count >= 2`, force a structural pivot.
- At `stale_count >= 4`, mark the task as structurally stuck and prepare a human-facing escalation report.

Round caps:

- Cap one work session at roughly 15 agent rounds or 30 minutes unless the user explicitly requested a longer run.
- Validation must run between iterations when the task has tests, compilation, data checks, or citation verification hooks.

## Worker Session Prompt Contract

A work agent prompt should include:

- Task background and current direction.
- The exact files it may read.
- The files it must write or append.
- A strict deliverable schema for findings.
- Evidence requirements.
- Validation command or manual verification requirement.
- Completion criteria and a statement that it must not ask the user questions.

Workers should append findings like:

```json
{"id":"F-0001","iteration":1,"direction":"taxonomy-gap-audit","claim":"...","evidence":[{"path":"...","lines":"12-20"}],"confidence":"medium","verification_status":"pending"}
```

## Heartbeat Watchdog

Use layered liveness checks:

- L0 resident guard: independent shell or scheduler guard. If task heartbeat is stale beyond the configured threshold, start an emergency patrol.
- L1 scheduled patrol: periodically read `progress.json` and heartbeat timestamps, restart timed-out loops, and nudge stalled sessions.
- L2 business loop: first action of every callback updates its own `last_seen` and writes a heartbeat log line.

A heartbeat patrol may only:

- Check liveness.
- Restart a missing loop.
- Nudge a stalled work agent with `task_spec.md` and `progress.json`.

It must not read findings deeply, judge paper quality, rewrite task evidence, or report as if it performed the work.

## Verification Agent

Run an independent verification agent regularly:

- After every high-impact iteration.
- After every 20 citation-like entries.
- Before integrating claims into manuscript text.
- Before declaring a task complete.

The verifier reads only the necessary evidence chain: selected findings, cited source snippets or paths, experiment outputs, and the relevant task spec. It appends verification results to `iteration_log.jsonl` or a dedicated verification log if the task creates one. It should mark each checked finding as supported, weakly supported, unsupported, duplicate, or needs external verification.

## Paper Track Coordination

When the task is a scientific paper, route work to the paper skills instead of folding all behavior into this framework:

- Use `paper-literature-survey` for high-recall retrieval, citation scoring, citation-depth plans, venue upgrades, bibliography verification, and taxonomy-cell coverage.
- Use `paper-structure-logic` for outline design, section architecture, taxonomy redesign, paragraph logic, hedging, related-work differentiation, and abstract/conclusion alignment.
- Use `paper-experiment-design` for hypothesis design, controlled experiments, API/GPU execution plans, iteration rules, statistical reporting, `results.json`, and `experiment_summary.md`.
- Use `paper-figures-tables` for benchmark tables, taxonomy tables, ablations, figures, captions, and publication-ready visual outputs from `results.json` or section placeholders.
- Use `paper-peer-review` for independent review rounds, calibrated scoring, weakness routing, regression checks, and final blocking quality gates.

Recommended paper workflow:

1. Initialize the Deli_AutoResearch task directory and write `task_spec.md` with target venue, paper type, audience, success criteria, and allowed resources.
2. Run early structure and literature iterations in separate fresh sessions.
3. Store literature findings in `findings.jsonl`; store bibliography artifacts such as `references.bib` and `citation_plan.jsonl` in task-specific output paths named in `task_spec.md`.
4. Use experiment iterations only for explicit paper claims or gaps.
5. Route presentation artifacts to `paper-figures-tables`; do not let experiment agents produce final LaTeX tables unless that skill is active.
6. Run `paper-peer-review` after compile/render checkpoints and feed weaknesses back through the orchestrator.
7. Treat unresolved major review weaknesses as directions for the next orchestrator iteration.

## Completion Gate

Do not mark the autonomous task complete until:

- `progress.json` status is updated to `complete`.
- Findings needed for the objective are verified or explicitly labeled with limitations.
- No heartbeat/session is still expected to perform work.
- The latest validation or compile/check result is logged.
- For papers, the appropriate paper-skill quality gates have passed or remaining gaps are documented.
