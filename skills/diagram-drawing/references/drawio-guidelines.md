# Draw.io Drawing Guidelines

## Table of Contents
- Output Contract
- Core Structure Rules
- Layout Rules
- Visual Rules
- Common Errors to Avoid
- Minimal XML Skeleton

## Output Contract
- Output valid mxGraph XML only.
- Do not output markdown fences, comments, or explanations.
- Keep all element ids unique. Start visible elements from id `2`.

## Core Structure Rules
- Use `mxGraphModel > root` as the document structure.
- Include base cells:
  - `<mxCell id="0" />`
  - `<mxCell id="1" parent="0" />`
- Vertex nodes must use:
  - `vertex="1"`, `parent="1"`
  - child `<mxGeometry ... as="geometry" />`
- Edge nodes must use:
  - `edge="1"`, `parent="1"`
  - valid `source` and `target` ids
  - child `<mxGeometry relative="1" as="geometry" />`
- Use double quotes for all attribute values.
- Ensure all tags are properly closed.

## Layout Rules
- Default node size: `160x80`.
- Compact node size: `120x60`.
- Spacing between nodes: `60-100`.
- Recommended flow direction:
  - Flow/State/Swimlane/Dataflow: top-down or left-right.
  - Hierarchy (org/tree): top-down.
  - Mindmap/concept: center + radial branches.
- Avoid overlap by checking rectangle bounds before placing new nodes.

## Visual Rules
- Keep same-level nodes consistent in size and style.
- Use up to 3-4 primary colors.
- Keep label text concise and readable.
- Use orthogonal connectors when routing around obstacles.

## Common Errors to Avoid
- Unclosed tags.
- Broken quoted attributes.
- `mxGeometry` outside `mxCell`.
- Edge `source`/`target` pointing to non-existent ids.
- Mixed prose with XML output.

## HTML Entity Encoding in Rich Text Values (Critical)

When using HTML-formatted `value` attributes (e.g., `<font style=&quot;...&quot;>`), the XML contains `&quot;`, `&amp;`, `&lt;`, `&gt;` entities. These entities cause a **rendering failure** if not handled correctly:

**Root cause**: The render pipeline embeds XML as JSON inside an HTML `data-mxgraph` attribute. The browser's HTML parser decodes entities (`&quot;` → `"`) **before** `JSON.parse()` runs, breaking the JSON structure.

**Fix applied in `render.py`**: Ampersands in the JSON data are HTML-encoded (`&` → `&amp;`) before embedding, so `&quot;` becomes `&amp;quot;` in the HTML attribute, which the browser decodes back to `&quot;` (preserving the entity for JSON).

**Symptom**: `Page.wait_for_selector: Timeout ... exceeded` with console error `SyntaxError: Expected ',' or '}' after property value in JSON`.

**Debugging tip**: If rendering fails silently, check browser console for JSON parse errors by running the generated HTML in a headed browser or capturing `page.on('console', ...)` events.

## Minimal XML Skeleton
```xml
<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
  </root>
</mxGraphModel>
```
