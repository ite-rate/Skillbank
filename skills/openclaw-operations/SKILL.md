---
name: openclaw-operations
description: Use when configuring, troubleshooting, or verifying OpenClaw installations, gateway services, messaging channels, App IM integrations, or OpenClaw CLI state on a remote machine.
level: manual
native_agent: Hermes
---

# OpenClaw Operations

## Overview

OpenClaw maintenance is CLI/schema-first: identify the installed package and active profile, inspect `openclaw config schema`, make minimal config changes, validate, then verify the gateway/channel layer with logs and status probes. Treat secrets as write-only and redact them in every transcript.

## When to Use

Use this for:
- Remote OpenClaw setup on a VPS or cloud host.
- Connecting messaging channels such as Feishu/App IM, ClickClack, Telegram, QQBot, Matrix, or Slack.
- Diagnosing `openclaw gateway`, `channels`, `config`, `secrets`, `doctor`, or systemd/launchd service behavior.
- Mapping a user's vague product name such as “App IM” to the actual OpenClaw channel schema.

Do not use this for Hermes Agent configuration; use `hermes-agent` and `maintaining-hermes-agent` instead.

## Safe Discovery Workflow

1. Connect and identify runtime:
   - `openclaw --version`
   - `openclaw status`
   - `npm list -g --depth=0 | grep openclaw`
   - inspect `~/.openclaw/`, process list, systemd user services, and containers.
2. Inspect command surfaces before editing:
   - `openclaw channels --help`
   - `openclaw channels add --help`
   - `openclaw config --help`
   - `openclaw config schema`
   - `openclaw channels list --all`
3. Locate the active config with `openclaw config file`; back it up before writes.
4. Use `openclaw config set/unset/patch` rather than hand-editing JSON unless the CLI cannot express the change.
5. Run `openclaw config validate` after changes.
6. Restart or install the gateway only when the user asked for a running integration or explicitly approved service changes.
7. Verify with channel status/logs and the actual gateway service status before claiming success.

## Channel Mapping Quick Reference

OpenClaw channel names are schema-driven; do not infer from marketing names alone.

- `feishu`: fields include `appId`, `appSecret`, and optional `encryptKey`; use for Feishu/Lark-style app credentials and App IM where the app credentials match this shape.
- `clickclack`: uses `token`; do not try to place appId/appSecret credentials here.
- `qqbot`: uses `appId` and `clientSecret`, not `appSecret`.
- `matrix`: has `encryption`; default may be false depending on config.
- `discord` voice has `daveEncryption`, which is unrelated to Feishu/App IM callback encryption.

If the user's screenshot or wording says “App IM” but the given credentials are `appid` + `appsecret`, inspect the schema before deciding. In the 2026.6.x CLI, the exact `appId`/`appSecret`/`encryptKey` combination maps to `channels.feishu`.

## Feishu/App IM Pattern

For a Feishu/App IM websocket integration where the user says not to enable encryption:

1. Set credentials:
   - `openclaw config set channels.feishu.enabled true --strict-json`
   - `openclaw config set channels.feishu.appId '"APP_ID"'`
   - `openclaw config set channels.feishu.appSecret '"APP_SECRET"'`
2. Prefer websocket mode unless the user explicitly provides webhook callback settings:
   - `openclaw config set channels.feishu.connectionMode '"websocket"'`
3. Ensure callback encryption is not configured:
   - `openclaw config unset channels.feishu.encryptKey || true`
4. Validate:
   - `openclaw config validate`
5. Verify without exposing secrets:
   - Show `enabled`, `appId`, `connectionMode`, and whether `appSecret` is set; never print the secret.

## Liangzimixin / QuantumIM Plugin Pattern

Use this when the user says the App IM is not a built-in OpenClaw IM and provides instructions like `openclaw plugins install liangzimixin@latest`, `openclaw configure`, and choosing `Local`.

1. Do **not** force the credentials into `channels.feishu` just because they are named `appId/appSecret`. First install and inspect the plugin:
   - `openclaw plugins install liangzimixin@latest`
   - `openclaw plugins list`
   - inspect `~/.openclaw/npm/projects/liangzimixin/node_modules/liangzimixin/openclaw.plugin.json` or `dist/openclaw.plugin.json`.
