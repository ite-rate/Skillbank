# Verdict Templates Reference

> This file documents the standard verdict template components shared across all rooms.
> Each room SKILL.md defines its own room-specific verdict, but all inherit these base patterns.

---

## Universal Verdict Footer

Every verdict ends with:

```markdown
### 相关审议室
{1-2 complementary rooms with brief reason}
E.g.: "Also consider: /bazaar if this decision has commercial dimensions, or /clinic if it's affecting your mental health."

### 后续追踪
{Room-specific retrospective prompt}
```

---

## Confidence Rating Guide

All verdicts include a Confidence rating. Use these consistently:

**High**: Evidence is solid, panel agreement is strong, the recommendation is robust to likely challenges.

**Medium**: Evidence is partial OR panel has meaningful disagreement OR the recommendation depends on assumptions that may not hold.

**Low**: Evidence is thin, panel is divided, or the question has high uncertainty that analysis cannot resolve. This is honest, not a failure.

---

## Dissenting Position

Every Full Mode verdict includes a Dissenting Position section:
- State the strongest version of the opposing argument
- Explain what would have to be true for the dissent to be correct
- This is NOT a hedge — it is intellectual honesty about the limits of the consensus

---

## Room-Specific Verdict Structures

| Room | Core Sections | Unique Features |
|------|--------------|-----------------|
| Forge | Architecture Decision, Implementation Path, Risk Assessment, Technical Debt Ledger | Evidence-grounded, code-specific |
| Bazaar | Strategic Recommendation, Financial Scenarios, Competitive Dynamics, Tail Risk | Market-evidence grounded |
| Oracle | Core Tension, Path A/B, Questions Only You Can Answer, Timing Assessment | Non-prescriptive, mirror-like |
| Hearth | Whose Task Is This, Love Audit, Different Frame, Practical Steps | Relational, specific dynamics |
| Clinic | Mechanism Analysis, Stoic Frame, Behavioral Prescription, Protocol | Multi-timeframe, actionable |
| Atelier | Destruction Phase, Simplification, The Space That Opens, Three Experiments | Creative, experimental |

---

## Quick Mode Verdict Minimum

Quick verdicts must contain:
1. The core recommendation (for technical/business rooms) OR core tension (for life/relationship rooms)
2. Panel positions (1 sentence each)
3. One next step OR one question to sit with

Quick verdicts should NOT contain: full Hegelian synthesis, scenario tables, or multi-phase protocols.

---

## Duo Mode Verdict Minimum

Duo verdicts must contain:
1. The dialectic framing: who represents what tension
2. Both positions clearly stated
3. Where they unexpectedly agree (if anywhere)
4. The core tension stated precisely
5. What this means for the user's decision
