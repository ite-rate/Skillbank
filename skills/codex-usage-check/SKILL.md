---
name: codex-usage-check
description: Check local Codex CLI quota/usage by reading session telemetry when no direct usage command exists.
level: manual
native_agent: Hermes
version: 1.0.0
license: CC0-1.0
---

# Codex Usage Check

Use this when the user asks for local Codex quota, usage, limits, credits, or reset times.

## Goal

Report the current Codex usage state from the local machine, even if the CLI has no dedicated `usage` command.

## Recommended workflow

### Step 1: Distinguish command type

Codex has **two layers** of commands. When the user asks about "status", "usage", "quota", etc., clarify which layer they mean:

- **Shell subcommands**: `codex login status`, `codex --help`, `codex doctor`
- **Interactive slash commands**: typed inside a running Codex session, e.g. `/fast`, `/model`, `/status`

If the user says "I remember it's `/status`", they mean an **interactive slash command**, not a shell subcommand.

### Step 2: Check shell-level status first

```bash
which codex
codex login status
codex --help
codex doctor
```

### Step 3: Check interactive slash commands

To discover available slash commands:

**Option A: Start an interactive session and try `/help`**
```bash
codex
# Then type: /help
```

**Option B: Search the Codex binary for slash command strings**
```bash
strings $(which codex) | grep -E "^/[^/ ]+$" | sort -u
```

Known slash commands (from binary analysis):
- `/fast` — toggle fast mode (1.5x speed, increased usage)
- `/model` — change model
- `/help` — show help

**Option C: Inspect session telemetry for `token_count` events**
Look under `~/.codex/sessions/**/*.jsonl` for `"type":"token_count"` events with `rate_limits`:

```bash
grep -R '"type":"token_count"' ~/.codex/sessions --include='*.jsonl'
```

Extract from the latest `rate_limits` payload:
- `primary.used_percent`
- `primary.resets_at`
- `secondary.used_percent`
- `secondary.resets_at`
- `credits.has_credits`
- `credits.unlimited`
- `credits.balance`

If reset times are Unix epochs, convert them with `date -r <epoch> '+%Y-%m-%d %H:%M:%S %Z'`.

### Step 4: Summarize

- short-window limit status
- long-window limit status
- whether credits are present
- whether the account appears unlimited
- available slash commands and their meanings

## Useful commands

Shell-level:
```bash
which codex
codex login status
codex --help
codex doctor
```

Discover interactive slash commands:
```bash
strings $(which codex) | grep -E "^/[^/ ]+$" | sort -u
```

Search session telemetry:
```bash
grep -R '"type":"token_count"' ~/.codex/sessions --include='*.jsonl'
```

If available, parse with `jq` or Python to find the latest event and extract `rate_limits`.

## Pitfalls

- **Distinguish shell subcommands from interactive slash commands.** When a user mentions a command like `/status`, they likely mean a slash command inside an interactive Codex session, not a shell argument. Don't waste time searching `codex --help` for it.
- **Codex requires a real TTY** for interactive mode. Running `echo "/status" | codex` or PTY emulation via Python may fail with "stdin is not a terminal". To test slash commands, the user must run `codex` interactively in a real terminal.
- **There may be no `codex usage` shell subcommand**; don't assume it exists at the shell level.
- **The newest session file may not be the one with the latest quota event**; search for the latest `token_count` record across session logs.
- **`credits.balance` may be null** even when usage data is present.
- **Always convert `resets_at` to a human-readable local time** before reporting.
- **Binary string search is a reliable fallback** for discovering slash commands when interactive mode is hard to automate: `strings $(which codex) | grep -E "^/[^/ ]+$"`

## Verification

The answer should include at least:
- login status (from `codex login status`)
- available slash commands (from binary search or interactive `/help`)
- primary usage percent and reset time (from telemetry)
- secondary usage percent and reset time (from telemetry)
- credits/unlimited state (from telemetry)

If any of those cannot be found, say so explicitly rather than guessing. If the user mentions a slash command you cannot verify (e.g. `/status`), ask them to run it interactively and share the output rather than asserting it doesn't exist.
