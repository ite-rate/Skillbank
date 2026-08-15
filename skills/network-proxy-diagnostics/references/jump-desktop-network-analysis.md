# Jump Desktop Network Architecture Analysis

## Overview

Jump Desktop (`com.p5sys.jump.connect`) has its own network stack that is INDEPENDENT of system HTTP/SOCKS proxies. It uses WebRTC + cloud relay for NAT traversal, not local proxy settings.

## Key Processes

When Jump Desktop is running, you'll see multiple processes:

```
/Applications/Jump Desktop Connect.app/Contents/MacOS/JumpConnect --service          (PID ~500, root)
/Applications/Jump Desktop Connect.app/Contents/MacOS/JumpConnect --rtcproxy <sock>      (PID ~28000, user)
/Applications/Jump Desktop Connect.app/Contents/MacOS/JumpConnect --desktopproxy <sock>  (PID ~28000, user)
/Applications/Jump Desktop Connect.app/Contents/MacOS/JumpConnect --minimized           (PID ~800, user)
```

## Architecture

```
[Remote Desktop Server] ←──WebRTC/UDP──→ [rtcproxy process] ←──unix socket──→ [desktopproxy process] ←──桌面协议──→ [Local Desktop]
                              ↑
                              └── 通过 service 进程连接 AWS 中继服务器 (e.g., 3.219.24.233:443)
```

1. **--service** (root): Maintains persistent connection to Jump cloud servers (AWS) for signaling and relay
2. **--rtcproxy**: Handles WebRTC peer connections, listens on local TCP/UDP ports for WebRTC traffic
3. **--desktopproxy**: Bridges between rtcproxy and local desktop capture/display
4. **--minimized**: UI process

## Network Connections

### Service Process (--service)
- **TCP connection to AWS**: `192.168.1.5:xxxxx → 3.219.24.233:443` (ESTABLISHED)
- IP `3.219.24.233` is AWS US East (Virginia)
- This is a **DIRECT** connection, not through local Clash/Surge proxy
- Uses port 443 (HTTPS) for signaling

### RTCProxy Process (--rtcproxy)
- **Listens on multiple interfaces**: `0.0.0.0:35385` (TCP + UDP)
- Binds to: `192.168.139.3`, `fd07:b51a:cc66:0` (IPv6), `2408:8220:2f15:b` (IPv6)
- Heavy UDP traffic for WebRTC media
- Communicates with --service via unix socket: `/var/folders/zz/.../jdtemp.*.sock`

### DesktopProxy Process (--desktopproxy)
- Connects to rtcproxy via unix socket: `/var/run/com.p5sys.jump.connect.desktop-server.*.sock`
- No direct network connections

## Proxy Behavior

| Question | Answer |
|----------|--------|
| Does Jump use system HTTP proxy? | **NO** — It uses its own network stack |
| Does Jump use macOS proxy settings (scutil)? | **NO** — Ignores system proxy config |
| Does Jump use shell env vars (http_proxy)? | **NO** — Does not read them |
| Does Jump use local Clash/Surge proxy? | **NO** — Direct connections to AWS |
| Does Jump use cloud relay? | **YES** — Built-in relay through AWS servers |
| Can you force Jump through local proxy? | **Difficult** — Would need network-level interception (TUN) |

## How to Check if Jump is Using Proxy

```bash
# 1. Check if Jump processes have network connections
lsof -i -a -c "Jump" 2>/dev/null

# 2. Check netstat for Jump connections
netstat -anv | grep -i "Jump\|jump" | head -20

# 3. Check if connections go to 127.0.0.1:proxy_port
# If YES: Jump is using local proxy
# If NO (goes to external IPs like 3.219.24.233): Jump is direct

# 4. Check process arguments for proxy-related flags
ps aux | grep JumpConnect | grep -E "proxy|relay|tunnel"
```

## Key Finding

Jump Desktop's `--rtcproxy` and `--desktopproxy` flags indicate it has its own **internal proxy/relay mechanism**. This is NOT a user-configurable proxy — it's Jump's cloud infrastructure for NAT traversal and P2P connectivity.

**Implication**: When user asks "jump 走不走代理", the answer is:
- It does NOT use your local Clash/Surge proxy
- It DOES use Jump's own cloud relay (through AWS)
- This is by design and cannot be easily disabled without breaking remote connectivity

## Related Files

- App: `/Applications/Jump Desktop Connect.app/`
- Config: `~/Library/Preferences/com.p5sys.jump.connect.plist`
- Cache: `~/Library/Caches/com.p5sys.jump.connect/`
- Support: `~/Library/Application Support/com.p5sys.jump.connect/`
