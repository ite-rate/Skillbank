---
name: paper-experiment-design
description: 'Use when a scientific paper needs empirical support for a claim: hypothesis design, controlled experiment planning, API/GPU execution paths, iteration rules, statistics, and structured result reporting.'
level: manual
native_agent: ClaudeCode
---

# Paper Experiment Design

Use this skill when a paper claim needs validation through a pilot study, ablation, benchmark, or model comparison.

## Inputs

- Claim, conjecture, or literature gap
- Compute/API budget
- Candidate tasks, datasets, benchmarks, or models

## Outputs

- Experiment spec
- `results.json`
- `experiment_summary.md`

## Workflow

1. Design first
   - State which paper claim the experiment supports.
   - Define hypothesis, independent variables, dependent variables, controls, and expected result.
   - Decide statistical plan before running.
   - Keep the first experiment falsifiable, minimal, controlled, and pre-registered.

2. Choose execution path
   - API path: lightweight model comparisons, prompt ablations, multi-model evaluations.
   - GPU path: training, RL, reward shaping, representation learning, or expensive simulations.
   - Use enough tasks, conditions, and trials to make the result interpretable.

3. Iterate with bounded rules
   - Ceiling effect: increase difficulty.
   - Floor effect: decrease difficulty or check for bugs.
   - Not significant: add trials or revise hypothesis.
   - Surprise result: design follow-up.
   - Stop after a bounded number of iterations and report the best valid result.

4. Report data only
   - `results.json`: config, raw results, statistics, and findings.
   - `experiment_summary.md`: purpose, protocol, results, limitations, paper-claim linkage.
   - Do not produce final LaTeX tables/figures here; route presentation to `paper-figures-tables`.

## Quality Gate

Pass only when the hypothesis is clear, controls are explicit, statistical tests or confidence intervals are reported, stochastic results include repeated trials, and limitations are stated.
