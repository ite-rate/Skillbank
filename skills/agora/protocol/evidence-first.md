# Evidence-First Protocol

> Referenced by Forge and Bazaar rooms. Rooms without external evidence (Oracle, Hearth, Clinic, Atelier) use context-gathering instead.

## Principle

Deliberation without evidence produces confident ignorance. Every engineering or business deliberation must begin with contact with reality — the actual codebase, the actual market, the actual data. This protocol governs how evidence is gathered, evaluated, and compiled into an Evidence Brief before any agent analysis begins.

---

## Evidence Quality Tiers

### Tier 1: First-Hand Evidence (Highest)
- Reading actual source code files
- Running actual tests and seeing real output
- Fetching actual competitor pricing pages
- Real git log and commit history

### Tier 2: Derived Evidence (Good)
- grep/glob patterns across codebase
- WebSearch recent news and market data
- Observed architectural patterns from file structure

### Tier 3: Analogical Evidence (Acceptable when Tier 1/2 unavailable)
- Historical analogues ("company X did Y and got Z")
- Domain research and academic sources
- Expert opinion from credible sources

### Tier 4: Speculative (Must be labeled)
- Extrapolation from partial information
- Theoretical arguments without empirical grounding
- Plausible but unverified claims

---

## Evidence Brief Standards

### Completeness Check
An Evidence Brief is complete when it answers:
- What do we **know** (Tier 1-2)?
- What do we **infer** (Tier 3)?
- What do we **not know** (explicit gaps)?
- How does the evidence **relate** to the specific question?

### Evidence Labels
Each claim in agent analyses must be labeled:
- `[empirical]` — directly observed or measured
- `[mechanistic]` — derived from known mechanisms
- `[strategic]` — based on competitive/market logic
- `[ethical]` — based on moral principles
- `[heuristic]` — rule of thumb, experience-based
- `[speculative]` — acknowledged extrapolation

### Confidence Adjustment
- Evidence Brief based entirely on Tier 1-2 → confidence ceiling: HIGH
- Evidence Brief with significant Tier 3 → confidence ceiling: MEDIUM
- Evidence Brief with major gaps → confidence ceiling: LOW, stated explicitly

---

## Anti-Patterns

**Avoid:**
- Proceeding to deliberation with an empty Evidence Brief
- Treating absence of evidence as evidence of absence
- Ignoring contradictory evidence that was found
- Overstating confidence when evidence is thin

**Correct for:**
- Survivorship bias (the examples you found are the ones that worked)
- Recency bias (recent evidence is more salient but not necessarily more relevant)
- Availability bias (evidence that was easy to find may not be representative)
