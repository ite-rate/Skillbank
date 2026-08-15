---
name: paddleocr-doc-parsing
description: Fallback parsing for complex PDFs that the PDF skill cannot handle, using PaddleOCR to preserve tables, formulas, charts, multi-column layouts, and other document structure in Markdown and JSON. Never invoke this skill before first using the PDF skill and determining that it cannot handle the PDF adequately.
level: manual
native_agent: TeleAgent
description_zh: 面向复杂文档的结构化解析工具，精准识别表格、数学公式、图表、多栏内容和版面层级，输出结构清晰的 Markdown 与 JSON 文件，适用于报告解析、资料数字化、内容抽取与结构化归档。
name_zh: 复杂文档解析
---

# PaddleOCR Document Parsing Skill

## When to Use This Skill

This skill is a fallback for complex PDFs that the PDF skill has already attempted but cannot handle adequately. **Never invoke or use this skill before calling the PDF skill first.**

**Use Document Parsing for**:
- Documents with tables (invoices, financial reports, spreadsheets)
- Documents with mathematical formulas (academic papers, scientific documents)
- Documents with charts and diagrams
- Multi-column layouts (newspapers, magazines, brochures)
- Complex document structures requiring layout analysis
- Any document requiring structured understanding

**Use Text Recognition instead for**:
- Simple text-only extraction
- Quick OCR tasks where speed is critical
- Screenshots or simple images with clear text

## Installation

Install Python dependencies before using this skill. From the skill directory (`skills/paddleocr-doc-parsing`):

```bash
pip install -r scripts/requirements.txt
```

This installs:
- `httpx` for API requests
- `keyring` for secure token persistence

**Optional** — for document optimization and `split_pdf.py` (page extraction):

```bash
pip install -r scripts/requirements-optimize.txt
```

## How to Use This Skill

### Windows Compatibility Notes

This skill now supports a more practical Windows flow for office users:

- UTF-8 console output is enabled in `vl_caller.py` to reduce garbled Chinese text in `cmd` / PowerShell.
- Credentials can be persisted once and reused later.
- On Windows, the access token is stored through the OS credential store via `keyring` when available.
- The API URL is stored in the user's config directory so users do not need to re-enter it every time.

Recommended Windows review points for non-technical office users:
- Prefer PowerShell or the host app's built-in terminal instead of legacy `cmd` when possible.
- Avoid file paths on unstable network shares during first-time troubleshooting.
- Prefer local PDF/image paths without special permission restrictions.
- If antivirus or endpoint security blocks Python credential access, run `python scripts/smoke_test.py` to verify whether keyring storage is available.

**⛔ MANDATORY RESTRICTIONS - DO NOT VIOLATE ⛔**

1. **PDF SKILL MUST COME FIRST** - Call the PDF skill and attempt the task with it first. Use this skill only after the PDF skill cannot handle the complex PDF adequately. Never invoke this skill before the PDF skill.
2. **WARN THE USER BEFORE ANY USE** - Before installing dependencies, running preflight checks, configuring credentials, uploading a file, or calling the PaddleOCR service, tell the user exactly: `请注意：addle-ocr 属于是外部服务，**不建议用它处理敏感数据文件**`
3. **ONLY use PaddleOCR Document Parsing API** - Execute the script `python scripts/vl_caller.py`
4. **NEVER parse documents directly** - Do NOT parse documents yourself
5. **NEVER offer alternatives** - Do NOT suggest "I can try to analyze it" or similar
6. **IF API fails** - Display the error message and STOP immediately
7. **NO fallback methods** - Do NOT attempt document parsing any other way

If the script execution fails (API not configured, network error, etc.):
- Show the error message to the user
- Do NOT offer to help using your vision capabilities
- Do NOT ask "Would you like me to try parsing it?"
- Simply stop and wait for user to fix the configuration

### Credential Persistence for Small-White-Collar Users

This skill supports a one-time credential setup flow. **You only need an access token** — the API URL is built in.

Persist your access token securely:

```bash
python scripts/configure_credentials.py --access-token "your_token_here"
```

What gets persisted:
- Access token: saved in the OS secure credential store through `keyring`
- API URL: automatically set to the built-in default (can be overridden with `--api-url` for self-hosted deployments)
- Timeout: optional, can also be persisted with `--timeout`

Priority at runtime:
1. Environment variables (`PADDLEOCR_ACCESS_TOKEN`)
2. Persisted token in OS secure credential store

This means users can:
- Configure once with just a token
- Reuse the skill later without re-entering credentials

### Preflight Check Before Parsing

You must verify configuration before running the real parsing command when:
- The user is using this skill for the first time
- The current environment is unknown
- The user may have switched machines, terminals, or runtime environments

Run this preflight check first:

```bash
python scripts/smoke_test.py --skip-api-test
```

