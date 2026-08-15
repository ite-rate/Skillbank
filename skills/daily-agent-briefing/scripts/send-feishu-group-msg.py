#!/usr/bin/env python3
"""
Send a plain-text message to a Feishu (Lark) group chat via the IM API.

Prerequisites:
  - FEISHU_APP_ID and FEISHU_APP_SECRET set in environment
  - The app has been added to the target group chat

Usage:
  python3 send-feishu-group-msg.py <chat_id> <message_file>

Example:
  python3 send-feishu-group-msg.py oc_4d28fe1641ca214746ed49c02a4ee3d8 /tmp/morning_briefing.txt
"""

import json, os, sys, urllib.request


def get_tenant_token():
    app_id = os.environ["FEISHU_APP_ID"]
    app_secret = os.environ["FEISHU_APP_SECRET"]
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read().decode())
    if resp.get("code") != 0:
        raise RuntimeError(f"Token error: {resp}")
    return resp["tenant_access_token"]


def send_text(chat_id, text, token):
    body = json.dumps({
        "receive_id": chat_id,
        "content": json.dumps({"text": text}),
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
    return resp


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 send-feishu-group-msg.py <chat_id> <message_file>")
        sys.exit(1)

    chat_id = sys.argv[1]
    msg_path = sys.argv[2]

    with open(msg_path, "r", encoding="utf-8") as f:
        text = f.read()

    token = get_tenant_token()
    resp = send_text(chat_id, text, token)

    if resp.get("code") == 0:
        print(f"Sent OK. message_id={resp['data']['message_id']}")
    else:
        print(f"Send failed: {resp}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
