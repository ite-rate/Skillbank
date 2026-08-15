---
name: maintaining-hermes-agent
description: Use when troubleshooting, configuring, routing work through, or modifying Hermes Agent behavior, especially gateway/platform delivery, model/provider selection, task-level model routing, cron/tool/provider issues, or safe maintenance requests.
level: manual
native_agent: Hermes
---

# Maintaining Hermes Agent

## Overview

Hermes maintenance should be config-first, evidence-backed, and minimally disruptive. Load `hermes-agent` for official commands and architecture, then use this skill to decide whether the work is configuration, runtime diagnosis, task-level model routing, or an authorized source change.

## When to Use

Use this for:
- Hermes configuration, provider/model picker, tools, cron, profiles, gateway, or platform behavior.
- Gateway/platform symptoms involving Feishu/Lark, Telegram, Slack, replies, threads, delivery placement, session keys, or cron delivery.
- Requests to use a different model/provider for one subtask while keeping the main conversation model unchanged.
- User-specific safety expectations around Hermes source edits, tests, builds, and service restarts.

Do not use this as a substitute for `hermes-agent`; it is a companion. Always load `hermes-agent` first when Hermes itself is involved.

## Core Rules

1. **Configuration first, source code last.** Inspect config/env/CLI/docs before proposing code edits.
2. **Evidence before diagnosis.** Separate inbound receipt, agent/model execution, outbound adapter delivery, and user-visible rendering.
3. **No unapproved disruption.** Do not modify Hermes source, run non-trivial builds/tests, or restart gateway/launchd services unless the user explicitly authorizes that action in the current conversation.
4. **Preserve user-visible intent separately from context intent.** A replied-to/quoted message may provide context without implying the bot response should be nested under that quote.
5. **Task-level routing is not a main-model switch.** If the user asks for one task on Gemini/Claude/DeepSeek/Qwen/etc., keep the current conversation as orchestrator and route only the subtask.

## Config-First Maintenance Workflow

1. Clarify the desired behavior in operational terms, separating UX expectation from implementation guess.
2. Inspect current state before editing:
   - `hermes config path`
   - `hermes config` or redacted `~/.hermes/config.yaml`
   - `hermes config env-path` and non-secret env names/flags when needed
   - `hermes gateway status`, `hermes cron list/status`, `hermes tools list`, or `hermes model --help` as relevant
3. Search for existing knobs: config keys, environment variables, CLI setup commands, platform adapter settings, or provider/catalog options.
4. Explain what exists versus what is missing. If no knob exists, propose a config-backed design before implementation.
5. If source changes are authorized, prefer minimal config-backed behavior over hard-coded patches. Add tests for default and new behavior.
6. Verify actual state after any change and state exactly what changed.

### Model/provider picker customization

When the user asks to hide/remove a model or provider from Hermes UI, first inspect supported config and picker commands. If no knob exists and source editing is authorized, prefer filtering picker payloads in `hermes_cli/inventory.py` rather than deleting provider implementations, credentials, or aliases.

Reference: `references/model-picker-hide-gemini.md`.

## Gateway Platform Debugging Workflow

1. Gather evidence from `~/.hermes/logs/` and `hermes gateway status`; classify the failure as inbound receipt, model/provider execution, outbound delivery, or rendering/thread placement.
2. For platform send failures, check credentials/config only after checking transport symptoms. For Feishu/Lark send failures, explicitly verify service-scoped proxy egress (`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`) and whether the local proxy port is listening.
3. Identify inbound metadata: `message_id`, `reply_to_message_id`, `thread_id`, `parent_id`, `root_id`, `chat_type`, plus platform-specific fields.
4. Trace metadata through:
   - `gateway/platforms/<platform>.py` inbound parsing
   - session-key construction (`gateway/session.py` or call sites)
   - `gateway/platforms/base.py` helpers such as `_reply_anchor_for_event()` and `_thread_metadata_for_source()`
   - platform adapter `send()` and API request bodies
5. Patch the smallest routing rule matching the platform/chat type and add adapter tests for the exact metadata behavior.
6. Run targeted tests first, then the full platform test file when practical. Ask before restarting live services.

### Common gateway symptoms

| Symptom | Inspect first |
| --- | --- |
| Message received but no visible reply | outbound `reply_to`, `thread_id`, platform reply API behavior |
| `history=0` unexpectedly | session key split by thread/message id |
| Cron failed before delivery | provider/model execution logs before messaging adapter |
| Feishu send/reaction `ProxyError` or `Connection refused` | local proxy listener and launchd service env |
| Reply appears under an old message | inbound reply fields promoted to thread metadata or outbound reply anchor |
| No typing feedback | adapter `send_typing()` / platform typing support |

### Cron provider/model routing pitfalls

