---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'ba844b76-c16b-4791-971c-07c5a3c4bf21'
  PropagateID: 'ba844b76-c16b-4791-971c-07c5a3c4bf21'
  ReservedCode1: '62c8919c-f7cc-46f0-bf5e-47cb72a7bbc1'
  ReservedCode2: '62c8919c-f7cc-46f0-bf5e-47cb72a7bbc1'
---

# Excalidraw Drawing Guidelines

## Table of Contents
- Output Contract
- JSON Rules
- Element Rules
- Bound Text (Text Inside Shapes)
- Arrow Bindings
- Arrow Coordinates (CRITICAL)
- Bidirectional Binding (CRITICAL)
- Required Element Properties (excalidraw.com Compatibility)
- .excalidraw File Format
- Layout Rules
- Mindmap Drawing Rules
- Visual Rules
- Common Errors to Avoid
- Minimal JSON Example

## Output Contract
- Output a JSON array of Excalidraw elements only.
- Do not output markdown fences, comments, or explanations.
- If arrows bind elements, referenced elements must have ids.

## JSON Rules
- Array must start with `[` and end with `]`.
- Use double quotes for keys and string values.
- Do not leave trailing commas.
- Booleans must be lowercase `true`/`false`.
- Numeric fields must be numbers, not strings.

## Element Rules
- Common node types: `rectangle`, `ellipse`, `diamond`, `text`.
- Connector types: `arrow`, `line`.
- **IMPORTANT**: Excalidraw does NOT support a `label` property on shapes. To put text inside a shape, you must use the Bound Text pattern (see below).
- Keep properties practical and minimal for render.py rendering; add full properties for .excalidraw file compatibility (see Required Element Properties).

## Bound Text (Text Inside Shapes)

Excalidraw requires a **separate text element** bound to the shape via `containerId` / `boundElements`. Never use a `label` property — it does not exist in Excalidraw's schema.

Pattern:
1. Shape element: add `"boundElements": [{"id": "<text-id>", "type": "text"}]`
2. Text element: set `"containerId": "<shape-id>"`, `"textAlign": "center"`, `"verticalAlign": "middle"`

**Text sizing and positioning** (critical for correct rendering):
- Estimate text dimensions based on content: `width ≈ max_line_chars × fontSize × 0.75`, `height ≈ num_lines × fontSize × 1.25`
- Position text at the **top-left of the centered area** within the container: `x = container_x + (container_w - text_w) / 2`, `y = container_y + (container_h - text_h) / 2`
- Do NOT set text x/y to the container center point — Excalidraw renders text from its top-left corner, so this would shift text downward
- Do NOT set text width/height to tiny values (e.g., 10) — this clips the text to that area in excalidraw.com

```json
{
  "id": "rect-1", "type": "rectangle",
  "x": 100, "y": 100, "width": 200, "height": 80,
  "strokeColor": "#1976d2", "backgroundColor": "#e3f2fd",
  "boundElements": [{"id": "text-1", "type": "text"}]
},
{
  "id": "text-1", "type": "text",
  "x": 130, "y": 125,
  "width": 140, "height": 30,
  "text": "Hello", "fontSize": 16, "fontFamily": 1,
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "rect-1", "originalText": "Hello",
  "autoResize": true, "lineHeight": 1.25
}
```

## Arrow Bindings

For render.py (exportToBlob), simple `start`/`end` with `id` works:
```json
"start": {"id": "node-1"}, "end": {"id": "node-2"}
```

For .excalidraw file compatibility, use `startBinding`/`endBinding`:
```json
"startBinding": {"elementId": "node-1", "focus": 0, "gap": 5},
"endBinding": {"elementId": "node-2", "focus": 0, "gap": 5}
```

Always include `"endArrowhead": "arrow"` for directional arrows and `"startArrowhead": null`.

## Arrow Coordinates (CRITICAL)

