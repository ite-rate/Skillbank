#!/usr/bin/env python3
"""
Print preview and parameter suggestion tool.
Analyzes files and suggests optimal print parameters.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from utils import get_default_printer

def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """Analyze PDF file and extract print-related information."""
    try:
        # Try pypdf first
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)

            page_count = len(reader.pages)
            if page_count == 0:
                return {"error": "PDF has no pages"}

            # Get first page dimensions
            first_page = reader.pages[0]
            mediabox = first_page.mediabox
            width_pt = float(mediabox.width)
            height_pt = float(mediabox.height)

            # Convert points to inches (1 point = 1/72 inch)
            width_in = width_pt / 72
            height_in = height_pt / 72

            # Determine orientation
            is_landscape = width_in > height_in

            # Suggest paper size
            # US Letter: 8.5 x 11 inches
            # A4: 8.27 x 11.69 inches
            letter_w, letter_h = 8.5, 11
            a4_w, a4_h = 8.27, 11.69

            paper_suggestion = "Letter"
            if abs(width_in - a4_w) < abs(width_in - letter_w):
                paper_suggestion = "A4"

            return {
                "page_count": page_count,
                "page_size_inches": {"width": round(width_in, 2), "height": round(height_in, 2)},
                "suggested_orientation": "landscape" if is_landscape else "portrait",
                "suggested_paper": paper_suggestion,
                "format": "PDF"
            }

        except ImportError:
            # Fallback: basic file info
            file_size = Path(file_path).stat().st_size
            return {
                "page_count": "unknown (pypdf not installed)",
                "file_size_bytes": file_size,
                "format": "PDF",
                "note": "Install pypdf for detailed analysis: pip install pypdf"
            }

    except Exception as e:
        return {"error": str(e)}

def analyze_image(file_path: str) -> Dict[str, Any]:
    """Analyze image file and suggest print parameters."""
    try:
        from PIL import Image

        with Image.open(file_path) as img:
            width, height = img.size
            is_landscape = width > height

            # Calculate dimensions at 300 DPI
            width_in = width / 300
            height_in = height / 300

            return {
                "dimensions_pixels": {"width": width, "height": height},
                "dimensions_at_300dpi_inches": {"width": round(width_in, 2), "height": round(height_in, 2)},
                "suggested_orientation": "landscape" if is_landscape else "portrait",
                "format": img.format or "Image"
            }

    except ImportError:
        file_size = Path(file_path).stat().st_size
        return {
            "file_size_bytes": file_size,
            "format": "Image",
            "note": "Install Pillow for detailed analysis: pip install Pillow"
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_office(file_path: str) -> Dict[str, Any]:
    """Analyze Office file (limited preview without conversion)."""
    path = Path(file_path)
    ext = path.suffix.lower()

    file_size = path.stat().st_size

    type_map = {
        ".docx": "Word Document",
        ".doc": "Word Document (Legacy)",
        ".xlsx": "Excel Spreadsheet",
        ".xls": "Excel Spreadsheet (Legacy)",
        ".pptx": "PowerPoint Presentation",
        ".ppt": "PowerPoint Presentation (Legacy)"
    }

    return {
        "format": type_map.get(ext, f"Office File ({ext})"),
        "file_size_bytes": file_size,
        "note": "Office files are converted to PDF before printing",
        "conversion_required": True
    }

def preview_file(file_path: str, copies: int = 1) -> Dict[str, Any]:
    """Generate print preview and suggestions for a file."""
    path = Path(file_path)

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    # Determine file type and analyze
    ext = path.suffix.lower()

    if ext == ".pdf":
        analysis = analyze_pdf(file_path)
    elif ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}:
        analysis = analyze_image(file_path)
    elif ext in {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}:
        analysis = analyze_office(file_path)
    else:
        analysis = {
            "format": "Unknown",
            "error": f"Unsupported file format: {ext}"
        }

    # Add system info
    default_printer = get_default_printer()

    result = {
        "file": str(path),
        "analysis": analysis,
        "default_printer": default_printer,
        "suggested_parameters": {}
    }

    # Build suggested command
    if "suggested_orientation" in analysis:
        result["suggested_parameters"]["orientation"] = analysis["suggested_orientation"]

    if "suggested_paper" in analysis:
        result["suggested_parameters"]["paper"] = analysis["suggested_paper"]

    if copies > 1:
        result["suggested_parameters"]["copies"] = copies

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Analyze files and suggest print parameters",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("file", help="File to analyze")
    parser.add_argument("-n", "--copies", type=int, default=1, help="Number of copies (for suggestion)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = preview_file(args.file, args.copies)

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print("PRINT PREVIEW")
        print("=" * 60)

        print(f"\nFile: {result.get('file', 'N/A')}")

        analysis = result.get("analysis", {})
        if "error" in analysis:
            print(f"\n✗ Error: {analysis['error']}")
        else:
            print(f"\nFormat: {analysis.get('format', 'Unknown')}")

            if "page_count" in analysis:
                print(f"Pages: {analysis['page_count']}")

            if "page_size_inches" in analysis:
                size = analysis["page_size_inches"]
                print(f"Page Size: {size['width']}\" x {size['height']}\"")

            if "dimensions_pixels" in analysis:
                dims = analysis["dimensions_pixels"]
                print(f"Dimensions: {dims['width']} x {dims['height']} pixels")

            if "dimensions_at_300dpi_inches" in analysis:
                dims = analysis["dimensions_at_300dpi_inches"]
                print(f"At 300 DPI: {dims['width']}\" x {dims['height']}\"")

            if "suggested_orientation" in analysis:
                print(f"Suggested Orientation: {analysis['suggested_orientation']}")

            if "suggested_paper" in analysis:
                print(f"Suggested Paper: {analysis['suggested_paper']}")

            if "note" in analysis:
                print(f"\nNote: {analysis['note']}")

        print(f"\nDefault Printer: {result.get('default_printer', '(none)')}")

        suggested = result.get("suggested_parameters", {})
        if suggested:
            print("\nSuggested Print Command:")
            cmd_parts = ["python", "scripts/print_file.py", args.file]
            for k, v in suggested.items():
                cmd_parts.extend([f"--{k}", str(v)])
            cmd_parts.append("--dry-run")
            print(" " + " ".join(cmd_parts))

        print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
