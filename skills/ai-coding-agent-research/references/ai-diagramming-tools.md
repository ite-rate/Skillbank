# AI Diagramming Tools & MCP Servers

## When to use
User asks about AI-assisted diagramming, architecture visualization, drawing tools for coding agents, or how to make LLM-drawn diagrams better.

## The core problem

LLMs drawing diagrams directly (Excalidraw JSON, SVG coordinates) produce poor results: overlapping boxes, tangled arrows, wrong positions. The solution is to separate **structure** (what nodes/edges exist) from **layout** (pixel coordinates), letting an algorithm handle placement.

## Tool landscape (July 2026)

### Excalidraw Architect MCP (recommended)
- **Repo**: `BV-Venky/excalidraw-architect-mcp` (135+ stars)
- **Install**: `pip install excalidraw-architect-mcp`
- **Key differentiator**: Sugiyama hierarchical auto-layout — AI describes components/connections, engine handles pixel math. Zero overlapping.
- **50+ tech icon auto-styling**: Kafka, PostgreSQL, Redis, K8s, Docker, S3, etc. get domain-appropriate visuals
- **Natural language incremental editing**: "add a cache in front of the DB" on existing diagram
- **Architecture knowledge graph** (v1.0): persistent `.claude/architecture.md` as source of truth; diagrams are rendered views. Queryable ("what breaks if payments goes down?"), lintable (cycles, single points of failure), git-diffable.
- **Export**: SVG (zero deps) + PNG (needs cairosvg)
- **Mermaid conversion**: Mermaid → Excalidraw one-way
- **Offline**: no API keys needed
- **MCP config**:
  ```json
  {
    "mcpServers": {
      "excalidraw-architect": {
        "command": "excalidraw-architect-mcp",
        "transport": "stdio"
      }
    }
  }
  ```

### Companion Skills (ship with the MCP)

1. **excalidraw-diagram-design** — teaches AI: node count limits (6-15 for architecture, 10-25 for flows), topology rules, edge label guidelines, common patterns
2. **architecture-knowledge-graph** — teaches AI: service boundary identification, communication signal mapping (HTTP/gRPC/Kafka/DB → labelled links), graph hygiene (stable ids, labelled edges, lint before render)

Install both to `~/.zcode/skills/` or `~/.cursor/skills/`:
```bash
mkdir -p ~/.zcode/skills/excalidraw-diagram-design
curl -o ~/.zcode/skills/excalidraw-diagram-design/SKILL.md \
  https://raw.githubusercontent.com/BV-Venky/excalidraw-architect-mcp/main/.skills/excalidraw-diagram-design/SKILL.md

mkdir -p ~/.zcode/skills/architecture-knowledge-graph
curl -o ~/.zcode/skills/architecture-knowledge-graph/SKILL.md \
  https://raw.githubusercontent.com/BV-Venky/excalidraw-architect-mcp/main/.skills/architecture-knowledge-graph/SKILL.md
```

### MCP Tools provided

**Diagram tools**: create_diagram, mermaid_to_excalidraw, modify_diagram, get_diagram_info, export_diagram

**Knowledge graph tools**: kg_init, kg_add_service, kg_remove_service, kg_link, kg_unlink, kg_set_domain, kg_info, kg_render, kg_render_view, kg_render_around, kg_render_domain, kg_import, whats_connected_to, kg_path, kg_lint, kg_export, kg_diff, kg_onboarding_doc, kg_drift

### Mermaid (built into Markdown)
- Zero install, works in any Markdown preview (Cursor, VS Code, GitHub)
- Good for simple flowcharts, sequence diagrams
- Cannot drag/reposition nodes — static output
- Best when you need quick inline diagrams in docs

### D2 (Declarative Diagramming)
- Terrastruct出品, newer generation diagram-as-code
- Cleaner syntax than Mermaid, better auto-layout
- Growing adoption but smaller ecosystem

### Draw.io / diagrams.net MCP
- Community MCP exists but less popular than Excalidraw Architect
- Better for precise manual positioning

### PlantUML
- Mature, code-based, good UML support
- Styling feels dated vs Excalidraw

## Recommendation for ZCode users

1. Use **Excalidraw Architect MCP** instead of plain Excalidraw MCP
2. Install both companion skills into `~/.zcode/skills/`
3. For architecture docs: use the knowledge graph workflow (architecture.md → kg_render) so diagrams stay version-controlled and queryable
4. For quick inline docs: Mermaid is still fine for simple flowcharts
5. Diagram complexity guideline: 6-15 nodes for architecture diagrams, 10-25 for detailed flows. Split larger systems into multiple focused diagrams.