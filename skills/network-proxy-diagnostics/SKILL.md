---
name: network-proxy-diagnostics
description: Diagnose network paths, proxy configurations, and SSH jump connections on macOS. Covers system proxy settings, Clash/Mihomo configs, SSH routing, and traffic analysis.
level: manual
native_agent: Hermes
version: 1.0.0
license: MIT
---

# Network Proxy Diagnostics

## Overview

When a user asks about "jump settings", "network path", or "proxy configuration", they might mean ANY of these:
- SSH config (`~/.ssh/config`)
- System proxy settings (`scutil --proxy`)
- Application-level proxy (Clash Verge, Mihomo, Surge)
- Environment variables (`http_proxy`, `https_proxy`, `all_proxy`)
- Whether traffic actually goes through proxy (TUN mode, ProxyCommand)

**First step: ALWAYS confirm what the user actually wants.**

## The Clarification Rule

When user says something ambiguous like:
- "看下本地jump的设置" (Check local jump settings)
- "网络怎么走" (How does network route)
- "代理配置" (Proxy config)

**DO NOT** immediately dump `~/.ssh/config` or `scutil --proxy` output.

**CRITICAL: "jump" can mean MULTIPLE things:**
1. **SSH jump host** — Configured in `~/.ssh/config` (Host alias with HostName/Port)
2. **Jump Desktop** — Remote desktop app (`com.p5sys.jump.connect`) with its own network stack
3. **General "jump" concept** — Any intermediate network hop

**When user says "jump", ALWAYS disambiguate FIRST:**
- Check `~/.ssh/config` for Host entries matching "jump" or similar
- Check running processes: `ps aux | grep -i jump`
- Check installed apps: `ls /Applications/ | grep -i jump`
- Then proceed with the appropriate diagnostic path

**Instead, ask or quickly check multiple dimensions:**
1. SSH config? → `~/.ssh/config`
2. System proxy? → `scutil --proxy`
3. Shell env vars? → `echo $http_proxy $https_proxy $all_proxy`
4. Active proxy process? → `lsof -i :<proxy_port>`
5. TUN mode? → `ifconfig | grep -E "utun|tun"`
6. Running apps with "jump" in name? → `ps aux | grep -i jump`

If user corrects you ("不是我看一下jump的网络 走的什么代理"), **note the correction and update this skill**.

## Diagnostic Checklist

### Phase 1: Identify the Proxy Layer

```bash
# 1. System proxy settings (macOS)
scutil --proxy

# 2. Shell environment variables
echo "http_proxy=$http_proxy https_proxy=$https_proxy all_proxy=$all_proxy"

# 3. SSH config (for jump hosts)
cat ~/.ssh/config

# 4. What process is listening on the proxy port?
lsof -i :<port_from_scutil>  # e.g., lsof -i :6922

# 5. Is TUN mode active?
ifconfig | grep -E "utun|tun|mihomo"
```

### Phase 2: Determine Traffic Routing

**For SSH connections:**
```bash
# Trace the actual network path
traceroute -n -m 5 <hostname>

# Check if SSH uses ProxyCommand
grep -A 5 "Host <name>" ~/.ssh/config
```

**Key facts about SSH and proxies:**
- SSH does NOT read system HTTP proxy settings (`scutil --proxy`)
- SSH does NOT read shell environment variables (`http_proxy`)
- SSH ONLY uses proxy if `ProxyCommand` is configured in `~/.ssh/config`
- SSH traffic is TCP direct, not HTTP
- TUN mode (if active) can intercept ALL traffic including SSH

**For application-specific connections (e.g., Jump Desktop):**
```bash
# Check if the app is running
ps aux | grep -i <app_name>

# Check app's network connections
lsof -i -a -c "<app_name>"
netstat -anv | grep -i <app_name>

# Check app's process arguments (may reveal proxy modes)
ps aux | grep <app_pid>

# Check app's preference plist for proxy settings
plutil -p ~/Library/Preferences/<bundle_id>.plist | grep -i proxy
```

**Key facts about application proxies:**
- Applications may have their OWN proxy logic (not using system proxy)
- Some apps use WebRTC/UDP for P2P connections (not HTTP proxy)
- Apps may use cloud relay servers (e.g., AWS) for NAT traversal
- Process arguments like `--rtcproxy`, `--desktopproxy` indicate internal proxy mechanisms
- Unix socket connections between processes (e.g., `/var/run/*.sock`) are local IPC, not network proxy

**For HTTP/HTTPS traffic:**
```bash
# Check if curl respects proxy
curl -v http://example.com 2>&1 | head -20

# Check proxy bypass list
curl --proxy http://127.0.0.1:<port> http://<internal_ip>
```

### Phase 3: Read Application Proxy Config

**Clash Verge / Mihomo:**
```bash
# Find config file
ls ~/Library/Application\ Support/io.github.clash-verge-rev.clash-verge-rev/

# Read the active config (large file, use grep for key sections)
grep -n "mode:\|proxy-groups:\|rules:\|mixed-port:" clash-verge.yaml
```

