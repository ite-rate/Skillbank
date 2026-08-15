---
name: paper-figures-tables
description: Use when converting scientific paper results, taxonomy, comparisons, or placeholders into publication-quality academic figures and tables.
level: manual
native_agent: ClaudeCode
---

# Paper Figures And Tables

Use this skill when a paper needs high-density tables, benchmark tables, ablation tables, taxonomy visualizations, or publication-ready figures.

## Inputs

- `results.json`
- Section placeholders or manuscript outline
- Taxonomy/method matrix

## Outputs

- `figures/*.pdf` or high-resolution PNG when appropriate
- `tables/*.tex`
- Figure/table inventory with text reference targets

## Table Patterns

- Comparison matrix: methods by features.
- Benchmark table: models by metrics.
- Ablation table: conditions by results.
- Taxonomy table: classification visualization.
- Meta-analysis table: aggregated cross-paper evidence.

## Table Rules

- Use booktabs-style tables; avoid vertical lines.
- Use restrained row shading only when it helps scanning.
- Bold best values and state metric direction.
- Experimental data should report mean plus uncertainty when applicable.
- Captions must state the key finding, not merely describe contents.

## Figure Rules

- Use matplotlib PDF for curves, bars, heatmaps, and quantitative plots.
- Use TikZ or SVG-to-PDF for architecture/flow diagrams when worth the effort.
- PIL/PNG is acceptable for simple schematics when vector output is unnecessary.
- Prefer vector outputs; PNG should be at least 300 DPI.
- Keep font size readable after final manuscript scaling.
- Label axes, include legends, and use light grids where useful.

## Quantity Targets

- Full survey: at least 10 tables and 6 figures.
- Short survey: at least 5 tables and 3 figures.

## Quality Gate

Pass only when each figure/table is referenced in text, captions carry conclusions, experimental tables include uncertainty, and visual outputs are readable at paper scale.
