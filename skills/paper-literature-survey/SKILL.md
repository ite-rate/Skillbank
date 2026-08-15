---
name: paper-literature-survey
description: 'Use when strengthening a scientific paper''s literature foundation: high-recall retrieval, citation scoring, citation-depth planning, arXiv-to-venue upgrade, bibliography verification, and taxonomy-cell coverage.'
level: manual
native_agent: ClaudeCode
---

# Paper Literature Survey

Use this skill for survey/reference work before or during scientific paper writing.

## Inputs

- Research topic
- Taxonomy keywords or section outline
- Existing references, if any

## Outputs

- `references.bib`
- `citation_plan.jsonl`
- Coverage report: gaps, must-cite papers, weak taxonomy cells, verification status

## Workflow

1. High-recall retrieval
   - Build 20-30 search queries across core terms, synonyms, method names, benchmark names, and taxonomy cells.
   - For each taxonomy cell, use at least three query variants.
   - Snowball from seed papers through references and citation networks.
   - Target 200-500 raw candidates before filtering for a full survey.

2. Literature Quality Score
   - Score candidates on recency, citation velocity, venue strength, institution/lab signal, and acceptance status.
   - Treat high-score papers as must-cite, middle-score papers as conditional, and low-score papers as drop candidates.
   - Prefer accepted conference/journal versions over arXiv-only versions when verified.

3. Citation depth classification
   - A-level: section protagonist, paragraph-level discussion.
   - B-level: important insight, several sentences.
   - C-level: support citation, one sentence.
   - D-level: drop or background-only.

4. Venue upgrade
   - Check DBLP, OpenReview, ACL Anthology, publisher pages, and conference pages.
   - Upgrade arXiv entries to accepted proceedings when title/authors match.
   - Keep arXiv-only ratio controlled for final manuscripts.

5. Verification
   - Verify title, authors, year, venue, URL/DOI for sampled batches and all high-impact citations.
   - Flag hallucinated or mismatched references immediately.
   - Report year distribution, accepted-paper ratio, arXiv-only ratio, and taxonomy-cell coverage.

## Quality Gate

Pass only when recent work is represented, accepted papers are not underrepresented, hallucinated citations are zero, and every taxonomy cell has enough A/B-level references.
