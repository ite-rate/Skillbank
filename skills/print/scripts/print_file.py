#!/usr/bin/env python3
"""
Main print script with safer defaults and richer metadata.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add scripts directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from utils import (  # noqa: E402
    PLATFORM_WINDOWS,
    check_dependencies,
    construct_print_command,
    detect_platform,
    execute_print_command,
    get_available_printers,
    get_default_printer,
)

OFFICE_FORMATS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}
DIRECT_PRINT_FORMATS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}


def resolve_soffice() -> Optional[str]:
    """Locate LibreOffice executable."""
    soffice = shutil.which("soffice")
    if soffice:
        return soffice

    common_paths = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "C:\\Program Files\\LibreOffice\\program\\soffice.exe",
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
    ]
    for candidate in common_paths:
        if Path(candidate).exists():
            return candidate
    return None


def convert_to_pdf(file_path: str, output_dir: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Convert an Office file to PDF using LibreOffice."""
    soffice = resolve_soffice()
    if not soffice:
        return None, "LibreOffice not found. Install LibreOffice to print Office documents."

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="print_convert_")

    input_path = Path(file_path).resolve()
    output_path = Path(output_dir)

    try:
        import subprocess

        cmd = [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_path),
            str(input_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
        )

        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "Unknown LibreOffice conversion error"
            return None, detail

        pdf_path = output_path / f"{input_path.stem}.pdf"
        if pdf_path.exists():
            return str(pdf_path), None

        return None, f"Converted PDF not found in {output_path}"
    except subprocess.TimeoutExpired:
        return None, "LibreOffice conversion timed out after 90 seconds"
    except Exception as error:
        return None, str(error)


def _validate_request(file_path: str, copies: int) -> Optional[Dict[str, Any]]:
    """Validate the print request before any side effects."""
    path = Path(file_path)
    if not path.exists():
        return {
            "success": False,
            "error_code": "FILE_NOT_FOUND",
            "error_message": f"File not found: {file_path}",
            "file": file_path,
        }

    if copies < 1:
        return {
            "success": False,
            "error_code": "INVALID_COPIES",
            "error_message": "Copies must be at least 1",
            "file": file_path,
        }

    ext = path.suffix.lower()
    if ext not in OFFICE_FORMATS and ext not in DIRECT_PRINT_FORMATS:
        return {
            "success": False,
            "error_code": "UNSUPPORTED_FORMAT",
            "error_message": f"Unsupported file format: {ext or '(no extension)'}",
            "file": file_path,
        }

    return None