2. The plugin channel id is `liangzimixin`; configure `channels.liangzimixin`, not `channels.feishu`.
3. Typical config fields from the 0.3.x manifest:
   - `appId`: required application ID.
   - `appSecret`: required application secret; never print it.
   - `env`: `production`, `staging`, or `test`; default to `production` unless the user says otherwise.
   - `encryptionMode`: runtime config accepts only `quantum_and_plain` or `quantum_only`; use `quantum_and_plain` when the user says not to require quantum-encrypted messages.
   - Do **not** write the interactive wizard choice `not_enabled` into JSON directly. In plugin 0.3.x, `not_enabled` is a CLI/setup choice that maps internally to `encryptionMode: "quantum_and_plain"` plus no `quantumAccount`; writing `not_enabled` causes `AccountConfigSchema.safeParse` to fail and the channel account will not start.
   - `quantumAccount`: optional; **filling it enables the quantum encryption module**, so omit/unset it when the user says not to enable quantum encryption.

   ## Kimi Code vs Moonshot provider

   When using a `sk-kimi-...` Kimi Code API key from `https://www.kimi.com/code/docs/`, do **not** configure it as Moonshot (`moonshot/...`) or call `https://api.moonshot.cn/v1`; that returns `401 Invalid Authentication` because Kimi Code uses a separate endpoint/provider.

   Use OpenClaw's built-in Kimi Coding provider:

   - Provider prefix: `kimi`
   - Auth env/profile: `KIMI_API_KEY` or `KIMICODE_API_KEY`
   - Model ref: `kimi/kimi-for-coding`
   - Kimi Code OpenAI-compatible Base URL: `https://api.kimi.com/coding/v1`
   - Kimi Code Anthropic-compatible Base URL: `https://api.kimi.com/coding/`

   Useful commands:

   ```bash
   printf '%s\n' "$KIMI_API_KEY" | openclaw models auth paste-api-key --provider kimi --profile-id kimi:manual
   openclaw models set kimi/kimi-for-coding
   openclaw models list --provider kimi
   openclaw models status --plain
   openclaw gateway restart
   ```

   Kimi Code may reject generic direct HTTP clients for `/chat/completions` with `403 access_terminated_error` saying it is only available for Coding Agents. That does not mean the key is invalid if `/coding/v1/models` succeeds; use OpenClaw's built-in `kimi` provider so the request is sent as a supported coding agent. Do not spoof/change User-Agent manually because Kimi docs warn that tampering with client identity can suspend benefits.
4. If a previous attempt misconfigured built-in Feishu, disable or clean it so only the plugin channel is active:
   - set `channels.feishu.enabled=false` or remove the mistaken channel config after backing up the config.
5. `openclaw configure --section channels` may not list external plugin channels even when `plugins list` shows the plugin enabled. In that case, write `channels.liangzimixin` directly, validate, and verify via gateway logs.
6. Validate and restart:
   - `openclaw config validate`
   - `openclaw gateway restart`
7. Verify with journal/log evidence, not only JSON validation. Look for lines like:
   - `[liangzimixin:runtime] plugin runtime initialized`
   - `[liangzimixin:plugin] plugin registered (v2 path) ✓`
   - `http server listening (... liangzimixin ...)`
   - `gateway ready`

See `references/liangzimixin-quantumim.md` for a concrete 2026.6.8 setup pattern and pitfalls.

## Gateway Service Pattern

If no gateway is running and the user wants the integration live:

1. Inspect `openclaw gateway --help` and `openclaw gateway install --help` for the installed version.
2. Set minimal local gateway config when missing:
   - `openclaw config set gateway.mode '"local"'`
   - `openclaw config set gateway.port 18789 --strict-json`
   - `openclaw config set gateway.bind '"loopback"'`
3. Install/start the service with the CLI's supported service manager:
   - `openclaw gateway install --force --port 18789`
   - `openclaw gateway start`
4. If token auth is enabled, remember that status/probe commands may need device pairing or a token; distinguish “gateway running but probe unauthenticated” from “gateway down”.
5. Verify with process/listener evidence plus OpenClaw status/logs.

## Secret Handling

- Never echo app secrets, tokens, passwords, or generated gateway tokens into final replies.
- Prefer SecretRef/file/env providers if the OpenClaw version supports them cleanly; otherwise redact config output aggressively.
- If a shell command includes secrets, avoid persisting it in shell history where possible and do not quote it back in summaries.
- Do not save user-provided secrets in memory or skill references.

## Common Pitfalls

- **Assuming App IM is ClickClack.** ClickClack uses a bot token; appId/appSecret belongs elsewhere.
- **Setting `encryptKey` after the user says not to enable encryption.** For Feishu websocket mode, omit `encryptKey`; webhook mode may require it.
- **Claiming success after config validate only.** Validation proves shape, not connectivity. Check channel status/logs and gateway process state.
- **Misreading unauthenticated probes.** `requires credentials before opening a websocket` can mean the local CLI lacks gateway auth/device pairing while the service itself is running.
- **Overwriting a fresh config without backup.** Always copy `~/.openclaw/openclaw.json` before major writes.

## Reference Notes

- `references/app-im-feishu-websocket.md` captures a concrete 2026.6.8 remote setup pattern and schema findings without storing secrets.
- `references/linux-gateway-installation.md` covers installing OpenClaw Gateway on Linux servers (Ubuntu, cloud VPS) via the official install script, Node.js setup, PATH configuration, and post-install verification.
