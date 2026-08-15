# BOSS直聘 CDP Cookie Extraction Technique

## Problem
BOSS直聘 (zhipin.com) blocks automated access with captcha/login walls. DOM scraping fails because job lists are Canvas-rendered. Search engines return irrelevant results for Chinese job queries.

## Solution: Extract cookies from logged-in Chrome via CDP, then call API directly

### Prerequisites
- Chrome running with `--remote-debugging-port=9222 --remote-allow-origins=http://127.0.0.1:9222`
- User has manually logged into BOSS直聘 in that Chrome instance
- Python: `websocket-client` and `requests` packages

### Step 1: Start Chrome with remote debugging
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=http://127.0.0.1:9222 \
  --user-data-dir="/tmp/chrome-debug-profile" \
  --no-first-run --no-default-browser-check \
  "https://www.zhipin.com"
```
User logs in manually in the opened Chrome window.

### Step 2: Extract cookies via CDP
```python
import json, requests
from websocket import create_connection

# List tabs
resp = requests.get('http://127.0.0.1:9222/json/list', timeout=10)
tabs = resp.json()
zhipin_tabs = [t for t in tabs if t['type'] == 'page' and 'zhipin.com' in t.get('url', '')]

# Connect to a logged-in tab
ws = create_connection(zhipin_tabs[0]['webSocketDebuggerUrl'], 
                       timeout=10, 
                       origin='http://127.0.0.1:9222')

# Get cookies for zhipin.com
ws.send(json.dumps({
    "id": 1, 
    "method": "Network.getCookies", 
    "params": {"urls": ["https://www.zhipin.com"]}
}))

# Parse response
for _ in range(20):
    raw = ws.recv()
    data = json.loads(raw)
    if data.get("id") == 1:
        cookies = data.get("result", {}).get("cookies", [])
        break
ws.close()

# Build cookie dict for requests
cookie_dict = {c['name']: c['value'] for c in cookies}
```

### Step 3: Call BOSS直聘 search API
```python
from urllib.parse import quote

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.zhipin.com/web/geek/job?query=Go&city=101210100",
    "Accept": "application/json, text/plain, */*",
}

api_url = f"https://www.zhipin.com/wapi/zpgeek/search/joblist.json?scene=1&query={quote(keyword)}&city={city_code}&page=1&pageSize=30"
r = requests.get(api_url, headers=headers, cookies=cookie_dict, timeout=10)
body = r.json()
zp = body.get('zpData', {})
count = zp.get('resCount', 0)  # Total job count
has_more = zp.get('hasMore', False)
jobs = zp.get('jobList', [])  # Array of job objects
```

### Job object fields
- `jobName`: job title
- `salaryDesc`: salary range (e.g., "15-25K·14薪")
- `brandName`: company name
- `securityId`: unique job ID (for detail page)

### Rate limiting
BOSS直聘 API has aggressive rate limiting. After 2-3 consecutive calls with the same cookie set, subsequent calls return `resCount=0` with empty `jobList`. 

Mitigation:
- Space requests 3+ seconds apart
- Cache results immediately
- Batch all keywords in a single session, then stop
- Do NOT retry with the same cookies after getting empty results — wait or re-extract cookies

### Known issues
- `--remote-allow-origins=*` may not work; use `--remote-allow-origins=http://127.0.0.1:9222` instead
- Chrome started with `open -a "Google Chrome"` does NOT inherit the `--remote-debugging-port` flag — must launch the binary directly
- `read_file` cannot parse PDFs on macOS — use `pdftotext` (Homebrew poppler) instead
- The `boss-zhipin-scraper` GitHub tool (924 stars) implements this same approach but requires Python 3.10+ for `int | None` type syntax

### Alternative: boss-zhipin-scraper
GitHub: https://github.com/eatmoreduck/boss-zhipin-scraper
```bash
git clone https://github.com/eatmoreduck/boss-zhipin-scraper.git
cd boss-zhipin-scraper
pip install -r requirements.txt
python3.12 scripts/boss_cdp_raw.py --keyword "Go后端" --city 杭州 --pages 3
```
Note: Requires Python 3.10+ (uses `X | None` type syntax). Use conda's python3.12 if system python is 3.9.