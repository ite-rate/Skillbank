---
name: html-architecture-explorer
description: Build a static HTML/CSS/JS repository that explains a codebase or system architecture in a human-readable way using overview sections, flow/timeline views, module cards, and source-to-abstraction mappings. Prefer this when the user finds direct code reading too slow.
level: manual
native_agent: Hermes
version: 1.0.0
license: MIT
---

# HTML Architecture Explorer

Use this skill when a user wants a **more human-readable way to understand a codebase or system** than reading source files directly. The output is a **static repo** (HTML/CSS/JS) that can be opened locally without a framework.

## When to use

Trigger when the user says things like:
- “看这个效率太低” / “this is too slow to read”
- “Can you make this visual?”
- “Build a repo/site to explain the system”
- “Use HTML as the base”
- “I want a human-readable architecture explorer”

Especially useful for:
- agent runtimes
- distributed systems
- multi-module apps
- any codebase with flow + boundaries + component relationships

## Core idea

Do **not** start from implementation details.
Instead present the system in this order:
1. **Architecture overview**
2. **Runtime flow / sequence**
3. **Module cards**
4. **Source-to-abstraction mapping**
5. **Complexity split** (core ideas vs real-world engineering overhead)
6. Only then point back to source files

This is almost always easier for humans than starting from code.

## Deliverable shape

Create a repo like:

```text
<repo>/
├── index.html
├── assets/
│   ├── styles.css
│   └── app.js
├── docs/
│   └── notes.md
└── README.md
```

## Recommended page sections

### 1. Hero / framing
Explain what the system *is* in one sentence.
Example:
> “This system is not just a chatbot UI — it is an LLM runtime with tools, state, gateways, and scheduling.”

### 2. Architecture overview
Show the main modules and their relationships.
Use cards or nodes for:
- Inputs
- Gateway / entry layer
- Session / state layer
- Agent loop / orchestrator
- Tool registry / execution
- Outputs
- Cron / scheduler

### 3. Sequence / runtime flow
Add tabs when there are multiple entry paths, e.g.:
- normal user message
- cron/scheduled task

### 4. Module cards
For each module, include only:
- responsibility
- inputs
- outputs
- dependencies

### 5. Source mapping table
Map real files to conceptual abstractions.
Columns should be something like:
- source file
- abstract concept
- simplified implementation location
- how to read it

### 6. Complexity split
Separate:
- the simple core idea
- the messy real-world engineering complexity

This reframing is often the moment the user finally “gets it.”

## Styling guidance

A dark, high-information, product-style UI works well. A Linear/Vercel-like visual language is a good default for architecture explorers:
- dark background
- restrained accent color
- cards with subtle borders
- compact top nav
- large headline
- monospace only for paths/code

If the `popular-web-designs` skill is available, load a suitable template (Linear works well for system visualizations).

## Interaction guidance

Useful minimal interactions:
- click an architecture node → highlight corresponding module card
- tabs for alternate flows (message path vs cron path)
- anchor nav for major sections

Keep interactions lightweight; avoid frameworks unless the user asks.

## Important execution rule

Unless the user explicitly asks you to preview/serve/run it, **only write the repo files**.
Do **not** automatically start a local server, build process, or runtime.
If you need verification, prefer static inspection of files first. Only run/serve when the user wants it.

## Suggested workflow

1. Read enough source/docs to identify the 4-7 true core modules.
2. Distill the architecture into plain language before writing HTML.
3. Create the static repo skeleton.
4. Write `README.md` with opening instructions.
5. Write `index.html` with the sections above.
6. Write `assets/styles.css` for a clean information-dense layout.
7. Write `assets/app.js` only for lightweight UI interactions.
8. If the user did not ask for runtime preview, stop after file creation and summarize paths.
9. If the user asks, then run a local server or open in browser.

## Pitfalls

- Don’t make the page a wall of prose; architecture explorers should be scannable.
- Don’t over-focus on implementation trivia before giving the big picture.
- Don’t use heavy frontend frameworks unless needed.
- Don’t auto-run the site if the user said not to build/run it.
- Don’t treat cron as a separate “brain” if it actually reuses the main runtime path.

## Good final summary to the user

Include:
- repo path
- what sections exist
- whether it has been run or **not run**
- exact next step they can use to open or preview it later

Example:
> “I created the static HTML explorer at `<path>`. It includes architecture overview, runtime sequence, module cards, and source mapping. Per your instruction, I did not run or serve the project.”
