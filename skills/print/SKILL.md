---
name: print
description: 'Universal document printing for PDF, Word, Excel, PowerPoint, and image files. Use this skill when the user clearly wants to send a file to a real printer, asks for hard copies, print settings, printer selection, print preview, or batch printing. Trigger when the user explicitly says ''print'', ''send to printer'', ''print out'', ''hard copy'', or asks to adjust copies, duplex, paper size, orientation, or page range for a print job. For real printing, default to a safe workflow: verify the target file and printer, preview or dry-run first when details are missing, and require explicit user intent before sending the final print job.'
level: manual
native_agent: TeleAgent
description_zh: 面向日常办公打印场景，支持常见文档一键打印，并智能推荐打印机、份数、单双面打印及纸张参数。
name_zh: 智能打印
license: Proprietary. LICENSE.txt has complete terms
---

# Print Skill

Universal document printing for local Agent applications. Automatically detects platform and uses the appropriate printing backend, with safer defaults for real-world office use.

## Operating Policy

Printing has real-world side effects. Follow this order by default:

1. Confirm the file to print
2. Resolve the target printer (explicit printer or system default)
3. Preview or dry-run when parameters are missing or ambiguous
4. Submit the print job only after the user clearly intends to print

Use fully automatic printing only when the user has already made the intent explicit.

## Quick Start

```bash
# Basic print (uses default printer)
python scripts/print_file.py document.pdf

# Specify printer and copies
python scripts/print_file.py report.docx --printer "HP LaserJet" --copies 2

# Safe preview without printing
python scripts/print_file.py report.docx --printer "HP LaserJet" --dry-run

# Duplex and paper size
python scripts/print_file.py presentation.pptx --duplex long-edge --paper A4

# Page range
python scripts/print_file.py document.pdf --pages 1-5,8,10-12

# List available printers
python scripts/get_printers.py
```

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Direct print |
| Word | `.docx`, `.doc` | Converts to PDF first |
| Excel | `.xlsx`, `.xls` | Converts to PDF first |
| PowerPoint | `.pptx`, `.ppt` | Converts to PDF first |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp` | Direct print |

## Workflow Decision Tree

```
User requests print
    ↓
Get print parameters (or use defaults)
    ↓
For each file:
    ├─ Is PDF/Image? → Direct print
    └─ Is Office? → Convert to PDF → Print
    ↓
Execute print command
    ↓
Return results
```

## Print Parameters

| Parameter | CLI Flag | Values | Default |
|-----------|----------|--------|---------|
| Copies | `--copies`, `-n` | Integer | 1 |
| Printer | `--printer` | String | Default printer |
| Duplex | `--duplex` | `none`, `long-edge`, `short-edge` | System default |
| Paper | `--paper`, `-p` | `Letter`, `A4`, `Legal` | System default |
| Orientation | `--orientation`, `-o` | `portrait`, `landscape` | System default |
| Pages | `--pages`, `-P` | Range (e.g., `1-5,8`) | All |
| Silent | `--silent` | Flag | False |
| Dry run | `--dry-run` | Flag | False |

## Platform Differences

**macOS/Linux (CUPS)**:
- Uses `lp` command
- Default printer: `lpstat -d`
- List printers: `lpstat -p`

**Windows**:
- Primary: `lpr.exe` (requires LPR Port Monitor)
- Fallback: `pdf-to-printer` (Node module)
- Default printer: PowerShell / registry fallback

See `references/platform-differences.md` for details.

## Dependencies

- **LibreOffice**: Office → PDF conversion (auto-detected via `soffice` command)
- **Python 3.6+**: Script execution
- **CUPS** (macOS/Linux): Printing backend
- **LPR Port Monitor** (Windows, optional): Enables `lpr.exe`

## Error Handling

| Error | Action |
|-------|--------|
| File not found | Return `FILE_NOT_FOUND`, prompt user to confirm path |
| Unsupported format | Return `UNSUPPORTED_FORMAT`, suggest supported formats |
| LibreOffice missing | Return `CONVERSION_FAILED`, prompt installation |
| No printer configured | Return `PRINTER_NOT_FOUND`, list available printers |
| Conversion failed | Return `CONVERSION_FAILED` with stderr details |
| Backend unavailable | Return `BACKEND_UNAVAILABLE`, explain how to enable it |

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| **docx** | Reuses LibreOffice conversion: `soffice --headless --convert-to pdf` |
| **xlsx** | Optional recalc before print: call `recalc.py` |
| **pdf** | Pre-processing: merge, extract pages, rotate |

## Print Preview Mode

For preview and parameter suggestions:

```bash
python scripts/print_preview.py document.pdf
```

Analyzes file and suggests:
- Optimal orientation based on page dimensions
- Paper size recommendation
- Page count for copy calculation
- Safe next-step command

## Batch Printing

Print multiple files at once:

```bash
# All PDFs in directory
python scripts/print_file.py *.pdf

# Mixed formats
python scripts/print_file.py report.docx data.xlsx chart.png
```

## Safer Execution Examples

```bash
# Preview exact backend command without printing
python scripts/print_file.py contract.docx --printer "Office Printer" --duplex long-edge --dry-run --json

# If the printer is not configured yet, inspect the system first
python scripts/get_printers.py --json
```

## Code Style Guidelines

1. **Platform abstraction**: All platform-specific code in `scripts/utils.py`
2. **Safety first**: dry-run must be available for non-destructive verification
3. **Error messages**: human-readable + machine-readable `error_code`
4. **Conversion temp files**: cleaned on exit
5. **Observability**: return backend, resolved printer, and job identifier when available

## Test Cases

See `evals/evals.json` for test scenarios:
1. Print single PDF
2. Print Word document with conversion
3. Batch print multiple files

## References

- `references/printing-guide.md` - Complete parameter reference
- `references/platform-differences.md` - OS-specific behaviors
