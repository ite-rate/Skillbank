# App IM / Feishu websocket setup notes (OpenClaw 2026.6.8)

Session pattern captured from a Tencent Cloud Ubuntu host running OpenClaw installed via npm global.

## Discovery facts

- SSH user may not be `root`; try likely users and verify with `whoami`, `hostname`, and `uname -a`.
- In this setup OpenClaw was installed globally as `openclaw@2026.6.8` under `~/.npm-global/bin/openclaw`.
- State/config lived under `~/.openclaw/`; the active config path was `~/.openclaw/openclaw.json`.
- `openclaw status` showed gateway service not installed and no channels configured before setup.

## Schema finding

`openclaw channels add --help` did not list an `app-im` channel name. Schema inspection showed:

- `channels.feishu` has `appId`, `appSecret`, and optional `encryptKey`.
- `channels.clickclack` uses `token`, not appId/appSecret.
- `channels.qqbot` uses `appId` and `clientSecret`, not appSecret.
- `channels.matrix` has `encryption` but this is Matrix E2EE, not Feishu App IM callback encryption.

Therefore, if the user says “App IM” and provides `appid` + `appsecret`, treat `channels.feishu` as the likely OpenClaw target unless the screenshot/docs prove a different channel.

## Non-encrypted Feishu/App IM websocket config

Use websocket mode and do not set `encryptKey`:

```bash
openclaw config set channels.feishu.enabled true --strict-json
openclaw config set channels.feishu.appId '"APP_ID"'
openclaw config set channels.feishu.appSecret '"APP_SECRET"'
openclaw config set channels.feishu.connectionMode '"websocket"'
openclaw config unset channels.feishu.encryptKey || true
openclaw config validate
```

Do not paste real secrets into logs, final replies, references, or memory.

## Gateway notes

A fresh OpenClaw install may have no gateway config. Minimal local gateway setup in this session used:

```bash
openclaw config set gateway.mode '"local"'
openclaw config set gateway.port 18789 --strict-json
openclaw config set gateway.bind '"loopback"'
openclaw gateway install --force --port 18789
openclaw gateway start
```

`openclaw gateway status` may show the process is running while websocket probes fail with a credentials/device identity error. Treat that as an authentication/pairing verification issue, not necessarily a failed service start.

## Verification checklist

- Redacted config shows `channels.feishu.enabled=true`, the intended `appId`, `connectionMode=websocket`, `appSecret` present, and no `encryptKey`.
- `openclaw config validate` succeeds.
- Gateway service is installed/running if live integration was requested.
- `openclaw channels status --probe` or gateway logs confirm the channel is recognized and connected.
