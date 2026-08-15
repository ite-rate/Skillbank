# Print Parameters Reference

Complete guide to print parameters supported by the print skill.

## Platform Support Matrix

| Parameter | macOS/Linux (CUPS) | Windows (lpr) | Windows (pdf-to-printer) |
|-----------|-------------------|---------------|--------------------------|
| Copies | ✓ | ✓ | ✓ |
| Printer Selection | ✓ | ✓ | ✓ |
| Duplex | ✓ | ✗ | ✓ |
| Paper Size | ✓ | ✗ | ✓ |
| Orientation | ✓ | ✗ | ✓ |
| Page Range | ✓ | ✗ | ✓ |
| Dry Run | ✓ | ✓ | ✓ |

## Parameter Details

### Copies (`--copies`, `-n`)

Number of copies to print. Default: 1.

```bash
python scripts/print_file.py document.pdf --copies 3
```

**Platform notes:**
- CUPS: Uses `-n` flag
- Windows lpr: Uses `-#` flag

### Printer Selection (`--printer`)

Specify which printer to use. Default: system default printer.

```bash
python scripts/print_file.py document.pdf --printer "HP LaserJet Pro"
```

**Finding printer names:**
```bash
python scripts/get_printers.py
```

### Duplex Mode (`--duplex`)

Two-sided printing options.

| Value | Description | CUPS Option |
|-------|-------------|-------------|
| `none` | Single-sided | `one-sided` |
| `long-edge` | Double-sided, flip on long edge | `two-sided-long-edge` |
| `short-edge` | Double-sided, flip on short edge | `two-sided-short-edge` |

```bash
python scripts/print_file.py document.pdf --duplex long-edge
```

**Platform notes:**
- CUPS: Full support via `-o sides=` option
- Windows lpr: Not supported (use printer defaults)
- pdf-to-printer: Supported via `--duplex` flag

### Paper Size (`--paper`, `-p`)

Paper size selection.

| Value | Dimensions |
|-------|------------|
| `Letter` | 8.5" x 11" (US Letter) |
| `A4` | 210mm x 297mm |
| `Legal` | 8.5" x 14" |

```bash
python scripts/print_file.py document.pdf --paper A4
```

**Platform notes:**
- CUPS: Uses `-o media=` option
- Windows: Depends on printer capabilities

### Orientation (`--orientation`, `-o`)

Page orientation.

| Value | Description |
|-------|-------------|
| `portrait` | Upright orientation |
| `landscape` | Sideways orientation |

```bash
python scripts/print_file.py spreadsheet.xlsx --orientation landscape
```

**Platform notes:**
- CUPS: `portrait` uses printer default; `landscape` maps to `orientation-requested=4`
- Windows lpr: Not supported
- Windows pdf-to-printer: Supported when backend is available

### Page Range (`--pages`, `-P`)

Print specific pages only.

```bash
python scripts/print_file.py document.pdf --pages 1-5,8,10-12
```

**Format:**
- Single page: `5`
- Range: `1-10`
- Multiple: `1-5,8,10-15`

**Platform notes:**
- CUPS: Uses `-o page-ranges=` option
- Windows: Limited support

## Silent Mode (`--silent`)

Suppress progress output. Useful for scripting.

```bash
python scripts/print_file.py document.pdf --silent
```

## Dry Run (`--dry-run`)

Build the exact backend command and metadata without sending a real print job.

```bash
python scripts/print_file.py document.pdf --printer "Office Printer" --dry-run --json
```

Use this mode for:
- Agent workflow verification
- Frontend integration
- Human confirmation before real printing

## JSON Output (`--json`)

Return results in JSON format for programmatic use.

```bash
python scripts/print_file.py document.pdf --json
```

**Response format:**
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "request id is printer-123 (1 file(s))",
  "file": "document.pdf",
  "resolved_printer": "HP_LaserJet",
  "copies": 1,
  "converted": false,
  "backend": "cups",
  "job_id": "printer-123"
}
```

## Common Workflows

### Print with custom parameters
```bash
python scripts/print_file.py report.docx \
  --printer "Office Printer" \
  --copies 2 \
  --duplex long-edge \
  --paper A4
```

### Print specific pages
```bash
python scripts/print_file.py document.pdf --pages 1-3,5
```

### Batch print multiple files
```bash
python scripts/print_file.py *.pdf --duplex long-edge
```

### Preview before printing
```bash
python scripts/print_preview.py document.pdf
```

## Error Codes

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | File not found |
| 2 | Conversion failed |
| 3 | Print command not available |
| 4 | Print execution failed |

## Troubleshooting

### "lp: command not found" (macOS/Linux)
CUPS is not installed or not in PATH. Install CUPS:
```bash
# macOS (usually pre-installed)
brew install cups

# Linux (Debian/Ubuntu)
sudo apt-get install cups

# Linux (RHEL/CentOS)
sudo yum install cups
```

### "lpr.exe not found" (Windows)
Install LPR Port Monitor:
1. Go to Settings → Apps → Optional Features
2. Add feature → "Print Management" → "LPR Port Monitor"

Or use pdf-to-printer as fallback:
```bash
npm install -g pdf-to-printer
```

### "LibreOffice not found"
Install LibreOffice for Office file conversion:
```bash
# macOS
brew install --cask libreoffice

# Linux (Debian/Ubuntu)
sudo apt-get install libreoffice

# Windows
# Download from https://www.libreoffice.org/download/
```

### Printer shows as "unknown" or "offline"
Check printer status:
```bash
python scripts/get_printers.py
```

Verify printer is:
- Powered on
- Connected to network
- Has paper and ink/toner
- Not in error state
