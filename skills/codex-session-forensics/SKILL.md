---
name: codex-session-forensics
description: Trace a user-referenced Codex conversation/session back to the underlying project path, especially when the user only remembers a topic (e.g. mysql) or a vault/repo name. Use this when searching Codex history, session JSONL files, or shell snapshots to identify the exact session and workspace.
level: manual
native_agent: Hermes
version: 1.0.0
license: CC0-1.0
---

# Codex Session Forensics

Use this when the user asks you to find a past/current Codex conversation, especially one tied to a topic, repo, or vault path, but the exact session id is unknown.

## When to use
- The user says “that Codex session about X” or “the MySQL one”
- The user remembers a repo/vault name but not the session id
- `session_search` returns broad or misleading matches
- You need to map a Codex history entry back to the actual workspace path

## Core workflow

1. **Start broad with `session_search`**
   - Search with OR queries around the topic, repo, and likely synonyms.
   - Example: `mysql OR MySQL OR repository OR obsidian OR vault`
   - If the user gave a session id, search it too, but do not assume `session_search` can resolve it directly.

2. **Search local Codex session files**
   - Look in `~/.codex/sessions/**.jsonl` for the keywords.
   - If you know a likely session id, search for that id in the filename pattern.
   - Session files often contain a `session_meta` object at the top with the real `cwd`.

3. **Inspect the top of the matching session JSONL**
   - Read the first lines of the session file.
   - Extract:
     - `cwd`
     - `current_date`
     - `model`
     - `originator`
   - This usually reveals the actual project path faster than the body of the conversation.

4. **Use repo/file clues to confirm**
   - Read README / workspace docs / node index files in the located `cwd`.
   - Confirm the topic by checking the project’s own docs and recent git log if needed.

5. **If the user mentions a vault or learning system**
   - Search for the vault name in the Codex session files *and* in the vault itself.
   - Common clues include `README.md`, `WORKSPACE.md`, `NODES/INDEX.md`, `STATE.yaml`, or similar structural docs.
   - The vault path may differ from the topic path; do not assume the user’s remembered vault name is the active workspace.

## Practical heuristics
- Search files under `~/.codex/sessions` first when you need a concrete workspace path.
- `session_search` summaries are useful for orientation, but the JSONL `session_meta` line is the source of truth for `cwd`.
- A session can mention one vault or repo in conversation while actually running in a different workspace directory; verify before concluding.
- If you see a project tree like `Projects/mysql`, inspect the project root docs before searching elsewhere.

## Pitfalls
- **Do not rely on `session_search` with a raw session id alone**; it may return nothing.
- **Do not assume the user’s remembered vault is the active workspace**.
- **Do not stop at a summary** when you need the exact path; read the session file header.
- **Do not confuse conversation topic with workspace root**; they can diverge.

## Verification
Before replying, verify at least one of:
- the `cwd` from `session_meta`
- a matching README/WORKSPACE/NODES document in that path
- a git log or file listing that confirms the repository/project identity

## Result format
When reporting back, be explicit:
- session id
- workspace path
- why you think it matches
- any uncertainty if the topic and workspace diverge
