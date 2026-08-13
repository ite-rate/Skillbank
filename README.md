# Skill-Hub

> Central skill repository syncing canonical `SKILL.md` to 7 AI agents via IR (`parser → IR → emitter`).
> **body byte-identical, no loss** — this is the non-negotiable hard constraint throughout.

## Why

7 desktop AI agents, each with its own skill directory and frontmatter dialect.
Without a single source of truth (SSoT), skills are copied manually across dirs / machines and drift.

Skill-Hub makes `~/SkillHub/skills/<name>/SKILL.md` the canonical source, then emits copies
to each agent with per-agent frontmatter rewriting, prompt injection, and manifest tracking.
Cross-machine sync via git (Mac main edit → laptop periodic pull → server manual pull).

## Repository layout

```
SkillHub/
├── skills/<name>/              # canonical source of truth (one dir per skill)
│   ├── SKILL.md                # canonical frontmatter + body (zero-loss baseline)
│   └── resources/              # scripts, references, fonts (non-md assets)
├── manifests/
│   └── deployments.json        # who deployed what skill to which machine x agent
├── agents.toml                 # 7 agents: install_dir / method (cp|ln) / level field mapping
├── capabilities.toml            # 13 capability tags x 7 agents (supported/unsupported/unknown/partial)
├── machines.toml               # 3 machines: home dir expansion + agents installed
├── bin/skillhub                 # CLI entry (fallback wrapper; prefer pip install -e .)
├── src/skillhub/
│   ├── cli.py                   # argparse subcommands: sync / add / rm / list / import / doctor
│   ├── ir.py                    # SkillIR dataclass (body: bytes) + parser/emitter framework
│   ├── parsers/                 # per-input-source parsers (canonical / per-agent)
│   ├── emitters/                # per-agent emitters (claudecode / zcode / qwenworkcn / teleagent / hermes / codex / kimi-code)
│   ├── manifest.py              # deployments.json read/write
│   ├── capabilities.py          # capabilities.toml loader
│   ├── prompt_inject.py         # native_agent + missing-capability front-matter injection
│   └── interactive.py           # skill x agent x machine interactive menu
└── tests/                       # roundtrip zero-loss tests (CI gate)
```

## 7 target agents (verified, not as the requirements doc claimed)

| Agent in agents.toml | real product | install dir |
|---|---|---|
| `ClaudeCode`  | Anthropic Claude Code | `~/.claude/skills` |
| `ZCode`       | 智谱 ZCode (GLM-5.2) | `~/.zcode/skills` |
| `QwenWorkCN`  | 阿里 QwenWorkCN 千问办公 (**not** Qwen Code CLI) | `~/.qwenworkcn/skills` |
| `TeleAgent`   | TeleAgent (OpenCode 内核) | `~/.config/TeleAgent/skills` |
| `Hermes`      | NousResearch Hermes | `~/.hermes/skills/<category>/` |
| `Codex`       | OpenAI Codex | `~/.codex/skills` |
| `kimi-code`   | moonshot kimi-code (**not** `${HOME}/.kimi`, **not** Claude-follower) | `~/.kimi-code/skills-imported` (via `--skills-dir`) |

> The original requirements doc had wrong identities for Qwen (Office vs Code CLI)
> and kimi (it claimed Claude-follow / OpenClaw; reality is moonshot kimi-code).
> See `docs/` (M7) for the audit trail. The dead-listed requirements below are NOT implemented.

## Canonical SKILL.md frontmatter

```yaml
---
name: canvas-design
description: Create beautiful visual art using design philosophy + AI image gen.
level: auto                            # auto | manual | experimental | disable
native_agent: TeleAgent                # optional; emitter injects "originally from X" hint
requires: [image_generation, file_write]   # optional; referenced against capabilities.toml
description_zh: 创意海报设计...           # optional; bilingual (emitter mirrors to TeleAgent _cn / QwenWork _zh)
name_zh: 创意海报设计                    # optional
version: 1.0.0                          # optional
license: Complete terms in LICENSE.txt   # optional
---
<body — bytes, byte-identical across parser→emitter→parser roundtrip>
```

Agent-specific fields (TeleAgent `name_cn`/`description_cn`/`create_source`,
QwenWork `name_zh`/market metadata, Hermes `metadata.hermes`, etc.) are NOT stored in canonical;
they live in per-agent `.agent_overrides/<agent>.toml` next to the canonical SKILL.md and
are tapped by emitters.

