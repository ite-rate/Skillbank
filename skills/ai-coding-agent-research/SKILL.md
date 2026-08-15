---
name: ai-coding-agent-research
description: Use when explaining, evaluating, or comparing AI coding agents, terminal coding assistants, IDE agents, agent CLIs, desktop clients, model-native coding tools, or their installation and GUI options.
level: auto
native_agent: Hermes
---

# AI Coding Agent Research

## Overview

Research AI coding agents from primary sources first, then explain them as products: positioning, install surface, model/provider assumptions, safety model, UX surfaces, strengths, weaknesses, and comparable alternatives.

## When to Use

Use for questions like:
- “What is Reasonix / Claude Code / Codex CLI / Gemini CLI / OpenCode / Aider?”
- “Does it have a desktop client or GUI?”
- “Compare coding agents/tools.”
- “Which agent should I use for DeepSeek/OpenAI/Claude/Gemini/local models?”

Do not use for operating Hermes itself; use `hermes-agent` and `maintaining-hermes-agent` for Hermes configuration/troubleshooting.

## Research Workflow

1. Verify current facts with primary sources:
   - Official website/docs
   - GitHub README/releases
   - Package registry metadata (`npm view`, PyPI JSON, Homebrew when relevant)
   - Vendor docs if the tool is officially listed by a model provider
2. Separate stable product traits from marketing claims.
3. If quoting performance/cost/cache numbers, label them as official/project claims unless independently reproduced.
4. Check release channels and naming carefully; coding agents often have `latest`, `next`, `canary`, desktop, and legacy lines.
5. For GUI/client questions, inspect GitHub releases and official download links, not only README prose.

## Comparison Axes

| Axis | What to compare |
| --- | --- |
| Model strategy | Single-vendor native, multi-provider, OpenAI-compatible, local models |
| UX surfaces | CLI/TUI, IDE, desktop GUI, web, IM/bot, mobile-adjacent |
| Execution model | Pair-programming edits, autonomous tool loop, plan/approval mode, subagents |
| Safety | Permissions, deny/allow rules, sandboxing, checkpoints/rewind, git integration |
| Extensibility | MCP, plugins, custom tools, skills/memory/hooks |
| Cost model | Token pricing, prompt cache, context reuse, included subscription quota |
| Maturity | Official vendor product vs OSS community project, release cadence, docs clarity |
| Best fit | SSH/terminal, IDE daily coding, long low-cost runs, enterprise support |

## Product Notes

- **Reasonix**: DeepSeek-native terminal/desktop coding agent. Key differentiator is cache-first append-only session design around DeepSeek prefix cache. See `references/reasonix.md`. For local desktop/user-workspace conversation triage, use `references/reasonix-local-workspace-triage.md`.
- **Claude Code**: Anthropic official terminal coding agent; strong model quality and mature workflow, but higher cost and Anthropic-bound.
- **OpenAI Codex CLI**: OpenAI official local coding agent; good when the user already uses OpenAI/Codex models and OAuth/API flow.
- **Gemini CLI**: Google official CLI; useful for Gemini ecosystem and large-context workflows.
- **Aider**: Mature terminal pair-programming tool, strong git-oriented edit workflow and broad model support.
- **OpenCode**: OSS terminal coding agent with multi-provider positioning and strong TUI orientation.
- **Cursor/Windsurf**: IDE-native agents; best for inline editing and daily editor UX, not primarily SSH/terminal automation. Custom OpenAI-compatible endpoints can be added via Settings → Models → OpenAI API Key → Override (Base URL + API Key + custom model name).
- **ZCode**: Electron-based AI coding IDE (dev.zcode.app) by Z.ai/Bigmodel. Provider configs at `~/.zcode/v2/config.json`, app settings at `~/.zcode/v2/setting.json`, skills at `~/.zcode/skills/`. Supports OpenAI and Anthropic protocol providers. See `references/zcode-provider-config.md` for config extraction and cross-tool reuse.

## AI Diagramming & MCP

For AI-assisted architecture diagrams and flowcharts, **Excalidraw Architect MCP** is the leading solution (auto-layout, 50+ tech icons, knowledge graph, NL editing). See `references/ai-diagramming-tools.md` for the full tool landscape, install instructions, and ZCode integration.

## Answer Pattern

For product introductions, give:
1. One-sentence positioning.
2. “Best for / not best for.”
3. Install/client surfaces.
4. Core differentiators.
5. Safety and extension model.
6. Comparison table or bullets against closest alternatives.
7. Explicit uncertainty/currentness note for fast-moving release channels.

## Common Mistakes

- Do not treat a package `latest` tag as the newest recommended channel; check `next`/RC and official site.
- Do not call a vendor/project performance number an independent benchmark unless reproduced.
- Do not assume “terminal agent” means no GUI; check desktop releases.
- Do not compare only model intelligence; include safety, cost, install friction, extensibility, and workflow fit.
