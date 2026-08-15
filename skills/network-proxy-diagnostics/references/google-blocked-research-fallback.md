# Google blocked → research fallback (China network, verified 2026-08)

## Symptom transcript (user machine, macOS)
- Direct fetch: `curl https://support.google.com/...` → exit 35, HTTP:000 (gateway has no proxy env)
- Via local proxy `-x socks5://127.0.0.1:6922` AND `-x http://127.0.0.1:6922` → same, `LibreSSL SSL_connect: SSL_ERROR_SYSCALL` after ~4–5s
- Proxy itself is HEALTHY: `curl -x socks5://127.0.0.1:6922 https://example.com` → HTTP 200
- `-x socks5h://127.0.0.1:6922` (remote DNS resolution) → still HTTP:000 → rules out local DNS poisoning
- Browser: `net::ERR_CONNECTION_CLOSED` on notebooklm.google.com
- Conclusion: exit node IP is flagged/reset by Google (datacenter/proxy IP). NOT a local proxy fault.

## Diagnosis sequence (reuse verbatim)
```bash
# 1. Is the proxy alive at all? Neutral host FIRST.
curl -sL -x socks5://127.0.0.1:6922 --max-time 10 https://example.com -o /dev/null -w "HTTP:%{http_code}\n"
# 2. Target domain through proxy
curl -sL -x socks5://127.0.0.1:6922 --max-time 15 "https://<target>" -w "HTTP:%{http_code}\n"
# 3. Rule out local DNS poisoning → resolve DNS through proxy
curl -sL -x socks5h://127.0.0.1:6922 --max-time 15 "https://www.google.com/generate_204" -w "HTTP:%{http_code}\n"
# 4. Browser check (browser may carry its own proxy config) → ERR_CONNECTION_CLOSED = same reset
```
Interpretation: proxy OK + TLS reset only on Google domains (even socks5h) → exit node flagged → stop retrying; switch node or use fallback research below. Date-stamp findings; re-test when the user changes nodes.

## Fallback research sources (no Google needed)
- **cn.bing.com is the workhorse**: `curl -sL "https://cn.bing.com/search?q=<URL-encoded query>&mkt=zh-CN&setlang=zh-CN"` with a desktop UA. Parse `<li class="b_algo">` blocks (h2 > a href/title, `p` snippet).
- **TRAP: `www.bing.com` 国内版** serves google.com.hk redirect garbage when `setlang=en` — always use `cn.bing.com` + `mkt=zh-CN`.
- **DuckDuckGo html (html.duckduckgo.com)**: blocked both direct and via proxy on this network (2026-08).
- **Zhihu (zhuanlan.zhihu.com)**: 403 to bare curl; use browser or skip.
- Working Chinese sources: aifreeapi.com/zh/posts/*, blog.csdn.net, cn.bing snippets.
- For product-feature research, dated Chinese walkthrough posts usually beat stale English docs; quote the post date in the answer ("以 2026-01 实测为准").

## Worked example (2026-08)
NotebookLM feature question → Google unreachable → cn.bing.com `q=NotebookLM 功能 音频概述 思维导图&mkt=zh-CN` → aifreeapi.com/zh/posts/notebooklm-guide (2026-01) → 8 core features, free tier limits (100 notebooks / 50 sources / ~50 chats/day / 3 audio overviews/day), Plus $20/mo (in Google One AI Premium), Chinese Audio Overviews since 2025-04, Goals (targeted dialogue) 2025.
