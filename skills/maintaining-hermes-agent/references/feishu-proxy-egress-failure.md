# Feishu outbound failures caused by Hermes gateway proxy egress

Use when Feishu/Lark messages are received or processed but replies/reactions do not appear, especially on macOS launchd gateways with service-scoped proxy vars.

## Symptom pattern

Logs show Feishu send/reaction failures while the gateway process remains running:

```text
requests.exceptions.ProxyError: HTTPSConnectionPool(host='open.feishu.cn', port=443)
Unable to connect to proxy
HTTPSConnection(host='127.0.0.1', port=6922): Failed to establish a new connection: [Errno 61] Connection refused

ERROR Lark: receive message loop exit, err: no close frame received or sent
```

This means Hermes was alive, but outbound egress to Feishu was blocked because its configured local proxy was not listening at that moment. The failure can break reply delivery, reaction delivery, tenant token refresh, and sometimes the Feishu receive websocket loop.

## Read-only diagnosis

1. Check gateway/service state:

```bash
hermes gateway status
launchctl print gui/$(id -u)/ai.hermes.gateway 2>&1 | sed -n '1,140p'
ps -axo pid,ppid,user,etime,comm,args | egrep 'hermes_cli.main gateway|hermes gateway|python.*hermes' | grep -v egrep
```

2. Check recent Feishu/proxy errors without exposing secrets:

```bash
grep -iE 'feishu|lark|proxyerror|connection refused|open.feishu.cn|tenant_access_token|receive message loop|send error|reaction' \
  ~/.hermes/logs/gateway.log ~/.hermes/logs/gateway.error.log 2>/dev/null | tail -n 160
```

3. Check the configured proxy endpoint:

```bash
lsof -nP -iTCP:6922 -sTCP:LISTEN 2>/dev/null || true
curl -I --proxy http://127.0.0.1:6922 --connect-timeout 5 https://open.feishu.cn 2>&1 | sed -n '1,40p'
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  curl -I --connect-timeout 8 https://open.feishu.cn 2>&1 | sed -n '1,40p'
```

4. Verify the launchd service inherited only intended proxy env vars:

```bash
ps eww -p <gateway_pid> | tr ' ' '\n' | egrep '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY)='
```

## Interpretation

- Gateway running + Feishu `ProxyError` + local proxy not listening: not a Hermes startup failure; restore the local proxy first.
- Proxy now listening + prior `receive message loop exit`: ask the user to send a fresh Feishu message. If it still does not respond, request permission to restart the gateway so the Feishu websocket reconnects cleanly.
- Direct Feishu curl works but proxied curl fails: proxy daemon/rules are the culprit.
- Proxied curl works now but logs show earlier refusal: explain it as a transient proxy outage and avoid changing credentials.

## Safety

Do not print Feishu app secrets, tokens, webhook URLs, cookies, or connection strings from config/logs. Replace with `[REDACTED]` if they appear.

Do not restart `hermes gateway` or reload launchd unless the user explicitly approves.
