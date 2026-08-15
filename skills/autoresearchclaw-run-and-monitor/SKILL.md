---
name: autoresearchclaw-run-and-monitor
description: Run AutoResearchClaw/ResearchClaw safely, validate config, launch a background research job, and monitor progress when stdout/logs are initially empty.
level: manual
native_agent: Hermes
---

# AutoResearchClaw: run and monitor

Use this skill when the user wants to execute a research task through an existing AutoResearchClaw / ResearchClaw checkout and you need grounded status updates.

## When to use

- A local project directory already exists (for example `~/.../AutoResearchClaw`)
- The user wants the tool to actually run a literature/paper pipeline
- You need phased progress updates rather than just a fire-and-forget command
- The pipeline may be quiet at startup and not emit useful stdout immediately

## Preconditions

1. Confirm the CLI exists, usually one of:
   - `.venv/bin/researchclaw`
   - `researchclaw` on PATH
2. Confirm config exists, typically `config.arc.yaml`
3. Confirm the configured ACP agent exists (e.g. `codex`)
4. Prefer read-only health checks before launching a full run:
   - `researchclaw --help`
   - `researchclaw doctor`
   - `researchclaw validate --config config.arc.yaml`

## Launch pattern

Run from the repository root.

```bash
.venv/bin/researchclaw run --config config.arc.yaml --topic "<user topic>" --auto-approve
```

If the run may take a while, launch it as a background process and keep the session ID.

## Monitoring workflow

### 1) Check the Hermes background process first

Use process tools:
- `process wait` for a short interval
- `process poll` to confirm it is still running
- `process log` to capture stdout/stderr if available

### 2) If no stdout appears, verify the OS process directly

Inspect the PID with shell tools:

```bash
ps -p <pid> -o pid=,ppid=,etime=,stat=,command=
pgrep -P <pid>
```

This is important because ResearchClaw may still be actively working even when Hermes sees no line-buffered output.

### 3) Inspect child processes

If a child like `acpx`, `codex`, or another ACP agent exists, the pipeline has likely entered LLM orchestration rather than failing immediately.

Typical useful command:

```bash
ps -o pid=,ppid=,etime=,stat=,command= -p $(pgrep -P <pid> | tr '\n' ',' | sed 's/,$//')
```

### 4) Check artifacts, but do not assume immediate disk output

Search under `artifacts/` for:
- `checkpoint.json`
- `heartbeat.json`
- stage folders
- new `rc-*` directories

If none appear yet, report that the run is still likely in early planning/agent-calling stages.

## Important finding from experience

AutoResearchClaw may:
- pass `doctor` and `validate`
- launch successfully
- start ACP/Codex child processes
- produce **no immediate stdout**
- produce **no immediate new artifacts**

Do **not** prematurely conclude failure in that state. First confirm:
- parent process still alive
- child ACP/agent process exists
- no early exit code has occurred

## Reporting template

Give the user a phased update including:

- exact launch command
- whether the background process is alive
- whether child ACP/Codex processes exist
- whether new artifacts/checkpoints have appeared yet
- best current interpretation of the phase (e.g. topic scoping / planning / literature discovery)

Example structure:

- Started successfully
- Current status: running
- Evidence: parent PID alive, ACP child active
- Artifacts: none yet / checkpoint found / stage files found
- Interpretation: likely in early orchestration or planning stage

## Safety / scope

- If the user says "do not modify files," limit actions to read-only checks and avoid `run`
- If the user explicitly asks to execute the research task, running the pipeline is in scope
- Avoid editing `config.arc.yaml` unless the user asks

## Common commands

```bash
.venv/bin/researchclaw --help
.venv/bin/researchclaw doctor
.venv/bin/researchclaw validate --config config.arc.yaml
.venv/bin/researchclaw run --config config.arc.yaml --topic "<topic>" --auto-approve
ps -p <pid> -o pid=,ppid=,etime=,stat=,command=
pgrep -P <pid>
```

## Pitfalls

- `pip show researchclaw` may not find anything even when the local venv CLI exists and works
- Empty Hermes `process log` output does not imply the run failed
- Searching `artifacts/` too early can show only old runs; do not misreport those as the current run
- `experiment.mode: ssh_remote` means later stages may depend on remote connectivity and can take time before local outputs appear
- `researchclaw run --help` currently exposes `--from-stage` but **not** a `--to-stage` / stop-at-stage flag. If the user wants to stop after stage 11 (or any intermediate stage), do not promise a native flag exists.

## Workaround: stop after a target stage

When the user wants the pipeline to stop after a specific stage (for example stage 11 so they can audit planning outputs before experiment execution), use a monitor-and-stop workflow:

1. Launch the run normally in the background and keep the Hermes session/process ID plus OS PID.
2. Create a cron monitor (or equivalent periodic checker) that inspects the newest matching `artifacts/rc-*` run.
3. Identify the correct run conservatively:
   - prefer `heartbeat.json.pid == <target pid>` when available
   - confirm `checkpoint.json.run_id` / `heartbeat.json.run_id`
   - among candidates, prefer the run with the newest `heartbeat.json` / `checkpoint.json` timestamps
   - if several `rc-*` directories exist, do **not** assume the newest directory name is the active run without checking heartbeat/checkpoint evidence
4. Read both `checkpoint.json` and `heartbeat.json`.
5. Gate on `checkpoint.json.last_completed_stage` for the cutoff decision. If `checkpoint.last_completed_stage < <target_stage>`, exit silently.
6. If `checkpoint.last_completed_stage >= <target_stage>`, stop the main `researchclaw` PID **if it is still running**. If the process already exited, report that fact rather than treating it as an error.
7. If `heartbeat.json.last_stage` is already `> <target_stage>` (for example stage 12 started), still perform the audit **only on artifacts up to the requested cutoff**.
8. Audit the relevant stage outputs directly from disk; for stage-11 planning audits this usually means reading stage 01-11 artifacts plus `pipeline_summary.json`.
9. Remove the cron job after delivery so it does not keep sending updates.

### Stage-11 audit lessons learned

For "stop after planning" requests, the most failure-prone points are:

- **Stage 03 search-plan drift**: query lists can degrade into fragments or raw user text; audit the actual `queries.json`, not just whether source APIs were reachable.
- **Stage 04 reference contamination**: check whether `search_meta.json` says `real_search: false`, whether `web_context.md` is on-topic, and whether `references.bib` contains domain-relevant papers rather than generic ML citations.
- **Stage 05-06 evidence collapse**: a shortlist/cards set that only contains generic MARL background papers is insufficient for a DSA/OSA research audit.
- **Stage 07-09 idea/evidence mismatch**: synthesis and hypotheses may look strong even when the retrieval stages are weak; explicitly call out when downstream reasoning outperforms the upstream evidence chain.
- **Stage 09-11 environment inconsistency**: compare hardware/domain assumptions across stages (for example local Apple/MPS vs later assumed NVIDIA GPU) and treat mismatches as planning risk.
- **Stage 10 validator contamination**: if the validation report references an unrelated RL environment/task (for example `ant` continuous control in a D-DSA project), treat code-generation reliability as compromised even if the stage decision says `proceed`.

This workaround is reusable for 'run until planning only', 'stop before remote experiment', and similar partial-pipeline requests.
