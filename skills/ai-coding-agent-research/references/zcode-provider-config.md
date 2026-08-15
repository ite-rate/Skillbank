# ZCode Provider Config Extraction

## When to use
User asks about ZCode provider/model configuration, or wants to reuse a ZCode provider endpoint in another tool (Cursor, Windsurf, etc.).

## Config file locations (macOS)

| File | Purpose |
|------|---------|
| `~/.zcode/v2/config.json` | All provider definitions (baseURL, apiKey, models, enabled, kind) |
| `~/.zcode/v2/setting.json` | App settings (proxy, locale, provider family selection, enabled CLI providers) |
| `~/.zcode/v2/credentials.json` | Encrypted OAuth tokens (oauth:zai:access_token, zcodejwttoken, etc.) |
| `~/.zcode/v2/bot-config.json` | Bot integration config (Feishu, Telegram) |
| `~/.zcode/skills/` | ZCode skills directory (similar to Hermes skills) |

ZCode is an Electron app (`dev.zcode.app`). Session/browser data at `~/Library/Application Support/ZCode/session/`.

## config.json structure

Top-level key `provider` maps provider IDs to objects:
```json
{
  "provider": {
    "<uuid-or-builtin-id>": {
      "name": "display name",
      "kind": "anthropic" | "openai",
      "options": {
        "apiKey": "<plain-text-key>",
        "baseURL": "<endpoint-url>"
      },
      "enabled": true | false,
      "source": "custom",
      "models": {
        "<model-name>": {
          "limit": { "context": N, "output": N },
          "modalities": { "input": [...], "output": [...] },
          "reasoning": { "enabled": bool, "variants": [...], "defaultVariant": "..." }
        }
      },
      "systemDisabledReason": "<reason-if-disabled>"
    }
  }
}
```

## Extracting provider info for reuse

```python
import json
with open('~/.zcode/v2/config.json') as f:
    cfg = json.load(f)
for pid, p in cfg['provider'].items():
    print(f"Name: {p['name']}")
    print(f"Base URL: {p['options']['baseURL']}")
    print(f"API Key: {p['options']['apiKey']}")
    print(f"Protocol: {p['kind']}")
    print(f"Models: {list(p['models'].keys())}")
    print(f"Enabled: {p.get('enabled', 'not set')}")
```

## Reusing ZCode provider in Cursor

1. Cursor → Settings → Models → OpenAI API Key → Override
2. Fill Base URL + API Key from ZCode config
3. Add custom model name (must match ZCode model key exactly)
4. Verify

If the ZCode provider `kind` is `openai`, it's directly compatible with Cursor's custom OpenAI endpoint. If `kind` is `anthropic`, it needs an Anthropic-compatible client instead.

## Common provider IDs on this user's system

| Provider | Kind | Base URL | Models |
|----------|------|----------|--------|
| Z.ai - API Key | anthropic | https://api.z.ai/api/anthropic | GLM-5.2, GLM-5-Turbo |
| Bigmodel - API Key | anthropic | https://open.bigmodel.cn/api/anthropic | GLM-5.2, GLM-5-Turbo |
| ollama的智谱 (custom) | openai | https://ollama.com/v1 | glm-5.2:cloud |

Disabled reasons seen: `oauth_provider_inactive`, `coding_plan_not_entitled`.

## Setting.json key fields

- `httpProxy`: proxy used by ZCode (e.g. `http://127.0.0.1:6922`)
- `modelProviderFamilyModes`: e.g. `{"zai": "oauth"}` — auth mode per family
- `modelProviderFamilySelectedKeys`: selected provider per family
- `providerFamilyDomain`: active domain (e.g. `zai`)
- `enabledBuiltinAgentCliProviders`: e.g. `["glm"]`