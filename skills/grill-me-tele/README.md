# grill-me

A tiny Claude Code skill that makes the agent **interview you relentlessly** about a
plan or design *before* writing any code — one question at a time, each with a
recommended answer, walking down every branch of the decision tree until you and the
agent share the same understanding.

Original by Matt Pocock — https://github.com/mattpocock/skills
(`skills/productivity/grill-me`). Reproduced verbatim here for easy distribution.

## When it triggers

Say something like "grill me", "stress-test this plan", or "get me grilled on this
design", and the agent flips from answering to interrogating.

## Install (Claude Code)

Drop the `grill-me/` folder into your skills directory:

```bash
# User-level (available in every project)
mkdir -p ~/.claude/skills
cp -R grill-me ~/.claude/skills/grill-me

# — or — Project-level (only this repo)
mkdir -p .claude/skills
cp -R grill-me .claude/skills/grill-me
```

Then restart Claude Code (or start a new session). It auto-discovers any folder
under `skills/` that contains a `SKILL.md`.

## Install (other agents)

A "skill" here is just the `SKILL.md` file — YAML frontmatter (`name` +
`description`) plus a plain-text instruction body. To use it in another agent:

- **Folder-based agents (Copilot CLI, etc.):** copy the `grill-me/` folder into that
  agent's skills directory the same way as above.
- **Anything else:** paste the body of `SKILL.md` into the system prompt, or hand the
  agent the file and tell it to follow those instructions. No scripts, no
  dependencies, no API keys — it's pure prompt.

## Contents

```
grill-me/
├── SKILL.md   # the skill itself (this is the only required file)
└── README.md  # this file
```