## Pipeline

```
canonical SKILL.md
  └─> parser (parsers/canonical.py)
        └─> SkillIR {name, description, body: bytes, level, native_agent, requires, agent_overrides, resources}
              └─> prompt_inject (prepend native/capability hints as blockquote; body bytes untouched)
                    └─> emitter (emitters/<agent>.py)
                          ├─ frontmatter rewrite (level mapping, lang duplication, description truncation)
                          ├─ resource cp/sync
                          └─ deployed SKILL.md on target machine's agent dir
                                └─ manifest record (manifests/deployments.json)
```

**Zero-loss guarantee**: `tests/test_roundtrip.py` asserts
`parser(canonical) -> IR -> emitter(agent) -> parser -> IR` keeps `IR.body == original IR.body`
(byte-identical). This test is the project CI gate.

## level field mapping

| level | canonical | deployed to | LLM auto-trigger on target agent |
|---|---|:-:|---|
| `auto`          | synced      | yes | allowed |
| `manual`        | synced      | yes | blocked via `disable-model-invocation: true` (Claude/Codex/ZCode) or `enabled_at: false` (TeleAgent/QwenWork) |
| `experimental`  | synced      | yes | blocked (same as manual) |
| `disable`       | NOT synced  | copies cleaned on next sync | — |

`disable` is equivalent to `rm` minus canonical deletion: next sync deletes all deployed copies
(per manifest), canonical stays in git for recovery.

## CLI

```sh
# install once (creates `skillhub` on PATH)
pip install -e ~/Documents/main_store/temp/SkillHub

# or use the fallback wrapper without installing
~/Documents/main_store/temp/SkillHub/bin/skillhub <command>

skillhub sync                       # interactive: pick skill x agent x machine, show diff, confirm
skillhub sync -s canvas-design      # one skill
skillhub sync -a ClaudeCode --yes   # one agent, no prompt
skillhub add ./some-skill-dir       # import new skill -> canonical
skillhub rm canvas-design           # remove + cleanup deployed copies
skillhub list --agent ClaudeCode
skillhub doctor                     # env check (agent dirs / git / manifest / kimi --skills-dir)
```

## Not implemented (dead-listed after grilling audit)

These requirements-doc claims were wrong on the verified environment and are NOT implemented:

- ❌ Qwen hardcoded `E:\anaconda\...\python.exe` path replacement — QwenWorkCN实测不存在
- ❌ Qwen `priority`/`paths`/`user-invocable`/`source` fields — those belong to Qwen Code CLI (dev build), not QwenWorkCN
- ❌ kimi follows `~/.claude/skills` / 100% OpenClaw-compatible — kimi is moonshot kimi-code, has `--skills-dir` for independent integration

## Open items to verify during implementation

1. **kimi default skill auto-discovery path** — confirm by running `kimi` once; decide cp to `~/.kimi-code/skills` or `--skills-dir` config. (M4)
2. **Hermes category default** — verified has `creative/` subdir + top-level mix; emitter uses `imported/` to avoid polluting `creative/`. (M3)
3. **Codex description truncation** — suffix `...` vs trim-to-last-sentence; verify with live codex load (M3)
4. **ZCode symlink skill discovery** — confirmed `~/.zcode/skills/agora` is a working symlink; re-verify after M4 cleanup of real copies (archify etc.).
5. **git remote** — local-only for now; add GitHub private or self-hosted when cross-machine tested (M7).

## Status

- [x] M0 skeleton (this commit): git repo + dir layout + 3 toml configs + CLI framework
- [ ] M1 IR core + zero-loss roundtrip test
- [ ] M2 ClaudeCode emitter + real-skill deploy test
- [ ] M3 TeleAgent / QwenWorkCN / Codex / Hermes emitters
- [ ] M4 ZCode symlink + kimi --skills-dir verification
- [ ] M5 manifest + rm / disable chain
- [ ] M6 interactive menu + add / import / list / doctor
- [ ] M7 cross-machine end-to-end + README polish

## Audit trail

All grilling decisions (17 hard answers) and the verified 7-agent topology
are persisted in the ZCode project memory file `skill-hub-project-status.md`.