**Arrows MUST have correct x, y, width, height, and points calculated from actual element positions.** Excalidraw's exportToBlob renders arrows exactly at their stored coordinates — it does NOT auto-calculate positions from bindings.

**Wrong** (all arrows pile up at origin, invisible or bunched in corner):
```json
{"type": "arrow", "x": 0, "y": 0, "width": 50, "height": 50, "points": [[0,0],[50,50]]}
```

### Points count determines line shape

- **2 points**: straight line — **correct** for flowcharts, state diagrams, org charts, swimlanes, and most structured diagrams.
- **3+ points with `roundness`**: curved line — required for mindmaps and other organic/hierarchical diagrams.
- Using 3 points where straight lines are expected adds unnecessary curvature; using 2 points where curves are expected produces straight lines. Choose based on the diagram type.

If you need curves (e.g., mindmaps), see **Mindmap Drawing Rules** below for midpoint calculation.

### Edge selection rule — pick the edge that faces the other element:

- If |dx| > |dy|: use left/right edges (horizontal connection)
  - Source right edge + gap, target left edge - gap
- If |dy| >= |dx|: use top/bottom edges (vertical connection)
  - Source bottom edge + gap, target top edge - gap

**For mindmaps**: Always use horizontal edges (left/right) from center outward — see Mindmap section below.

### Implementation pattern — use a two-pass approach:

1. First pass: create all shapes, register their positions.
2. Second pass: create arrows using stored positions to calculate coordinates.
3. Third pass: inject arrow refs into shape `boundElements` for bidirectional binding (see Bidirectional Binding section).

```python
# Two-pass arrow creation pattern
_shape_positions = {}  # id -> {x, y, width, height}
_arrow_queue = []       # [(from_id, to_id, color, stroke_width)]

def queue_arrow(from_id, to_id, color="#525252", sw=2):
    _arrow_queue.append((from_id, to_id, color, sw))

def flush_arrows():
    arrows = []
    for from_id, to_id, color, sw in _arrow_queue:
        s, d = _shape_positions[from_id], _shape_positions[to_id]
        # Calculate edge points based on direction
        sx, sy, ex, ey = calculate_edge_points(s, d, gap=8)
        ax, ay = min(sx, ex), min(sy, ey)
        w = max(abs(ex - sx), 1)
        h = max(abs(ey - sy), 1)
        pts = [[sx - ax, sy - ay], [ex - ax, ey - ay]]
        arrows.append(mk_arrow(ax, ay, w, h, pts, from_id, to_id, color, sw))
    return arrows
```

## Bidirectional Binding (CRITICAL)

When an arrow binds to two shapes, BOTH shapes must reference the arrow in their `boundElements`. Missing this causes invisible arrows or broken connections in excalidraw.com.

**Wrong**:
```json
{"id": "rect-1", "boundElements": [{"id": "text-1", "type": "text"}]}
{"id": "arrow-1", "startBinding": {"elementId": "rect-1"}, "endBinding": {"elementId": "rect-2"}}
```
(rect-1 missing arrow-1 in boundElements → broken binding)

**Correct**:
```json
{"id": "rect-1", "boundElements": [{"id": "text-1", "type": "text"}, {"id": "arrow-1", "type": "arrow"}]}
{"id": "rect-2", "boundElements": [{"id": "text-2", "type": "text"}, {"id": "arrow-1", "type": "arrow"}]}
{"id": "arrow-1", "startBinding": {"elementId": "rect-1", "focus": 0, "gap": 5}, "endBinding": {"elementId": "rect-2", "focus": 0, "gap": 5}}
```

**Post-processing function** — always run after all elements are created:
```python
def finalize_bindings(elements):
    d = {el["id"]: el for el in elements}
    for el in elements:
        if el.get("type") != "arrow":
            continue
        sb, eb = el.get("startBinding"), el.get("endBinding")
        for b in (sb, eb):
            if b and b.get("elementId") in d:
                tgt = d[b["elementId"]]
                if tgt.get("boundElements") is None:
                    tgt["boundElements"] = []
                tgt["boundElements"].append({"id": el["id"], "type": "arrow"})
```