def print_file(
    file_path: str,
    printer: Optional[str] = None,
    copies: int = 1,
    duplex: Optional[str] = None,
    paper: Optional[str] = None,
    orientation: Optional[str] = None,
    pages: Optional[str] = None,
    silent: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Print a single file or return a dry-run execution plan."""
    validation_error = _validate_request(file_path, copies)
    if validation_error:
        return validation_error

    path = Path(file_path)
    ext = path.suffix.lower()
    needs_conversion = ext in OFFICE_FORMATS
    converted_pdf: Optional[str] = None
    file_to_print = str(path)
    temp_dir: Optional[Path] = None

    try:
        if needs_conversion:
            if not silent:
                print(f"Converting {file_path} to PDF...")
            converted_pdf, conversion_error = convert_to_pdf(file_path)
            if not converted_pdf:
                return {
                    "success": False,
                    "error_code": "CONVERSION_FAILED",
                    "error_message": conversion_error or f"Failed to convert {file_path} to PDF",
                    "file": file_path,
                }
            file_to_print = converted_pdf
            temp_dir = Path(converted_pdf).parent

        resolved_printer = printer or get_default_printer()
        if not resolved_printer:
            return {
                "success": False,
                "error_code": "PRINTER_NOT_FOUND",
                "error_message": "No printer specified and no default printer configured.",
                "file": file_path,
                "available_printers": get_available_printers(),
            }

        cmd, metadata = construct_print_command(
            file_to_print,
            printer=resolved_printer,
            copies=copies,
            duplex=duplex,
            paper=paper,
            orientation=orientation,
            pages=pages,
        )

        result: Dict[str, Any]
        if dry_run:
            result = {
                "success": True,
                "dry_run": True,
                "command": " ".join(cmd) if cmd else "",
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
            }
        elif not cmd:
            result = {
                "success": False,
                "error_code": "BACKEND_UNAVAILABLE",
                "error_message": "No usable print backend found for this platform.",
            }
        else:
            result = execute_print_command(cmd)

        result.update(
            {
                "file": file_path,
                "printed_file": file_to_print,
                "resolved_printer": resolved_printer,
                "copies": copies,
                "converted": needs_conversion,
                "backend": metadata.get("backend"),
                "warnings": metadata.get("warnings", []),
            }
        )

        if dry_run and not result.get("backend"):
            result["success"] = False
            result["error_code"] = "BACKEND_UNAVAILABLE"
            result["error_message"] = "No usable print backend found for this platform."

        return result
    finally:
        if converted_pdf and Path(converted_pdf).exists():
            try:
                os.unlink(converted_pdf)
                if temp_dir and temp_dir.name.startswith("print_convert_") and not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
            except Exception:
                pass


def print_multiple_files(
    file_paths: List[str],
    printer: Optional[str] = None,
    copies: int = 1,
    duplex: Optional[str] = None,
    paper: Optional[str] = None,
    orientation: Optional[str] = None,
    pages: Optional[str] = None,
    silent: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Print multiple files and return aggregated results."""
    results = []
    success_count = 0
    failed_files = []

    for index, file_path in enumerate(file_paths, start=1):
        if not silent:
            action = "Planning" if dry_run else "Printing"
            print(f"[{index}/{len(file_paths)}] {action} {file_path}...")

        result = print_file(
            file_path,
            printer=printer,
            copies=copies,
            duplex=duplex,
            paper=paper,
            orientation=orientation,
            pages=pages,
            silent=silent,
            dry_run=dry_run,
        )
        results.append(result)

        if result.get("success"):
            success_count += 1
        else:
            failed_files.append(
                {
                    "file": file_path,
                    "error_code": result.get("error_code"),
                    "error": result.get("error_message", "Unknown error"),
                }
            )

    total_files = len(file_paths)
    return {
        "success": success_count == total_files,
        "dry_run": dry_run,
        "total_files": total_files,
        "success_count": success_count,
        "failed_count": total_files - success_count,
        "results": results,
        "failed_files": failed_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print files with safer defaults and configurable parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf
  %(prog)s report.docx --printer "HP LaserJet" --copies 2
  %(prog)s *.pdf --duplex long-edge --paper A4
  %(prog)s presentation.pptx --pages 1-5 --dry-run
        """,
    )

    parser.add_argument("files", nargs="+", help="File(s) to print")
    parser.add_argument("-n", "--copies", type=int, default=1, help="Number of copies (default: 1)")
    parser.add_argument("--printer", help="Printer name (default: system default)")
    parser.add_argument("--duplex", choices=["none", "long-edge", "short-edge"], help="Duplex mode")
    parser.add_argument("-p", "--paper", choices=["Letter", "A4", "Legal"], help="Paper size")
    parser.add_argument("-o", "--orientation", choices=["portrait", "landscape"], help="Page orientation")
    parser.add_argument("-P", "--pages", help="Page range (for example: 1-5,8,10-12)")
    parser.add_argument("--silent", action="store_true", help="Suppress progress output")
    parser.add_argument("--dry-run", action="store_true", help="Build the print command without sending a real job")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")

    args = parser.parse_args()

    dependencies = check_dependencies()
    platform = detect_platform()

    if platform == PLATFORM_WINDOWS:
        if not dependencies.get("lpr.exe", False) and not dependencies.get("pdf-to-printer", False):
            print("Warning: no usable Windows print backend found.")
            print("Enable 'LPR Port Monitor' or install 'pdf-to-printer'.")
    elif not dependencies.get("lp", False):
        print("Error: CUPS 'lp' command not found. Cannot print.")
        sys.exit(1)

    if len(args.files) == 1:
        result = print_file(
            args.files[0],
            printer=args.printer,
            copies=args.copies,
            duplex=args.duplex,
            paper=args.paper,
            orientation=args.orientation,
            pages=args.pages,
            silent=args.silent,
            dry_run=args.dry_run,
        )
    else:
        result = print_multiple_files(
            args.files,
            printer=args.printer,
            copies=args.copies,
            duplex=args.duplex,
            paper=args.paper,
            orientation=args.orientation,
            pages=args.pages,
            silent=args.silent,
            dry_run=args.dry_run,
        )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if result.get("success"):
        if args.dry_run:
            print("✓ Dry run completed")
        elif len(args.files) == 1:
            print(f"✓ Print job submitted: {args.files[0]}")
        else:
            print(f"✓ Printed {result['success_count']}/{result['total_files']} files successfully")

        warnings = result.get("warnings", [])
        if warnings:
            for warning in warnings:
                print(f"! {warning}")
        return

    print(f"✗ Print failed: {result.get('error_message', 'Unknown error')}")
    if result.get("available_printers"):
        print("Available printers:")
        for printer_info in result["available_printers"]:
            marker = " [DEFAULT]" if printer_info.get("default") else ""
            print(f"  - {printer_info.get('name')}{marker}")
    sys.exit(1)


if __name__ == "__main__":
    main()
