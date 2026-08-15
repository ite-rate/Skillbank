# Liangzimixin / QuantumIM OpenClaw Setup Notes

Session-derived reference for configuring the external `liangzimixin` plugin on OpenClaw 2026.6.x.

## When this applies

Use this when a user says the IM is not a built-in OpenClaw channel and gives instructions like:

```bash
openclaw plugins install liangzimixin@latest
openclaw configure
# choose Local
```

This is distinct from built-in Feishu/Lark, even though both use field names like `appId` and `appSecret`.

## Install and identify

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
openclaw plugins install liangzimixin@latest
openclaw plugins list
```

Expected plugin list evidence in 2026.6.8-era installs:

- name: `liangzimixin`
- format: `openclaw`
- status: `enabled`
- version observed: `0.3.105`
- source path: `~/.openclaw/npm/projects/liangzimixin/node_modules/liangzimixin/dist/index.cjs`

Inspect manifest before writing config:

```bash
PLUG="$HOME/.openclaw/npm/projects/liangzimixin/node_modules/liangzimixin"
node -e "const fs=require('fs'); const j=JSON.parse(fs.readFileSync('$PLUG/openclaw.plugin.json','utf8')); console.log(JSON.stringify(j,null,2))"
```

## Manifest facts observed

The channel id is:

```text
liangzimixin
```

Typical channel config fields:

- `appId` — required application ID.
- `appSecret` — required paired secret; treat as write-only.
- `quantumAccount` — optional; manifest says filling it enables the quantum encryption module.
- `botUserId` — optional anti-loop ID.
- `env` — one of `staging`, `test`, `production`; default `production`.
- `encryptionMode` — one of `quantum_only`, `quantum_and_plain`; default `quantum_and_plain`.

## No-quantum-encryption interpretation

If the user says not to enable quantum encryption:

- Do not set `quantumAccount`.
- Prefer `encryptionMode: "quantum_and_plain"` rather than `quantum_only`.
- Do not invent or populate any quantum account/tenant value.

## Config write pattern

Back up config first:

```bash
CFG="$HOME/.openclaw/openclaw.json"
cp "$CFG" "$CFG.bak.liangzimixin.$(date +%Y%m%d%H%M%S)"
```

Then write `channels.liangzimixin` with the provided credentials. Avoid printing secrets. If credentials were mistakenly written to `channels.feishu` in a prior attempt, migrate them without echoing the secret and disable Feishu.

Resulting redacted shape:

```json
{
  "channels": {
    "liangzimixin": {
      "enabled": true,
      "appId": "APP_ID",
      "appSecret": "***",
      "env": "production",
      "encryptionMode": "quantum_and_plain"
    },
    "feishu": {
      "enabled": false
    }
  }
}
```

Validate:

```bash
openclaw config validate
```

## Configure UI pitfall

`openclaw configure --section plugins` may not show `liangzimixin` even after install, because it is a channel plugin rather than a generic plugin setup entry.

`openclaw configure --section channels` can show only stock channels in some builds and may not expose external channel entries cleanly. If the manifest and schema are present, direct JSON/config writes to `channels.liangzimixin` are acceptable; verify with logs after restart.

## Restart and verification

```bash
openclaw gateway restart
journalctl --user -u openclaw-gateway --no-pager -n 240 | grep -iE 'liangzimixin|quantum|密信|channel|error|warn|failed|websocket|gateway'
```

Good evidence:

```text
[liangzimixin:runtime] plugin runtime initialized
[liangzimixin:plugin] plugin registered (v2 path) ✓
http server listening (... liangzimixin ...)
gateway ready
```

A gateway status/probe error like `device identity required` or `requires credentials before opening a websocket` can mean the local CLI lacks gateway credentials or pairing while the gateway itself is running. Do not conflate that with a plugin load failure; check systemd process and plugin log lines separately.

## Secret handling

- Never print `appSecret`, gateway tokens, or credential files in summaries.
- Redact log filters aggressively: `appSecret`, `secret`, `token`, and `password`.
- It is OK to report `appSecret_set=true` as a boolean.
