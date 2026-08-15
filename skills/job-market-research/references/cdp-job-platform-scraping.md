# CDP Job Platform Scraping — Implementation Details

## Critical: Chrome Launch Flags

Chrome must be started with `--remote-allow-origins=*` or WebSocket connections will get `403 Forbidden`:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="/tmp/chrome-debug-profile" \
  --no-first-run --no-default-browser-check "https://www.zhipin.com"
```

Without `--remote-allow-origins=*`, the error is:
```
Rejected an incoming WebSocket connection from the http://127.0.0.1:9222 origin.
Use the command line flag --remote-allow-origins=http://127.0.0.1:9222 to allow connections from this origin or --remote-allow-origins=* to allow all origins.
```

## Mature Tool: boss-zhipin-scraper

For full scraping (salary, skills, pagination, anti-font-scraping), use `eatmoreduck/boss-zhipin-scraper` (924 stars, GitHub):

```bash
git clone https://github.com/eatmoreduck/boss-zhipin-scraper.git
cd boss-zhipin-scraper
pip install -r requirements.txt
python3 scripts/boss_cdp_raw.py --keyword "Go后端" --city 杭州 --pages 3 --analysis
```

**Requirements**: Python 3.10+ (uses `int | None` type syntax that fails on 3.9). Use `/opt/homebrew/Caskroom/miniconda/base/bin/python3.12` if system Python is 3.9.

The scraper:
- Connects to Chrome CDP on port 9222 (reuses logged-in session)
- Bypasses font anti-scraping via API mode
- Outputs明文薪资 JSON/CSV
- Generates薪资分布, 技能词频, 求职材料优化提示词
- Doubles as a Hermes Skill (has SKILL.md)

## Raw WebSocket CDP Client (no websockets library needed)

Use this when the `websockets` Python package is unavailable. Implements WebSocket framing manually over a raw socket.

### Connection

```python
import json, socket, struct, os, base64, time
from urllib.parse import quote

def ws_connect(page_id):
    """Connect to Chrome CDP via raw WebSocket"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("127.0.0.1", 9222))
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET /devtools/page/{page_id} HTTP/1.1\r\n"
        f"Host: 127.0.0.1:9222\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    s.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += s.recv(4096)
    if b"101" not in resp.split(b"\r\n")[0]:
        s.close()
        return None
    return s
```

### Send / Receive

```python
def ws_send(sock, msg_id, method, params=None):
    payload = json.dumps({"id": msg_id, "method": method, "params": params or {}})
    data = payload.encode("utf-8")
    header = bytearray([0x81])  # FIN + text
    mask_key = b"\x00\x01\x02\x03"  # client must mask
    if len(data) < 126:
        header.append(0x80 | len(data))
    elif len(data) < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack(">H", len(data)))
    header.extend(mask_key)
    masked = bytearray(b ^ mask_key[i % 4] for i, b in enumerate(data))
    sock.sendall(bytes(header) + bytes(masked))

def ws_recv(sock, timeout=10):
    sock.settimeout(timeout)
    header = sock.recv(2)
    if len(header) < 2:
        return None
    length = header[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", sock.recv(8))[0]
    masked = header[1] & 0x80
    if masked:
        mask = sock.recv(4)
    data = b""
    while len(data) < length:
        chunk = sock.recv(min(length - len(data), 65536))
        if not chunk:
            break
        data += chunk
    if masked:
        data = bytearray(b ^ mask[i % 4] for i, b in enumerate(data))
    if (header[0] & 0x0F) == 1:
        return json.loads(data.decode("utf-8"))
    return None

def drain(sock, timeout=1):
    while True:
        try:
            ws_recv(sock, timeout)
        except:
            break
```

### Search and Extract Job Data

```python
def search_boss(keyword, city_code="101210100", page_id="F5DB37A27E97D27F03868F546E19B622"):
    s = ws_connect(page_id)
    if not s:
        return f"{keyword}: connection failed"

    # Navigate to search page
    url = f"https://www.zhipin.com/web/geek/job?query={quote(keyword)}&city={city_code}"
    ws_send(s, 1, "Page.navigate", {"url": url})
    time.sleep(8)  # wait for JS to render
    drain(s)

    # Extract unique job links via JS injection
    ws_send(s, 2, "Runtime.evaluate", {
        "expression": """
        (function() {
            var result = {};
            var jobLinks = document.querySelectorAll('a[href*="/job_detail/"]');
            var seen = new Set();
            var titles = [];
            jobLinks.forEach(function(a) {
                var href = a.getAttribute('href');
                if (!seen.has(href)) {
                    seen.add(href);
                    var name = a.textContent.trim().substring(0, 80);
                    if (name) titles.push(name);
                }
            });
            result.uniqueJobs = seen.size;
            result.first5Titles = titles.slice(0, 5);
            result.cookies = document.cookie.substring(0, 200);
            return JSON.stringify(result);
        })()
        """,
        "returnByValue": True
    })

    result = None
    for _ in range(10):
        try:
            data = ws_recv(s, timeout=5)
            if data and data.get("id") == 2:
                result = data.get("result", {}).get("result", {}).get("value", "")
                break
        except:
            break

    s.close()
    return f"{keyword}: {result}"
```

### Finding Chrome Tab IDs

```bash
curl -s http://127.0.0.1:9222/json/list -o /tmp/chrome_tabs.json
# Then read the file to find page IDs and URLs
```

### Verifying Login State

Check for user name element and login cookies:

```javascript
(function() {
    var userInfo = document.querySelector('.user-info, .nav-user, [class*="user-name"]');
    var cookies = document.cookie;
    return JSON.stringify({
        userInfo: userInfo ? userInfo.textContent.trim() : 'not found',
        hasLoginToken: cookies.indexOf('__zp_stoken') >= 0 || cookies.indexOf('wt') >= 0,
        cookies: cookies.substring(0, 500)
    });
})()
```

## Key Findings from Session

1. **`--remote-allow-origins=*` is mandatory** — without it, CDP WebSocket connections get 403 Forbidden. This is a Chrome 111+ security change.

2. **BOSS直聘 renders job lists as Canvas** — `document.body.innerText` and `outerHTML` contain mostly CSS, not job data. The only reliable way to extract job info is via `a[href*="/job_detail/"]` link elements.

3. **Unlogged state caps at ~17 jobs per page** — need login for full results. Check `document.cookie` for `__zp_stoken__` tokens to verify login state.

4. **Generic card selectors return duplicates** — `querySelectorAll('[class*="job-card"]')` returned 78 elements but only 17 were unique. Always deduplicate by `href`.

5. **`websockets` Python package may not be installed** — the raw socket implementation above works without any external packages.

6. **`pdftotext` is available on macOS via homebrew** at `/opt/homebrew/bin/pdftotext` — use it instead of `read_file` for PDF text extraction.

7. **Search engines fail for Chinese job queries** — Google returns CAPTCHA, Bing returns irrelevant dictionary results. Direct platform access is the only reliable approach.

8. **boss-zhipin-scraper requires Python 3.10+** — system Python on macOS may be 3.9 which fails on `int | None` syntax. Use conda's Python 3.12: `/opt/homebrew/Caskroom/miniconda/base/bin/python3.12`.

9. **Multiple Chrome profiles don't share login** — if user logs in via their own Chrome (not the CDP-launched one), the CDP session won't have login cookies. User must log in within the CDP Chrome window specifically.