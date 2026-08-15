# Feishu IM API: Sending Group Chat Text Messages

**Session:** 2026-06-21 cron run for Feishu 群聊早报
**Context:** The `daily-agent-briefing` skill was invoked to produce a "60秒读懂科技世界" group-chat morning briefing. After drafting the content, the message needed to be delivered to the target Feishu group chat (`oc_4d28fe1641ca214746ed49c02a4ee3d8`).

## What was missing

The skill's alternate format section mentions sending to Feishu but had no concrete script or API recipe for the IM message endpoint. The `feishu-sheets-api` skill only covers spreadsheet creation/writing, not chat messages.

## Working API flow

### 1. Obtain tenant access token

```python
import json, urllib.request

req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req, timeout=30) as r:
    resp = json.loads(r.read().decode())
token = resp["tenant_access_token"]
```

### 2. Send text message to group chat

```python
body = json.dumps({
    "receive_id": chat_id,               # e.g. "oc_4d28fe1641ca214746ed49c02a4ee3d8"
    "content": json.dumps({"text": msg}), # msg is plain UTF-8 text
    "msg_type": "text",
}).encode()

req = urllib.request.Request(
    "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    data=body,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as r:
    resp = json.loads(r.read().decode())
```

**Key details:**
- `receive_id_type=chat_id` query parameter is required.
- `content` must be a **JSON-stringified JSON object**: `json.dumps({"text": msg})`, not the raw string.
- `msg_type: "text"` sends plain text; for rich posts use `"post"`.
- The app must already be added to the target group chat, otherwise the API returns a permission error.

## Response verification

Success:
```json
{"code":0,"data":{"message_id":"om_...","chat_id":"oc_..."},"msg":"success"}
```

## Reusable script

See `scripts/send-feishu-group-msg.py` in this skill directory for a standalone CLI wrapper.

## Pitfall: no `feishu` tool in this environment

The `delegate_task` subagent attempted to use a `feishu` tool, but it does not exist in the available toolset. The fallback was raw `urllib` via `terminal('python3 /tmp/script.py')`, which succeeded. This confirms that for Feishu IM delivery in cron runs, a standalone Python script is the reliable path.
