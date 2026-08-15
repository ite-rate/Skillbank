# Clash Verge Config Analysis Patterns

## File Location

```
~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
```

## Key Sections to Extract

### 1. Mode and Port
```bash
grep -n "mode:\|mixed-port:" clash-verge.yaml
```

- `mode: rule` — Routes based on rules (most common)
- `mode: global` — All traffic through proxy
- `mode: direct` — No proxy
- `mixed-port:` — Unified HTTP/HTTPS/SOCKS port (e.g., 6922)

### 2. Proxy Groups (Strategy Groups)
```bash
grep -n "proxy-groups:" clash-verge.yaml
```

Common groups:
- `🔰 节点选择` (select) — Manual node selection
- `♻️ 自动选择` (url-test) — Auto-select by latency
- `🌍 国外媒体` (select) — Foreign media routing
- `Ⓜ️ 微软服务` (select) — Microsoft services routing
- `🎯 全球直连` (select) — Direct connection
- `🐟 漏网之鱼` (select) — Catch-all (usually proxy)

### 3. Rules
```bash
grep -n "rules:" clash-verge.yaml
tail -20 clash-verge.yaml  # Last rule is usually MATCH
```

Rule priority (top to bottom):
1. `DOMAIN-SUFFIX,local,🎯 全球直连` — Local domains direct
2. `IP-CIDR,192.168.0.0/16,🎯 全球直连` — LAN direct
3. `DOMAIN-SUFFIX,openai.com,🌍 国外媒体` — Specific domains proxy
4. `GEOIP,CN,🎯 全球直连` — China IPs direct
5. `MATCH,🐟 漏网之鱼` — Everything else (usually proxy)

### 4. TUN Mode
```bash
grep -A 10 "^tun:" clash-verge.yaml
```

- `enable: true` — All traffic intercepted (including SSH)
- `enable: false` — Only HTTP/HTTPS/SOCKS traffic proxied

### 5. DNS Settings
```bash
grep -A 5 "^dns:" clash-verge.yaml
```

- `enhanced-mode: fake-ip` — Returns fake IPs for domains
- `fake-ip-range: 198.18.0.1/16` — Fake IP range

## Analysis Pattern

When analyzing a user's proxy setup:

1. **Check mode** — `rule` means selective routing, `global` means everything through proxy
2. **Check mixed-port** — This is the port HTTP/HTTPS/SOCKS clients should use
3. **Check TUN** — If enabled, ALL traffic (including SSH) goes through proxy
4. **Check rules** — Look for specific domain/IP rules that affect the user's target
5. **Check proxy groups** — See what strategy is used for catch-all (漏网之鱼)

## Common Configurations

### Standard Rule Mode (most common)
- HTTP/HTTPS/SOCKS → mixed-port → selective routing based on rules
- SSH → direct (unless TUN enabled or ProxyCommand configured)
- LAN IPs → direct
- Foreign domains → proxy
- China IPs → direct
- Unknown → proxy (漏网之鱼)

### TUN Mode (full traffic interception)
- ALL traffic → TUN interface → Clash routing
- SSH → may be intercepted
- Need to check if SSH host is in bypass list

## Session Examples

### Example 1: SSH Jump Host Not Using Proxy
```
User: "看下本地jump的设置"
Agent: Shows ~/.ssh/config (SSH config)
User: "不是我看一下jump的网络 走的什么代理"
Agent: Checks scutil --proxy, lsof, traceroute
Result: SSH is direct, HTTP goes through Clash Verge 6922
```

Lesson: User said "jump settings" but meant "network routing". Always check multiple dimensions.
