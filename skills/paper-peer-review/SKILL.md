---
name: paper-peer-review
description: 'Use when simulating peer review for a scientific paper: multi-persona review, calibrated scoring, anti-inflation rules, regression checks, and routing weaknesses back to paper-writing sub-skills.'
level: manual
native_agent: ClaudeCode
---

# Paper Peer Review Simulation

Use this skill when a draft or compiled paper needs critical review and an actionable revision loop.

## Inputs

- Compiled PDF or complete manuscript draft
- Previous review reports, if any
- Target venue or score target

## Outputs

- Overall score
- Per-dimension scores
- Strengths and weaknesses
- Actionable revision plan routed to sub-skills
- Regression check for previously fixed issues

## Reviewer Personas

Use 3-5 independent reviewers per round:

- Experimentalist: statistical rigor, baselines, replication.
- Theorist: definitions, proofs, MECE taxonomy, technical depth.
- Perfectionist: clarity, formatting, figures, paper polish.
- Synthesizer: cross-cutting analysis, novelty, gap identification.
- Newcomer: accessibility, definitions, examples.

## Scoring Protocol

- Reviewers score independently; avoid anchoring.
- Final score is the median reviewer score.
- Score novelty, comprehensiveness, clarity, technical depth, and experimental validation.
- Calibrate conservatively: workshop, main-conference, strong-accept, oral-level.

## Anti-Inflation Rules

- First review round is capped below top-tier scores.
- Limit score gains per round.
- Keep at least one unresolved weakness unless the paper truly meets the target.
- Use a different model or reviewer style for at least one reviewer when possible.

## Weakness Routing

- Citation coverage insufficient -> `paper-literature-survey`.
- Too many arXiv-only references -> literature venue upgrade.
- Structure unclear -> `paper-structure-logic`.
- Taxonomy not novel -> taxonomy redesign.
- Claims too strong -> hedge downgrade.
- Missing or weak experiments -> `paper-experiment-design`.
- Tables incomparable or visuals missing -> `paper-figures-tables`.

## Quality Gate

Pass only when the paper compiles/renders cleanly, review score meets the current target, and previously fixed weaknesses remain fixed.