Decision rule:
- If the preflight check passes, continue to `python scripts/vl_caller.py ...`
- If the preflight check fails, do not execute `python scripts/vl_caller.py`
- If configuration is missing, immediately tell the user:
  - Option A: follow the skill's configuration steps to set `PADDLEOCR_ACCESS_TOKEN`
  - Option B: stop using this skill and switch to another method or skill for degraded execution
- When describing Option B, clearly say the degraded path is less reliable and may produce materially worse results than PaddleOCR document parsing
- Prefer guiding the user toward Option A whenever they actually need high-quality document parsing

### Basic Workflow

1. **Execute document parsing**:
   ```bash
   python scripts/vl_caller.py --file-url "URL provided by user" --pretty
   ```
   Or for local files:
   ```bash
   python scripts/vl_caller.py --file-path "file path" --pretty
   ```

   **Optional: explicitly set file type**:
   ```bash
   python scripts/vl_caller.py --file-url "URL provided by user" --file-type 0 --pretty
   ```
   - `--file-type 0`: PDF
   - `--file-type 1`: image
   - If omitted, the service can infer file type from input.

   **Default behavior: save raw JSON to a temp file**:
   - If `--output` is omitted, the script saves automatically under the system temp directory
   - Default path pattern: `<system-temp>/paddleocr/doc-parsing/results/result_<timestamp>_<id>.json`
   - If `--output` is provided, it overrides the default temp-file destination
   - If `--stdout` is provided, JSON is printed to stdout and no file is saved
   - In save mode, the script prints the absolute saved path on stderr: `Result saved to: /absolute/path/...`
   - In default/custom save mode, read and parse the saved JSON file before responding
   - In save mode, always tell the user the saved file path and that full raw JSON is available there
   - Use `--stdout` only when you explicitly want to skip file persistence

2. **The output JSON contains COMPLETE content** with all document data:
   - Headers, footers, page numbers
   - Main text content
   - Tables with structure
   - Formulas (with LaTeX)
   - Figures and charts
   - Footnotes and references
   - Seals and stamps
   - Layout and reading order

   **Input type note**:
   - Supported file types depend on the model and endpoint configuration.
   - Always follow the file type constraints documented by your endpoint API.

3. **Extract what the user needs** from the output JSON using these fields:
   - Top-level `text`
   - `result[n].markdown`
   - `result[n].prunedResult`

### IMPORTANT: Complete Content Display

**CRITICAL**: You must display the COMPLETE extracted content to the user based on their needs.

- The output JSON contains ALL document content in a structured format
- In save mode, the raw provider result can be inspected in the saved JSON file
- **Display the full content requested by the user**, do NOT truncate or summarize
- If user asks for "all text", show the entire `text` field
- If user asks for "tables", show ALL tables in the document
- If user asks for "main content", filter out headers/footers but show ALL body text

**What this means**:
- **DO**: Display complete text, all tables, all formulas as requested
- **DO**: Present content using these fields: top-level `text`, `result[n].markdown`, and `result[n].prunedResult`
- **DON'T**: Truncate with "..." unless content is excessively long (>10,000 chars)
- **DON'T**: Summarize or provide excerpts when user asks for full content
- **DON'T**: Say "Here's a preview" when user expects complete output

**Example - Correct**:
```
User: "Extract all the text from this document"
Agent: I've parsed the complete document. Here's all the extracted text:

[Display entire text field or concatenated regions in reading order]

Document Statistics:
- Total regions: 25
- Text blocks: 15
- Tables: 3
- Formulas: 2
Quality: Excellent (confidence: 0.92)
```

**Example - Incorrect**:
```
User: "Extract all the text"
Agent: "I found a document with multiple sections. Here's the beginning:
'Introduction...' (content truncated for brevity)"
```

### Understanding the JSON Response

The output JSON uses an envelope wrapping the raw API result:

```json
{
  "ok": true,
  "text": "Full markdown/HTML text extracted from all pages",
  "result": { ... },  // raw provider response
  "error": null
}
```

**Key fields**:
- `text` — extracted markdown text from all pages (use this for quick text display)
- `result` - raw provider response object
- `result[n].prunedResult` - structured parsing output for each page (layout/content/confidence and related metadata)
- `result[n].markdown` — full rendered page output in markdown/HTML

> Raw result location (default): the temp-file path printed by the script on stderr

### Usage Examples

**Example 1: Extract Full Document Text**
```bash
python scripts/vl_caller.py \
  --file-url "https://example.com/paper.pdf" \
  --pretty
```

Then use:
- Top-level `text` for quick full-text output
- `result[n].markdown` when page-level output is needed

**Example 2: Extract Structured Page Data**
```bash
python scripts/vl_caller.py \
  --file-path "./financial_report.pdf" \
  --pretty
```

Then use:
- `result[n].prunedResult` for structured parsing data (layout/content/confidence)
- `result[n].markdown` for rendered page content

**Example 3: Print JSON Without Saving**
```bash
python scripts/vl_caller.py \
  --file-url "URL" \
  --stdout \
  --pretty
```

