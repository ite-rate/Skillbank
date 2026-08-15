---
name: paper-structure-logic
description: 'Use when drafting, reorganizing, or repairing a scientific paper''s argument: chapter architecture, taxonomy design, paragraph logic, related-work differentiation, formal claims, hedging, and abstract-conclusion alignment.'
level: manual
native_agent: ClaudeCode
---

# Paper Structure And Logic

Use this skill when a manuscript needs clearer structure, stronger reasoning, or better survey logic.

## Inputs

- Bibliography or citation plan
- Experiment findings, if any
- Target audience or venue
- Existing outline or draft sections

## Outputs

- Revised outline or section plan
- `sections/*.tex` or equivalent manuscript sections
- Claim/hedging audit
- Related-work comparison table plan

## Workflow

1. Build chapter architecture
   - Introduction: hook -> gap -> contributions -> roadmap.
   - Background: definitions, notation, taxonomy overview.
   - Core chapters: one method family or conceptual axis per section.
   - Benchmarks/experiments: protocols, findings, validity threats.
   - Future directions: barrier plus plausible attack vector.
   - Conclusion: numbered key findings, not a repeated abstract.

2. Enforce paragraph logic
   - Use claim -> evidence -> implication for main claims.
   - Use compare -> contrast -> trade-off for method comparisons.
   - Use concession -> rebuttal for critical assessment.
   - Use broad -> narrow -> this paper for introductions.

3. Design taxonomy
   - Prefer multi-axis taxonomies over flat lists.
   - Keep categories as MECE as possible; explain unavoidable overlaps.
   - Empty taxonomy cells are useful gap evidence.
   - Tie each taxonomy cell to representative A/B references.

4. Calibrate claims
   - Use conjecture/observation/remark unless proof-level evidence exists.
   - Claim strength must not exceed evidence strength.
   - Downgrade overclaims with appropriate hedging.

5. Differentiate related work
   - Include a comparison table against existing surveys.
   - Do not rely on recency alone as novelty.
   - Identify structural novelty: taxonomy, lens, empirical synthesis, or experiment.

## Quality Gate

Pass only when sections compile/render, transitions are present, terminology is consistent, core sections contain critical assessment, and abstract/conclusion are aligned.
