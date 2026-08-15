---
name: feishu-sheets-api
description: Create and populate Feishu Sheets directly via Open Feishu APIs using FEISHU_APP_ID and FEISHU_APP_SECRET from the environment.
level: manual
native_agent: Hermes
---

# Feishu Sheets API

Use this skill when the user wants data exported to a Feishu/Lark spreadsheet and the environment already has Feishu app credentials.

## When to use

- User asks to output results to a 飞书表格 / Feishu sheet
- You have `FEISHU_APP_ID` and `FEISHU_APP_SECRET` in environment variables
- There is no higher-level Feishu tool available

## Preconditions

1. Verify credentials exist:

```bash
env | grep -E 'FEISHU_APP_ID|FEISHU_APP_SECRET|FEISHU_DOMAIN'
```

2. If missing, stop and ask the user for a sheet link or a different export target.

## Authentication

Request a tenant access token:

```bash
python - <<'PY'
import os, json, urllib.request
app_id=os.environ['FEISHU_APP_ID']
app_secret=os.environ['FEISHU_APP_SECRET']
req=urllib.request.Request(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    data=json.dumps({'app_id': app_id, 'app_secret': app_secret}).encode(),
    headers={'Content-Type': 'application/json'},
)
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

Extract `tenant_access_token` from the JSON response.

## Create a spreadsheet

```bash
python - <<'PY'
import json, urllib.request
TOKEN='...'
url='https://open.feishu.cn/open-apis/sheets/v3/spreadsheets'
data=json.dumps({'title':'Your Sheet Title'}).encode()
req=urllib.request.Request(
    url,
    data=data,
    headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

Save:
- `spreadsheet_token`
- sheet URL

## Find the default sheet ID

After creation, query the workbook metadata to get the first `sheet_id`:

```bash
python - <<'PY'
import json, urllib.request
TOKEN='...'
spreadsheet='...'
url=f'https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet}/sheets/query'
req=urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}'})
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

Read `data.sheets[0].sheet_id`.

## Write values

Use the v2 values endpoint with a PUT request. The range also needs to be present in the query string.

```bash
python - <<'PY'
import json, urllib.request, urllib.parse
TOKEN='...'
spreadsheet='...'
sheet='...'
values=[
  ['列1','列2'],
  ['a','b'],
]
body=json.dumps({'valueRange': {'range': f'{sheet}!A1:B2', 'values': values}}).encode()
base=f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet}/values'
query='?range=' + urllib.parse.quote(f'{sheet}!A1:B2')
req=urllib.request.Request(
    base + query,
    data=body,
    headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'},
    method='PUT'
)
with urllib.request.urlopen(req, timeout=30) as r:
    print(r.read().decode())
PY
```

## Practical workflow

1. Locate and verify source data first.
2. Summarize into compact rows before exporting.
3. Create the spreadsheet.
4. Query `sheet_id`.
5. Write headers + rows in one batch.
6. Return the Feishu sheet URL to the user.

## Good sheet structure for review tasks

Recommended columns:

- 阶段 / Stage
- 阶段名
- 状态
- 用时
- 核心产物
- 质量评分
- 质量判断
- 风险/备注
- 目录

Add a short run summary in the top rows before the table if useful.

## Pitfalls

- Feishu has both v3 spreadsheet creation/query endpoints and a v2 values write endpoint; mixing versions is normal here.
- After spreadsheet creation, you still need to query the sheet list to get the actual `sheet_id` (for example `bb4541`), not just the spreadsheet token.
- The values PUT request should include the range in both the JSON body and URL query string.
- A successful deliverables manifest may still be incomplete; verify actual source data before exporting.
- Keep secrets out of the final user response; only return the sheet URL.
- In Hermes, environment-variable visibility can differ by tool context. If `terminal` can see `FEISHU_APP_ID` / `FEISHU_APP_SECRET` but `execute_code` cannot, prefer a `terminal` call running `python3 - <<'PY'` rather than assuming the Python sandbox inherits the same env.

## Verification

- Confirm spreadsheet creation returned `code: 0`
- Confirm values write returned `updatedRows` / `updatedCells`
- Open the URL only if necessary; usually API success is sufficient
