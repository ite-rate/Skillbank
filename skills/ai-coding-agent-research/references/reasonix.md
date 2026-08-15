# Reasonix Research Notes

Use this when the user asks about Reasonix or DeepSeek-native coding agents. Verify current versions again before giving install instructions; the project is moving quickly.

## Positioning

Reasonix is a DeepSeek-native AI coding agent for terminal and desktop workflows. Its distinctive claim is not generic multi-model breadth, but long-session cost reduction by designing the agent loop around DeepSeek's byte-stable prefix cache.

Primary sources checked in the source session:
- Official site: `https://reasonix.io/`
- GitHub repo: `https://github.com/esengine/DeepSeek-Reasonix`
- DeepSeek API docs Reasonix integration page
- npm package metadata for `reasonix`
- GitHub release `desktop-v1.6.0`

## Key Claims to Label Carefully

Official/project claims found:
- DeepSeek-native terminal coding agent.
- Append-only/cache-first loop aligned with DeepSeek prefix cache.
- Long sessions can hold 90%+ cache hit and input token cost can collapse to ~1/5.
- A cited project case study claimed 435M input tokens, 99.82% cache hit, about $12 vs about $61 without cache.

When answering, say these are official/project claims unless independently reproduced in the user's environment.

## Current Version/Channel Caveat

At the time checked:
- npm `reasonix` latest was `0.53.2`.
- npm `reasonix@next` was `1.6.0-rc.1`.
- Official docs said 1.0+ is a ground-up Go rewrite and 0.x TypeScript is legacy/maintenance.
- The official site promoted `npm i -g reasonix@next` and desktop `v1.6.0`.

Pitfall: `npm i -g reasonix` may install the legacy line depending on tags. Re-check `npm view reasonix --json` and official install instructions before advising.

## Install Surfaces

CLI/TUI:
- `npm i -g reasonix@next` was the site-promoted command for the Go rewrite.
- `brew install esengine/reasonix/reasonix` was documented for macOS/Linux Homebrew users.
- `reasonix setup`, `reasonix chat`, and `reasonix run "..."` are core entry points.

Desktop GUI release found:
- Release tag: `desktop-v1.6.0`
- macOS: `Reasonix-darwin-universal.dmg` (Apple Silicon + Intel)
- Windows: `Reasonix-windows-amd64-installer.exe`
- Linux: `Reasonix-linux-amd64.deb` and `Reasonix-linux-amd64.tar.gz`

IM/Bot surfaces documented:
- Feishu
- Lark
- WeChat

## Feature Notes

From README/docs/site:
- Config-driven providers, agent settings, enabled tools, and plugins via `reasonix.toml`.
- DeepSeek and MiMo presets; OpenAI-compatible endpoints can be configured.
- MCP-compatible plugins over stdio and Streamable HTTP; `.mcp.json` support.
- Permissions: Ask/Auto/YOLO/Plan/Goal style modes.
- Sandbox: file writers confined to workspace; macOS bash sandboxing via Seatbelt was documented.
- Checkpoints/Rewind: snapshot-based restore of code, conversation, or both; bash side effects are not tracked.
- Two-model collaboration: planner and executor use separate sessions to preserve cache stability.

## Comparison Summary

- vs Claude Code: Claude Code has stronger vendor maturity/model quality; Reasonix has DeepSeek-native low-cost long-session angle and MIT OSS positioning.
- vs OpenAI Codex CLI: Codex fits OpenAI users; Reasonix fits DeepSeek API users and cache-cost optimization.
- vs Gemini CLI: Gemini CLI is attractive for Google/Gemini and large-context workflows; Reasonix is more cache-first DeepSeek-specific.
- vs Aider: Aider is mature git/pair-programming oriented; Reasonix is more autonomous agent loop + cache-first.
- vs OpenCode: OpenCode is more general multi-provider OSS terminal agent; Reasonix is narrower but differentiated by DeepSeek prefix-cache design.
- vs Cursor/Windsurf: IDE-native tools win inline editor UX; Reasonix is better for terminal/SSH/desktop-agent workflows.

## Answering User GUI Questions

If asked “有没有客户端/图形化界面”, answer yes and include:
- Desktop app exists.
- macOS `.dmg`, Windows installer `.exe`, Linux `.deb`/`.tar.gz` were available in GitHub releases.
- Official download page is `https://reasonix.io/`.
- Also supports CLI/TUI and Feishu/Lark/WeChat bot entry points.

Always re-check release assets before giving direct download links in future sessions.
