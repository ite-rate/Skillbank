# Adaptive Depth Algorithm

> Used in STEP 4 of the deliberation protocol across all rooms.

## Overview

The Adaptive Depth Gate prevents two failure modes:
1. **Over-deliberating simple questions** — wasting rounds on questions that already have a clear answer after Round 1
2. **Under-deliberating complex questions** — rushing to verdict on questions with genuine, unresolved tensions

## Consensus Assessment Procedure

After Round 1, the Coordinator reads all outputs and assesses:

### Metrics to Evaluate

**Direction agreement**: Do >80% of members recommend the same basic course of action?
- Yes → HIGH consensus candidate
- No → MEDIUM or LOW

**Reasoning convergence**: Even if conclusions differ, do the underlying analyses point the same direction?
- Strong convergence despite different frameworks → +1 toward HIGH
- Frameworks pointing in different directions → +1 toward LOW

**Novelty check**: Did Round 1 produce significantly different insights, or did members largely echo each other?
- Significant novel insights from different members → more depth warranted
- Members largely agreeing → less depth needed

**Stakes assessment**: How consequential is this decision?
- High stakes (major architectural decision, life crossroads, large business bet) → lower the threshold for deep dive
- Low stakes (quick sanity check, minor decision) → raise the threshold for accepting quick consensus

### Consensus Levels

**HIGH (>80% agreement)**:
- Most members agree on core recommendation
- Frameworks converge despite different lenses
- Proceed to verdict with current Round 1 data
- AskUser: present the consensus and offer to accept or dig deeper

**MEDIUM (60-80% agreement)**:
- General direction is clear but meaningful disagreements exist
- Some frameworks diverge on important dimensions
- Default: proceed to Round 2
- AskUser: show the convergence and divergence, let user choose

**LOW (<60% agreement)**:
- Fundamental disagreements on approach or framing
- Multiple genuinely different recommendations
- Force Round 2 regardless of user preference (but inform them)
- AskUser: explain why depth is important here

---

## Depth Decision Matrix

| Consensus | Stakes | Default Action |
|-----------|--------|----------------|
| HIGH | Low | Accept (skip Round 2) |
| HIGH | High | AskUser — offer deep dive |
| MEDIUM | Low | Proceed to Round 2 |
| MEDIUM | High | Force Round 2 |
| LOW | Any | Force Round 2 |

---

## Mode Overrides

- `--quick` → always skip adaptive gate, go directly to verdict after Round 1
- `--depth full` → always proceed to Round 2, skip adaptive gate
- `--depth auto` (default) → apply the algorithm above

---

## Presenting Adaptive Gate to User

When presenting AskUserQuestion #2, the Coordinator should:

1. Show a 1-sentence summary of each member's Round 1 position
2. State the consensus level with brief reasoning: "3 of 4 members recommend X, with different reasoning. 1 member recommends Y."
3. Offer options that feel genuine:
   - "The consensus is clear — accept?" (for HIGH)
   - "There are real tensions — go deeper?" (for MEDIUM/LOW)
   - Always include: "Just give me the conclusion now"

The framing matters: users should feel like they're being offered genuine intelligence about what kind of question this is, not being asked for administrative preferences.
