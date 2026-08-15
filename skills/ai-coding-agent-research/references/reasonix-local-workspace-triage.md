# Reasonix Local Workspace / Session Triage

Use this when the user asks what their Reasonix desktop/project conversations are doing, especially phrases like “reasonix user-workspace 的几个会话什么进度”. This is local-state inspection, not web research.

## Key Local Paths Observed on macOS

Reasonix app data commonly lives under:

- `~/Library/Application Support/reasonix/`
- User workspace: `~/Library/Application Support/reasonix/user-workspace`
- Project session logs: `~/Library/Application Support/reasonix/projects/-Users-ss-Library-Application Support-reasonix-user-workspace/sessions/`
- Desktop tab state: `~/Library/Application Support/reasonix/desktop-tabs.json`
- Project/topic list: `~/Library/Application Support/reasonix/desktop-projects.json`
- Display/user-message index: `.../sessions/.display.json`

Do not rely only on filename search from `/Users/ss`; broad recursive search can time out. Start with the known app-support paths above once Reasonix is identified.

## Fast Triage Workflow

1. Read `desktop-tabs.json`.
   - It maps open tabs to `workspaceRoot`, `topicId`, `sessionPath`, model, and active tab.
   - This tells you which sessions are currently open and which one is active.
2. Read `desktop-projects.json`.
   - It maps the user workspace root to project `topicId`s.
3. Read `sessions/.display.json`.
   - This is a compact index of visible user prompts by session filename; use it to identify the topic without dumping huge JSONL logs.
4. Inspect the last messages in the relevant `.jsonl` session files.
   - Parse line-delimited JSON and summarize the last assistant/tool/user turns.
   - Look for final status, remote commands, “still running”, “results saved”, or “SSH timed out”.
5. Verify workspace artifacts directly.
   - For AutoResearchClaw-style work, check `artifacts/*/checkpoint.json`, `pipeline_summary.json`, specs under `docs/superpowers/specs/`, and experiment result folders.
   - Use artifact timestamps and counts to separate “conversation says it is running” from “files actually landed”.
6. Check local running processes only when progress depends on a local job.
   - Absence of local process does not prove a remote GPU job stopped; remote jobs may need SSH verification.

## What to Report

Summarize by conversation/topic, not by raw file names:

- Topic/session date or title.
- Current status: design complete, implementation pending, running, results present, blocked, or needs remote verification.
- Evidence: session file, artifact path, latest checkpoint/result count, or last message.
- Gaps: e.g. “local results exist but remote sweep final JSON not verified”, “spec reviewed but no implementation files found”.

## Pitfalls

- Do not treat `.jsonl` mtime alone as progress; read the last turns and verify artifacts.
- Do not expose secrets found in pasted SSH commands or session logs. Redact passwords/tokens in summaries.
- Do not claim remote experiment completion from local files unless the local files include the final expected artifact or you verified the remote path.
- Reasonix may have both global and project tabs; distinguish `global-workspace` from `user-workspace` before summarizing.

## Example Interpretation Pattern

If `pipeline_summary.json` says `final_stage: 8`, `final_status: done`, and `checkpoint.json` says `last_completed_stage: 8`, report: “pipeline reached Stage 8 / HYPOTHESIS_GEN; later stages have not run in this artifact set.”

If a session ends with “SSH timed out” after a remote run command, report: “remote job was launched, but final result was not verified; need to reconnect and check the remote results/log path.”