**Key config sections to extract:**
- `mode: rule` or `mode: global` or `mode: direct`
- `mixed-port:` (HTTP/HTTPS/SOCKS unified port)
- `proxy-groups:` (strategy groups like 节点选择, 全球直连, 漏网之鱼)
- `rules:` (DOMAIN, IP-CIDR, GEOIP, MATCH)
- `tun:` (enable: true/false)

**Proxy group types:**
- `select` — Manual selection
- `url-test` — Auto-select based on latency
- `fallback` — Fallback on failure

**Common rule patterns:**
- `IP-CIDR,192.168.0.0/16,🎯 全球直连` — Direct for LAN
- `DOMAIN-SUFFIX,openai.com,🌍 国外媒体` — Proxy for specific domains
- `GEOIP,CN,🎯 全球直连` — Direct for China IPs
- `MATCH,🐟 漏网之鱼` — Catch-all (usually proxy)

## Common Pitfalls

### Pitfall 1: Assuming SSH uses system proxy
SSH is TCP-based and does not use HTTP proxies by default. Only `ProxyCommand` or TUN mode can redirect SSH traffic.

### Pitfall 2: Confusing "settings" with "routing"
User asks about "settings" → might mean config file contents.
User asks about "network" or "routing" → might mean actual traffic path.
Always clarify or check both.

### Pitfall 3: Missing TUN mode check
If TUN mode is enabled (`tun: enable: true`), ALL traffic including SSH may be intercepted. Check `ifconfig` for TUN interfaces.

### Pitfall 4: Environment variables vs system proxy
Shell env vars (`http_proxy`) and system proxy (`scutil --proxy`) are separate. Some tools read one, some read the other, some read both.

### Pitfall 5: Proxy works for neutral hosts but target domain TLS-resets → node-level blocking, not a proxy fault
Symptom: `curl -x socks5://127.0.0.1:6922 https://example.com` → HTTP 200, but Google domains (google.com, notebooklm.google.com, support.google.com) fail with `curl: (35) SSL_ERROR_SYSCALL` or browser `ERR_CONNECTION_CLOSED`, including via `socks5h` (remote DNS). The local proxy is healthy; the **exit node is flagged/reset for that domain** (Google aggressively blocks datacenter/proxy IPs). Do NOT keep retrying or blame the proxy — switch node, or pivot to reachable alternatives (cn.bing.com, Chinese tech blogs) to finish the research. Rule: **always validate a proxy with a neutral host (example.com / generate_204) BEFORE diagnosing the target domain**, and try `socks5h` to rule out local DNS poisoning. Date-stamp findings — nodes change.

### Pitfall 6: AI coding tool "网络错误" because domestic API routed through foreign proxy
Desktop AI coding tools (ZCode, Codex, Cursor) that use Chinese model endpoints
(api.z.ai, open.bigmodel.cn, api.deepseek.com, …) break with intermittent "network
error" when they send everything through a foreign proxy: the extra hop + latency
kills the long SSE streaming connections, even though a one-shot curl GET returns
200. Fix = make domestic domains go DIRECT (clear `httpProxy` or add them to
`httpProxyNoProxy`). Also: these apps rewrite their own setting.json on a timer, so
quit the app before editing. Full recipe + endpoint lists in
`references/ai-coding-tool-proxy-diagnosis.md`.

## Quick Reference

| Question | Command | What it tells you |
|----------|---------|-------------------|
| System proxy? | `scutil --proxy` | HTTP/HTTPS/SOCKS proxy settings |
| Shell env? | `echo $http_proxy` | Environment variable proxy |
| SSH config? | `cat ~/.ssh/config` | Jump host definitions |
| Proxy process? | `lsof -i :<port>` | What app runs the proxy |
| TUN mode? | `ifconfig \| grep tun` | Virtual interfaces for traffic interception |
| SSH path? | `traceroute <host>` | Actual network route |
| Clash config? | `grep "mode:" clash-verge.yaml` | Rule/Global/Direct mode |
| Running "jump" apps? | `ps aux \| grep -i jump` | Is Jump Desktop running? |
| Jump network? | `lsof -i -a -c "Jump"` | Jump Desktop network connections |
| Jump proxy args? | `ps aux \| grep JumpConnect` | Process flags like --rtcproxy |

## References

- `references/clash-verge-config-analysis.md` — Detailed Clash Verge config parsing patterns
- `references/jump-desktop-network-analysis.md` — Jump Desktop network architecture and proxy behavior
- `references/google-blocked-research-fallback.md` — Google domains TLS-reset through an otherwise-working proxy: diagnosis sequence + China-network research fallback (cn.bing.com recipe, Bing 国内版 trap, zhihu 403)
- `references/ai-coding-tool-proxy-diagnosis.md` — AI coding tools (ZCode/Codex/Cursor) "网络错误" from domestic Chinese API endpoints routed through a foreign proxy; SSE-streaming diagnosis + direct/bypass fix + quit-before-edit gotcha