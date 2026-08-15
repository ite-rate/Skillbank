---
name: go-study-repo-from-codebase
description: Build a Go-based learning repository from an existing codebase by extracting core architecture, writing annotated docs, and creating runnable teaching prototypes with source-language comparisons.
level: manual
native_agent: Hermes
version: 1.0.0
license: MIT
---

# Go Study Repo from Existing Codebase

Use this when the user wants a **learning-oriented repository** rather than a production port: especially for requests like “study this project’s design principles”, “explain how it works in Go”, “add full comments”, or “compare with the source language”.

## Goal

Create a self-contained Go study repo that:
1. Explains the original system’s architecture
2. Maps real source files to conceptual modules
3. Rebuilds the core abstractions in Go
4. Adds heavy explanatory comments for syntax, structs, interfaces, and design tradeoffs
5. Compares the original implementation language (often Python) with Go
6. Produces a small runnable prototype to validate the abstractions

## When to use

- User wants to **learn** a system, not just run it
- User asks for a **Go version with explanations/comments**
- User cares about **design principles**, **struct design**, **runtime flow**, or **language-feature comparison**
- Source project is large; a full port is inappropriate, but a teaching skeleton is useful

## Workflow

### 1. Locate the target workspace first
If the user mentions an environment shortcut like `cdtmp`, do not assume it exists in non-interactive shells.
- Check shell config files for the alias/function definition if direct execution fails.
- In this macOS setup, `cdtmp` is defined in `~/.zshrc` as:
  ```sh
  alias cdtmp='cd $(mktemp -d /tmp/iteratess-XXXXXX)'
  ```
- If needed, replicate the behavior by creating a temp dir under `/tmp/iteratess-*` and building the repo there.

### 2. Read the real source before designing the study repo
Inspect the top-level README and the main architecture files. For Hermes-style systems, useful files were:
- `README.md`
- `AGENTS.md`
- `run_agent.py`
- `model_tools.py`
- `tools/registry.py`
- `toolsets.py`
- `hermes_state.py`
- `gateway/run.py`
- `cron/jobs.py`
- `cron/scheduler.py`

Also search for anchor symbols/classes/functions (e.g. `AIAgent`, `SessionDB`, `ToolRegistry`, schedule parsing, delivery target resolution).

### 3. Extract the architectural spine
Before writing code, identify the smallest set of concepts that explain the whole system. For Hermes, these were:
- Agent Loop
- Tool Registry / Tool Dispatch
- Session Store
- Gateway / Platform ingress
- Cron Scheduler / Delivery orchestration

Build the study repo around those abstractions. Avoid trying to recreate every provider integration or production detail.

### 4. Create both docs and code
A good study repo needs both.

Recommended structure:
```text
<repo>/
├── README.md
├── docs/
│   ├── 01-reading-map.md
│   ├── 02-python-vs-go.md
│   └── 03-end-to-end-flow.md
├── go.mod
├── cmd/study/main.go
└── pkg/
    ├── core/
    │   ├── types.go
    │   └── agent.go
    ├── tools/registry.go
    ├── session/store.go
    ├── gateway/gateway.go
    └── cron/scheduler.go
```

### 5. Write docs that map the real codebase to the teaching repo
Include:
- Source file → teaching module mapping
- Recommended reading order
- End-to-end flow from ingress → session → agent → tools → reply
- Python vs Go design tradeoffs

### 6. Write teaching-oriented Go code, not a fake “full port”
Use explicit abstractions:
- `struct` for domain models
- `interface` for external dependencies (`LLMClient`, `SessionStore`, `Tool`)
- clear comments about why the Go shape differs from Python

Good examples:
- `Message`, `ToolCall`, `Session`, `AgentConfig`
- `Tool` interface + `Registry`
- `SessionStore` interface
- `Gateway.HandleEvent`
- `Scheduler.Tick`

### 7. Add dense comments where users are likely learning language features
Specifically explain:
- custom string types + constants
- interface-based dependency inversion
- mutex usage (`sync.RWMutex`)
- why Go prefers explicit initialization over Python import-time registration
- why goroutines/channels would simplify some Python async/sync bridging patterns

### 8. Expect and fix Go package cycles
This is a common pitfall when turning a dynamic Python architecture into Go.

Observed issue:
- `core` imported `session`
- `session` imported `core`
- build failed with `import cycle not allowed`

Reusable fix:
- Move the storage interface (`SessionStore`) up into the `core` package
- Let `session.MemoryStore` implement `core.SessionStore`
- Keep `core` depending only on abstractions, not concrete packages

This is the right Go translation of the original architecture’s dependency direction.

### 9. Always run and format the prototype
After writing files:
```bash
gofmt -w ./cmd/study/main.go ./pkg/core/types.go ./pkg/core/agent.go ./pkg/tools/registry.go ./pkg/session/store.go ./pkg/gateway/gateway.go ./pkg/cron/scheduler.go
go run ./cmd/study
```
If it fails, fix the design problem instead of only patching syntax.

## Principles

### Teaching over completeness
Do not try to mirror all production features. Preserve the conceptual backbone.

### Stronger boundaries than the source language
Dynamic source languages often rely on `dict[str, Any]`, import-time side effects, and loosely typed payloads. In Go, prefer:
- explicit interfaces
- typed structs
- constructor-based initialization
- dependency inversion

### Show the correspondence explicitly
Users learning architecture benefit from “Python original → Go equivalent” tables and comments.

## Good final deliverable checklist

- [ ] Repo created in requested workspace
- [ ] README explains purpose and structure
- [ ] Docs cover reading map, language comparison, end-to-end flow
- [ ] Go code models the core architecture
- [ ] Comments explain both syntax and design choices
- [ ] Prototype compiles and runs
- [ ] Any major translation pitfall (like import cycles) is resolved and documented

## Common pitfalls

- Treating a study repo like a full production port
- Writing only docs with no runnable code
- Writing only code with no architecture guide
- Copying Python dynamic patterns directly into Go without redesign
- Ignoring import cycles instead of restructuring dependencies
- Failing to validate with `go run`