## Required Element Properties (excalidraw.com Compatibility)

The render.py `exportToBlob` API is forgiving and fills in defaults. But excalidraw.com requires complete element definitions. Without these properties, elements may exist (selectable) but not render visually.

**All elements** must include:
```
seed, version, versionNonce, isDeleted, groupIds, frameId,
roundness, boundElements, updated, link, locked, angle
```

**Text elements** additionally need:
```
originalText, autoResize, lineHeight (1.25), textAlign, verticalAlign, containerId (null if standalone)
```

**Arrow elements** additionally need:
```
points, startArrowhead, endArrowhead, startBinding, endBinding, width (non-zero), height (non-zero)
```

Recommended base template:
```python
def _base(typ, x, y, extra):
    return {
        "id": nid(), "type": typ, "x": x, "y": y,
        "width": 0, "height": 0, "angle": 0,
        "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
        "fillStyle": "hachure", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 2, "opacity": 100,
        "seed": random.randint(1, 2**31),
        "version": 1, "versionNonce": random.randint(1, 2**31),
        "isDeleted": False, "groupIds": [], "frameId": None,
        "roundness": None, "boundElements": None,
        "updated": int(time.time() * 1000), "link": None, "locked": False,
        **extra
    }
```

## .excalidraw File Format

The render.py automatically wraps elements in the standard .excalidraw format when saving the source file. No manual wrapping is needed.