- Cron jobs can pin their own `provider`/`model`; do not assume they use the active chat model from `~/.hermes/config.yaml`.
- When a cron error says `No LLM provider configured`, compare three layers before changing anything: `hermes cron list --all`, `~/.hermes/cron/jobs.json` redacted fields (`provider`, `model`, `base_url`), and available credentials in `hermes config check` / `.env` variable names.
- If the user asks to move a job to Kimi and `KIMI_API_KEY` exists, prefer Hermes' canonical Kimi provider (`kimi-coding`) and a model from the local Hermes model catalog, not stale OpenRouter aliases such as `openrouter/kimi-latest`.
- `hermes cron run <job_id>` queues the job for the scheduler tick; verify completion via `last_run_at`/`last_status` and a new file under `~/.hermes/cron/output/<job_id>/`, not just by seeing `next_run_at` change.
- If manual cron trigger does not produce output but the provider works, run the same cron prompt as a one-shot with the pinned provider/model to unblock the user, then report that the scheduler path still needs diagnosis.

### Feishu/Lark lessons

- In Feishu DMs, reply UI fields (`parent_id`, `root_id`, `reply_to_message_id`) may be quote context, not a request for threaded delivery.
- Preserve quoted text for model context while suppressing DM outbound reply anchors when main-chat delivery is desired.
- Do not globalize Feishu DM behavior to Telegram DM topics or real group threads.
- For Markdown readability/rendering problems, treat outbound payload shape as the first suspect. Preserve normal Markdown in Feishu `post` + `md` payloads; do not solve by stripping headings, separators, bold, bullets, ordered lists, or tables at the prompt layer.
- Markdown tables used in briefings (for example `属于啥 | 名字 | 干啥的简介`) should not be downgraded to `msg_type="text"` merely because table rendering may be imperfect; raw Markdown source is worse for readability.
- A running gateway may need a restart to pick up code changes; ask before restarting.

## Skill Hygiene & Cleanup

When the user reports skill bloat, low-quality auto-generated skills, or token waste from skill descriptions:

1. **Diagnose**: Check `~/.hermes/skills/.usage.json` for `use_count=0` skills, scan top-level dirs for missing `SKILL.md` (stubs), and check for duplicate symlinks (`ls -la ~/.hermes/skills/ | grep '^l'`).
2. **Delete stubs**: `rm -rf` top-level dirs with no `SKILL.md` (safe — they have no real skill content). Verify no duplicate exists in the correct category dir first.
3. **Disable never-used skills**: Add `use_count=0` skill names to `config.yaml` → `skills.disabled` list. Back up config first. Takes effect on next `/reset`.
4. **Measure impact**: Check `~/.hermes/.skills_prompt_snapshot.json` for total skills injected and description bytes saved.

Full workflow with commands and code: `references/skill-hygiene-cleanup.md`.

References:
- `references/feishu-dm-reply-main-chat.md`
- `references/feishu-proxy-egress-failure.md`
- `references/feishu-markdown-post-rendering.md` — preserve Markdown tables and normal Markdown via Feishu `post`/`md` instead of downgrading to text
- `references/provider-fallback-pipeline.md` — retry loop, error classifier, fallback chain internals
- `references/cron-max-iterations-error-pattern.md` — when cron job fails with `RuntimeError: <content>` and the content is the agent's output, check for `max_iterations_reached(90/90)` in logs
- `references/skill-hygiene-cleanup.md` — diagnose and clean up skill library: stub dirs, duplicate symlinks, never-used skills, token impact measurement

## Per-Task Model Routing

Use this when the user asks to use another model/provider for one task without changing the main/default model.

Trigger phrases include:
- “这个任务用 Gemini / Google 做”
- “不要切主模型”
- “任务中切到谷歌模型”
- “GPT 讲，Gemini 生成前端/demo”
- “某一步用另一个模型”
- “per-task model / subtask model / one-shot model”

Flow:
1. Confirm the subtask boundary in one short sentence.
2. Keep the current main model as orchestrator.
3. Invoke the requested model/provider as a one-shot/subtask where possible.
4. Capture the output back into the current session.
5. Verify returned output or saved files before claiming success.

CLI patterns:

```bash
hermes -z "TASK" --provider gemini --model gemini-2.5-flash
hermes -z "TASK" --provider google-gemini-cli --model gemini-2.5-flash
```

Provider distinction:
- `gemini` = Google AI Studio API key provider
- `google-gemini-cli` = Google Gemini OAuth / Code Assist provider

Pitfalls:
- Do not recommend `hermes model` when the user requested temporary task-level routing.
- Do not treat provider setup as equivalent to routing strategy.
- Prefer one-line copy-pasteable commands over fragile multi-line continuations.
- If a Code Assist/OAuth Gemini route is quota-limited or flaky, try the configured AI Studio API-key route separately before declaring Gemini unusable.

## Safety and Secret Handling

- Do not print Feishu app secrets, tokens, webhook URLs, cookies, credentials, or connection strings from config/logs. Redact as `[REDACTED]`.
- Do not store secrets in memory or skills.
- If an accidental source edit happens without authorization, revert immediately and verify `git status --short`.

## Verification Checklist

Before finalizing:
- Was `hermes-agent` loaded first?
- Were config/env/CLI knobs checked before code?
- Were source edits, builds/tests, and restarts authorized before running?
- If the issue is gateway-related, was it classified by inbound/model/outbound/rendering layer?
- If routing another model, was the subtask result captured and verified?
- If anything changed, was the actual state verified and summarized?