Then return:
- Full `text` when user asks for full document content
- `result[n].prunedResult` and `result[n].markdown` when user needs complete structured page data

### First-Time Configuration

**When the preflight check shows configuration is missing**:

Treat this as a stop-and-guide branch before parsing. Do not continue into `vl_caller.py` until the user confirms configuration is ready.

The error may show:
```
CONFIG_ERROR: PADDLEOCR_ACCESS_TOKEN not configured. Get your API at: https://paddleocr.com
```

**Required response flow**:

1. **Explain the current state clearly**:
   - Say that PaddleOCR document parsing is not configured in the current environment
   - Say that this skill cannot continue until the access token is available

2. **Offer exactly two next-step paths**:
   - Option A: configure PaddleOCR and continue with this skill
   - When introducing Option A, explicitly emphasize that PaddleOCR usually provides a free quota for new accounts, which is often enough for light personal office use and first-time testing
   - Option B: stop using this skill and switch to another method or skill for degraded execution
   - When presenting Option B, explicitly warn that the degraded path is harder to guarantee and may have noticeably worse parsing quality
   - Prefer recommending Option A when the user needs reliable structured extraction

3. **If the user chooses Option A, guide the user to configure securely**:
   - Show the exact error message to the user
   - Recommend configuring through the host application's standard method, or use `python scripts/configure_credentials.py` for one-time local persistence.
   - List the supported configuration inputs:
     ```
     - PADDLEOCR_ACCESS_TOKEN (required)
     - Optional: PADDLEOCR_DOC_PARSING_TIMEOUT
     ```

4. **For domestic first-time users, explain registration plainly**:
   - Visit `https://www.paddleocr.com`
   - Register with a mobile phone number if they do not already have an account
   - Explicitly reassure the user that new accounts usually include a free quota, so they can often complete initial setup and light usage without paying first
   - After registration and sign-in, open the model API page
   - Copy the Access Token
   - No need to configure an API URL — the official endpoint is built in

5. **If the user provides credentials in chat anyway** (accept any reasonable format), for example:
   - `PADDLEOCR_ACCESS_TOKEN=abc123...`
   - `Here's my token: abc123`
   - Copy-pasted code format
   - Any other reasonable format
   - **Security note**: Warn the user that credentials shared in chat may be stored in conversation history. Recommend setting them through the host application's configuration instead when possible.

   Then parse, validate, and persist the values:
   - Extract `PADDLEOCR_ACCESS_TOKEN` (long alphanumeric string, usually 40+ chars)
   - Save with:
     ```bash
     python scripts/configure_credentials.py --access-token "abc123..."
     ```

6. **Ask the user to confirm the environment or persisted configuration is ready**.

7. **Re-run the preflight check after configuration changes**:
   ```bash
   python scripts/smoke_test.py --skip-api-test
   ```
   - Only continue after this check passes or the user explicitly confirms the configuration is ready

8. **Retry only after confirmation**:
   - Once the user confirms the environment variables or persisted credentials are available, retry the original parsing task

### Handling Large Files

There is no file size limit for the API. For PDFs, the maximum is 100 pages per request.

**Tips for large files**:

#### Use URL for Large Local Files (Recommended)
For very large local files, prefer `--file-url` over `--file-path` to avoid base64 encoding overhead:
```bash
python scripts/vl_caller.py --file-url "https://your-server.com/large_file.pdf"
```

#### Process Specific Pages (PDF Only)
If you only need certain pages from a large PDF, extract them first:
```bash
# Extract pages 1-5
python scripts/split_pdf.py large.pdf pages_1_5.pdf --pages "1-5"

# Mixed ranges are supported
python scripts/split_pdf.py large.pdf selected_pages.pdf --pages "1-5,8,10-12"

# Then process the smaller file
python scripts/vl_caller.py --file-path "pages_1_5.pdf"
```

### Error Handling

**Authentication failed (403)**:
```
error: Authentication failed
```
→ Token is invalid, reconfigure with correct credentials

**API quota exceeded (429)**:
```
error: API quota exceeded
```
→ Daily API quota exhausted, inform user to wait or upgrade

**Unsupported format**:
```
error: Unsupported file format
```
→ File format not supported, convert to PDF/PNG/JPG

## Important Notes

- **The script NEVER filters content** - It always returns complete data
- **The AI agent decides what to present** - Based on user's specific request
- **All data is always available** - Can be re-interpreted for different needs
- **No information is lost** - Complete document structure preserved
- **Credentials can be persisted** - Users do not need to re-enter API URL and token every time

## Reference Documentation

- `references/output_schema.md` - Output format specification

> **Note**: Model version and capabilities are determined by your API endpoint (`PADDLEOCR_DOC_PARSING_API_URL`).

Load these reference documents into context when:
- Debugging complex parsing issues
- Need to understand output format
- Working with provider API details

## Testing the Skill

To verify the skill is working properly:
```bash
python scripts/smoke_test.py
```

This tests configuration and optionally API connectivity.
