---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '72a322aa-082b-4850-83b0-a7ca766126f3'
  PropagateID: '72a322aa-082b-4850-83b0-a7ca766126f3'
  ReservedCode1: '12a0e00c-1229-4c51-8825-c700c6af4e43'
  ReservedCode2: '12a0e00c-1229-4c51-8825-c700c6af4e43'
---

# Visual QA Checklist

Used by Step 5 (Visual QA Gate) to build image_understanding prompts.
For each diagram, apply: Universal checks + Diagram-type checks + Engine checks.

## Universal Checks (all diagrams)

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| U1 | Text readability | All text is legible, no truncation/overflow/blur. Font size sufficient for labels. |
| U2 | No accidental overlap | No nodes/shapes overlap each other unless semantically intended (e.g. Venn). |
| U3 | Arrow visibility | All arrows/lines are visible and not hidden behind shapes or clipped at edges. |
| U4 | Arrow direction | All arrows point in the correct direction (from source to target, not reversed). |
| U5 | Connection integrity | Every arrow connects to exactly two nodes; no orphan arrows or dangling ends. |
| U6 | Color distinguishability | Different branches/sections use clearly distinguishable colors. |
| U7 | Layout balance | The diagram does not appear heavily skewed to one corner; content is centered and balanced. |
| U8 | Content completeness | All items described by the user appear in the diagram; no missing nodes. |
| U9 | No crossing lines (where avoidable) | Lines do not cross through node interiors; crossing between lines is minimized. |
| U10 | Canvas fit | All content fits within the image bounds; nothing is clipped. |

## Diagram-Type Checks

### Mindmap

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| M1 | Root centering | Root node is vertically centered among all Level-1 branches (not floating at top-left or bottom). |
| M2 | Left-to-right flow | Layout flows strictly left→right: root on left, L1 branches to its right, L2 further right. Not center-radial or top-down. |
| M3 | Curved connections | All connections are smooth curves (not straight lines). Curves have visible curvature, not barely-bent. |
| M4 | Branch color consistency | All sub-branches inherit their parent branch's color scheme. Each branch group is self-consistent. |
| M5 | No cross-branch overlap | Leaves of one branch do not overlap with leaves or connections of another branch. |

### Flowchart

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| F1 | Start/end markers | Clear start (ellipse/rounded rect) and end nodes present. |
| F2 | Decision diamonds | Decision points use diamond shapes with labeled outgoing branches (是/否, Yes/No). |
| F3 | Flow direction consistency | All flows follow a single predominant direction (top-down or left-right), no back-and-forth confusion. |

### Org Chart / Tree

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| T1 | Parent centering | Each parent node is horizontally centered above/beside its children. |
| T2 | Level alignment | Nodes at the same hierarchy level are aligned on the same row/column. |

### SWOT / Matrix

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| S1 | Quadrant clarity | Four quadrants are clearly separated with distinct background colors. |
| S2 | Label presence | Each quadrant has its category label (e.g. Strengths/Weaknesses). |

### Sequence Diagram

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| Q1 | Lifeline alignment | Participant lifelines are vertical and evenly spaced. |
| Q2 | Message direction | Arrows between lifelines point in the correct direction (caller→callee). |

### ER Diagram

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| E1 | Relationship diamonds | Relationships are shown as diamonds with cardinality labels. |
| E2 | Entity distinction | Entities and relationships are visually distinct shapes. |

### Architecture Diagram

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| A1 | Layer separation | Layers/zones are clearly separated with labels. |
| A2 | Data flow direction | Arrows show clear data flow direction between components. |

### Concept Map

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| C1 | Relationship labels | Arrows/lines between nodes have descriptive labels. |
| C2 | Hub visibility | Central/important nodes are visually prominent (larger, bolder, or different color). |

### General chart types (gantt, timeline, funnel, pyramid, venn, fishbone)

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| G1 | Axis/scale readability | Axis labels, scales, or proportions are readable and accurate. |
| G2 | Data-point alignment | Data points, bars, or segments align correctly with their labels. |

## Engine-Specific Checks

### Excalidraw

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| X1 | Bidirectional binding | Arrows are visually attached to both endpoints (not floating near them). If an arrow appears detached from its source or target, binding is broken. |
| X2 | Hand-drawn aesthetic | The diagram exhibits the expected hand-drawn/sketchy visual style (slightly rough lines, not pixel-perfect). |

### Draw.io

| # | Check Item | PASS Criteria |
|---|-----------|---------------|
| D1 | Shape rendering | All shapes render correctly (no broken geometry or missing fills). |
| D2 | Professional/clean aesthetic | The diagram looks clean and professional with consistent styling. |

> AI生成