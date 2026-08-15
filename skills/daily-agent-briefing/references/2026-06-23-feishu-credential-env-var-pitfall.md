# Feishu IM API Credential Environment Variable Pitfall

**Session:** 2026-06-23 cron run for Feishu 群聊早报
**Context:** The `send-feishu-group-msg.py` script failed with `{'code': 10014, 'msg': 'app secret invalid'}` repeatedly, even though the environment variable `FEISHU_APP_SECRET` was confirmed to exist.

## Root cause

The `FEISHU_APP_SECRET` environment variable was set in the shell session with a **wrong value** (likely an old/rotated secret). The script correctly read the variable, but the value itself was rejected by the Feishu API.

**Key trap:** `app secret invalid` means the secret was successfully transmitted but does not match the app ID. It is NOT a "missing env var" error. Do not confuse this with unset variables.

## Diagnostic steps that worked

1. Verify the env var exists: `python3 /tmp/check_env.py` (prints `True`, `True`, `32`, `cli_a95c2f...`)
2. Verify the value length matches Feishu secrets (32 chars)
3. If still invalid, the secret itself is wrong — **regenerate or retrieve the correct one from the Feishu Open Platform console**

## How to set the correct secret in a cron/headless environment

**Option A: Export in the cron job command itself (most reliable)**
```bash
FEISHU_APP_SECRET="the_...et" python3 /path/to/send-feishu-group-msg.py <chat_id> <msg_file>
```

**Option B: Write to a persistent env file sourced by the cron shell**
```bash
# ~/.feishu_env
export FEISHU_APP_ID="cli_a95c2f98a3b89cb0"
export FEISHU_APP_SECRET="the_...et"
```
Then in cron: `source ~/.feishu_env && python3 /path/to/send-feishu-group-msg.py ...`

**Option C: Use launchctl (macOS, but transient)**
```bash
launchctl setenv FEISHU_APP_SECRET "the_actual_correct_secret"
```
Note: This only affects newly launched processes in the current GUI session. Cron jobs running in a different context may not inherit it. Prefer Option A for cron reliability.

## What NOT to do

- Do NOT repeatedly retry the same command with the same wrong secret — this wastes API calls and hits tool loop warnings.
- Do NOT assume `app secret invalid` means the variable is missing. Check the value first.
- Do NOT use `launchctl setenv` as the primary cron credential mechanism on macOS; it is session-scoped and unreliable for background cron jobs.

## Verification after fix

```bash
FEISHU_APP_SECRET="corr...et" python3 send-feishu-group-msg.py oc_4d28fe1641ca214746ed49c02a4ee3d8 /tmp/morning_briefing.txt
```

Expected success response:
```json
{"code":0,"data":{"message_id":"om_...","chat_id":"oc_..."},"msg":"success"}
```