The standard format is:
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [ ... ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

## Layout Rules
- Default shape size: `160x80`.
- Small shape size: `120x60`.
- Typical spacing: `60-100`.
- Recommended arrangements:
  - Flow-like diagrams: left-right or top-down.
  - Hierarchies: top-down with centered parents.
  - Mindmap: left-to-right hierarchy, root at far left (see Mindmap Drawing Rules below).
  - Concept map: center + radial branches, core concept in the middle.
- Avoid overlap and crossing lines where possible.
- **Zone partitioning**: For diagrams with multiple distinct sections (e.g., two parallel hierarchies), divide the canvas into explicit zones with sufficient gaps (300px+ between zones) to prevent overlap.

## Mindmap Drawing Rules

A mindmap is NOT a grid of boxes with straight lines. It is an **organic, hierarchical structure** with curved connections. Follow these rules strictly:

### Layout Structure

**Left-to-right layout (default and preferred):**
```
  ROOT ────── Branch 1 ── Sub 1a
          │               ── Sub 1b
          ├── Branch 2 ── Sub 2a
          │               ── Sub 2b
          └── Branch 3 ── Sub 3a
                          ── Sub 3b
```

1. **Root node**: Place a large ellipse (280×120+) at the far LEFT of the canvas (e.g., x=50, y centered).
2. **Root vertical centering**: The root's Y position should be the vertical midpoint of all Level-1 branches, so that branches above and below the root are roughly symmetric. This prevents arrows from crossing distant branches.
3. **Primary branches**: Spread vertically to the RIGHT of root, connected by horizontal arrows.
4. **Sub-branches**: Continue further RIGHT from their parent, also connected horizontally.
5. **All connections flow left→right**: arrows always from right edge of parent to left edge of child.
6. **Vertical distribution**: Spread branches evenly across the canvas height so they don't overlap.

### Node Placement (Left-to-Right)

**MUST use a two-pass layout calculation — never create root first then reposition.**

**Pass 1 — Compute L1 branch centers (no element creation):**
1. For each primary branch, calculate its total height (sum of all leaf node heights + gaps).
2. Stack branches vertically with consistent inter-branch gap (e.g. 300-340px).
3. Record each branch's vertical center Y.

**Pass 2 — Place root and create all elements:**
1. Root Y = average of all L1 branch center Y values minus ROOT_H/2.
2. Root X = 50-60. Create root node.
3. Create L1 nodes centered vertically within their branch group.
4. Create L2 nodes stacked from the branch group's start Y.
5. After all nodes are placed, create arrows (flush_arrows).

- **Root node**: Large ellipse (280×130+), bold text (fontSize 20+), x=50-60. Y derived from Pass 2 step 1.
- **Level 1 (primary branches)**: Rounded rectangles (220×55+), x=450-500, centered vertically within their branch group.
- **Level 2 (sub-branches)**: Rounded rectangles (240-300×42+), x=820-860, spaced 50-52px vertically.
- Level spacing: ~400px between hierarchy levels.

### Connection Style

- **ALWAYS use smooth curves, NEVER straight lines.**
- **CRITICAL: Two points (start + end) produce a straight line even with `roundness`.** To create visible curves, arrows MUST have at least 3 points: `[start, midpoint, end]`. The midpoint creates a control point that Excalidraw renders as a smooth curve.
- Set `"roundness": {"type": 2}` on ALL arrows for curved rendering.
- **Source exit point distribution (prevents crossing)**: When root has branches both above and below, don't route all arrows from the same Y. Instead:
  - Branches ABOVE root: exit from upper portion of root's right edge (e.g., `sy = root_y + height * 0.25`)
  - Branches BELOW root: exit from lower portion of root's right edge (e.g., `sy = root_y + height * 0.75`)
  - This separates upward and downward arrows spatially, preventing them from crossing through middle branches.
- **Midpoint calculation for organic curves** (left-to-right connections):
  ```python
  gap = 10
  sx = s["x"] + s["width"] + gap
  # Exit point Y depends on target direction
  if ey < sy:  # target above
      sy = s["y"] + s["height"] * 0.25  # upper quarter
  elif ey > sy:  # target below
      sy = s["y"] + s["height"] * 0.75  # lower quarter
  else:
      sy = s["y"] + s["height"] / 2
  ex = d["x"] - gap
  ey = d["y"] + d["height"] / 2

  midx = (sx + ex) / 2
  dy = ey - sy
  if abs(dy) < 30:
      midy = (sy + ey) / 2 - 20  # gentle arc
  else:
      midy = sy + dy * 0.4  # curve exits horizontally, then bends
  ```
- Use `"strokeWidth": 2` for primary branches, `"strokeWidth": 1` for sub-branches.

### Color Scheme

- Each primary branch gets a DISTINCT color scheme (stroke + light fill).
- All sub-branches inherit their parent's color scheme.
- Root node uses a neutral/dark color (e.g., dark blue `#1a1a2e` with cream fill `#fef3c7`).
- Suggested branch colors (5): `#c1121f`/red, `#2e7d32`/green, `#1565c0`/blue, `#e65100`/orange, `#7b1fa2`/purple.

### Anti-Patterns (DO NOT)

- **Grid/cascading layout** (boxes stacked in columns with no curves) — this is NOT a mindmap.
- **Straight lines** — mindmaps use organic curves with visible curvature.
- **Vertical-only connections** (parent-above-child-below) — this is a tree/org chart, not a mindmap.
- **Center-radial layout in mindmaps** — appropriate for concept maps and network diagrams, but mindmaps should use left-to-right flow for clearer hierarchy reading direction.
- **Arrows crossing through nodes** — curves should go around/between nodes.
- **Post-hoc root repositioning** — creating the root at y=0 and moving it after branches are laid out. This causes coordinate update omissions (text offset mismatch, arrow exit points from wrong Y). Instead, pre-calculate branch positions in a first pass, then place root at the computed center.

### Example: Left-to-right mindmap layout

```
Canvas: 1200 × 1400

Root:  ellipse at (50, 550), size 280×120

Branch 1 (天道不朽·核心设定):  rect at (450, 100)
  Sub: rect at (850, 60), (850, 110), (850, 160), (850, 210)

Branch 2 (天道不朽·四卷结构):  rect at (450, 380)
  Sub: rect at (850, 340), (850, 390), (850, 440), (850, 490)

Branch 3 (长生劫·核心设定):    rect at (450, 630)
  Sub: rect at (850, 590), (850, 640), (850, 690), (850, 740)

Branch 4 (长生劫·六卷结构):    rect at (450, 900)
  Sub: rect at (850, 850), ...

Branch 5 (核心共识):           rect at (450, 1250)
  Sub: rect at (850, 1230), ...
```

### When Data Has Two Parallel Hierarchies

If content has two parallel structures (e.g., comparing two novels), put the root on the left with each hierarchy as a separate primary branch. This is much clearer than center-radial or side-by-side grids.

## Visual Rules
- Use no more than 3-4 primary colors (mindmaps exempt: each branch gets its own color).
- Keep typography consistent:
  - `fontFamily: 1` (Virgil) for hand-drawn style, `fontFamily: 6` for standard.
- Keep stroke widths and styles consistent for the same semantic level.
- Use concise labels.
- `fillStyle: "hachure"` creates diagonal line patterns — may reduce text readability in small cards. Consider `"solid"` or lighter background colors for text-heavy diagrams.

## Common Errors to Avoid
- Returning an object instead of an array.
- Single quotes or unquoted keys.
- Trailing commas.
- Arrow bindings to missing ids.
- Mixed prose with JSON output.
- **Using `label` property on shapes** — does not exist, use bound text pattern.
- **Setting bound text width/height to tiny values** — clips text in excalidraw.com.
- **Setting bound text x/y to container center** — text renders from top-left, causing downward shift.
- **Missing `seed`/`version`/`versionNonce`** — elements invisible in excalidraw.com.
- **Saving raw JSON array as .excalidraw file** — invalid format, needs wrapper object.
- **Arrow x/y at (0,0) with placeholder points** — causes all arrows to render at origin, invisible or bunched. Calculate coordinates from source/target bounding boxes.
- **Missing bidirectional binding** — shapes must reference arrows in boundElements, not just arrows referencing shapes.
- **Straight lines where curves are expected (mindmaps)** — mindmaps must use 3-point curved connections with roundness. Note: 2-point straight arrows are correct for flowcharts and other structured diagrams.
- **Grid layout for mindmaps** — mindmaps must use left-to-right hierarchy with curved connections, not grid/cascading boxes.

## Minimal JSON Example
```json
[
  {
    "id": "rect-1",
    "type": "rectangle",
    "x": 100, "y": 100, "width": 160, "height": 80,
    "strokeColor": "#1976d2",
    "backgroundColor": "#e3f2fd",
    "fillStyle": "hachure",
    "roughness": 2,
    "boundElements": [{"id": "text-1", "type": "text"}],
    "seed": 12345, "version": 1, "versionNonce": 67890,
    "isDeleted": false, "groupIds": [], "frameId": null,
    "roundness": {"type": 3}, "updated": 1700000000000,
    "link": null, "locked": false, "angle": 0,
    "strokeWidth": 1, "strokeStyle": "solid", "opacity": 100
  },
  {
    "id": "text-1",
    "type": "text",
    "x": 130, "y": 125, "width": 100, "height": 30,
    "text": "Start", "fontSize": 16, "fontFamily": 1,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "rect-1", "originalText": "Start",
    "autoResize": true, "lineHeight": 1.25,
    "strokeColor": "#1976d2",
    "seed": 11111, "version": 1, "versionNonce": 22222,
    "isDeleted": false, "groupIds": [], "frameId": null,
    "roundness": null, "boundElements": null, "updated": 1700000000000,
    "link": null, "locked": false, "angle": 0,
    "strokeWidth": 1, "strokeStyle": "solid", "opacity": 100,
    "backgroundColor": "transparent", "fillStyle": "hachure", "roughness": 2
  }
]
```

> AI生成