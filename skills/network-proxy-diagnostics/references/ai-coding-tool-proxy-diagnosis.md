# AI Coding Tools: Proxy Misdirection to Chinese API Endpoints

## Symptom pattern

User reports a desktop AI coding agent (ZCode / Codex / Cursor, etc.) keeps throwing
"网络错误" (network error) intermittently, while plain web browsing and short curl
requests seem fine. The tool is usually a Chinese-product tool whose model API
endpoints live in mainland China.

## Root cause (the recurring trap)

The tool is configured to send ALL traffic through a foreign (US/etc.) proxy node,
but its API servers are domestic. Domestic traffic routed through a foreign exit =
extra hop + high latency. These tools use **Anthropic-protocol SSE streaming** for
code generation — long-lived connections that break easily under that latency, so
the symptom shows up as intermittent "network error" mid-stream, not a hard block.

Short GET probes (e.g. `curl` of the baseURL) return 200 through the proxy, which
makes it LOOK fine — but a 200 on a one-shot GET does not exercise the long stream.

## Diagnostic sequence

1. Find the tool's proxy config (don't assume it uses the system proxy):
   - ZCode: `~/.zcode/v2/setting.json` → `httpProxy` / `httpProxyNoProxy`.
     Providers live in `~/.zcode/v2/config.json` (`provider.<id>.options.baseURL`).
   - Confirm system proxy + env vars too: `scutil --proxy`, `env | grep -i proxy`.
2. List every provider baseURL from config.json, then compare reachability
   **direct vs through the proxy**:

   ```bash
   for u in "https://api.z.ai/api/anthropic" "https://open.bigmodel.cn/api/anthropic" \
            "https://zcode.z.ai/api/v1/zcode-plan/anthropic" "https://api.deepseek.com/anthropic"; do
     d=$(curl -sk --noproxy '*'  -o /dev/null -w "%{http_code}" --max-time 12 "$u")
     p=$(curl -sk -x http://127.0.0.1:6922 -o /dev/null -w "%{http_code}" --max-time 12 "$u")
     echo "direct=$d proxy=$p  $u"
   done
   ```

   A 200/401/404 (any non-000) means the endpoint is reachable on that path; a 000
   or long hang means it isn't. 401 on `/anthropic` is normal without a key.
3. Grep the tool's own logs for corroborating evidence:
   `~/.zcode/v2/logs/<date>.log` — look for update-download range retries,
   "读取远端强制升级配置失败", or `[desktop-network] renderer proxy mode=fixed_servers`.

## The fix

Two options, ordered by how much the tool depends on foreign services:

1. **Full direct (simplest when the tool is all-domestic):** set `httpProxy` to `""`.
   This is the right call for ZCode — every provider it uses is Chinese.
2. **Selective bypass (keep proxy for foreign extras):** add the domestic domains to
   `httpProxyNoProxy`, e.g.:
   `localhost,127.0.0.1,::1,*.z.ai,*.bigmodel.cn,*.deepseek.com`

   `*.z.ai` covers api.z.ai / zcode.z.ai / cdn-zcode.z.ai in one pattern.

## Critical gotcha: quit before editing

ZCode (and many Electron apps) **rewrite their setting.json on a timer / on every
settings change** — the logs show "writing settings to .../setting.json" every few
seconds. Editing the file while the app is running gets silently overwritten.
Sequence: `pgrep -fl ZCode` to confirm it's stopped → edit → reopen.

## Generalization

The same logic applies to any AI coding tool:
- Chinese endpoints to bypass: `*.z.ai`, `*.bigmodel.cn`, `*.deepseek.com`, `*.moonshot.cn`, `*.dashscope.aliyuncs.com`, etc.
- Foreign endpoints that DO want the proxy: `*.openai.com`, `*.anthropic.com`, `*.googleapis.com`, `*.opencode.ai`.
- Rule: route domestic model APIs direct, foreign ones through the proxy — never a
  blanket proxy for a tool whose providers are domestic.
