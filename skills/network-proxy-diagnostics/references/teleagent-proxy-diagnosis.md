# TeleAgent Proxy Diagnosis

## Symptom

TeleAgent (TeleAI 桌面端) 报错：

```text
proxyconnect tcp: dial tcp 127.0.0.1:6922: connect: connection refused
```

通常出现在调用国内模型接口时：

```text
Post "https://agent.teleai.com.cn/superCowork/sapi/api/v1/chat/completions": proxyconnect tcp: dial tcp 127.0.0.1:6922: connect: connection refused
```

## Root cause

1. TeleAgent 的**沙箱网络策略**强制所有出网流量走一个本地代理端口（常见为 `127.0.0.1:6922`）。
2. `127.0.0.1:6922` 通常是一云梯_Lite (`OneLiteCore`) 的本地 HTTP/SOCKS 代理端口。
3. 当一云梯 Lite 未启动、崩溃、或对 TeleAgent 做了应用级隔离时，连接会被拒绝。
4. 即使代理能连上，`agent.teleai.com.cn` 这类**国内 API 走海外代理节点**也容易导致 SSE 流式断连 / 网络错误。

## Diagnosis commands

```bash
# 1. 查看 6922 端口是否有进程在监听
lsof -i :6922

# 典型输出：OneLiteCore 监听 6922
# OneLiteCo 51309 ss ... TCP localhost:6922 (LISTEN)

# 2. 查看 TeleAgent 的 sandbox 策略中 hardcode 的代理端口
grep -R '"proxyPorts"\|"allowedLoopbackPorts"\|"hasProxyConfiguration"' \
  ~/.local/share/TeleAgent/sandbox-helper/platform-audit/ | head -20

# 3. 查看当前系统代理和 shell 环境变量（通常为空）
scutil --proxy
echo "http_proxy=$http_proxy https_proxy=$https_proxy all_proxy=$all_proxy"

# 4. 查看 TeleAgent 相关进程
ps aux | grep -iE 'teleagent|super-agent|oneLite'
```

## Sandbox audit log excerpt

```json
{
  "envKeys": [
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "http_proxy",
    "https_proxy"
  ],
  "networkPolicy": {
    "enabled": true,
    "restrictedToExceptions": true,
    "allowedLoopbackPorts": [6922],
    "proxyPorts": [6922],
    "hasProxyConfiguration": true
  }
}
```

This confirms TeleAgent enforces `127.0.0.1:6922` at the sandbox level, regardless of `scutil` or shell env.

## Fixes

### Option A: Restart the local proxy

退出并重新打开 `一云梯_Lite.app`，确认状态栏图标稳定后，再试 TeleAgent。

### Option B: Change TeleAgent's proxy setting

TeleAgent → 设置 → 网络代理 (Proxy)

- 选择「不使用代理 / Direct」如果你当前网络可以直连。
- 或改成当前实际在用的代理端口。

### Option C: Bypass domestic domains (recommended for `*.teleai.com.cn`)

在代理工具或 TeleAgent 的 bypass list 中把国内 API 域名设为直连：

```text
agent.teleai.com.cn
api.z.ai
open.bigmodel.cn
api.deepseek.com
```

这样可以避免国内 SSE 流因绕海外代理而断连。

## See also

- `references/ai-coding-tool-proxy-diagnosis.md` — 同类问题在 ZCode/Codex/Cursor 中的表现和修复