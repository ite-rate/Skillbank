#!/usr/bin/env python3
"""
Fallback DOCX-to-image converter. Used when LibreOffice (soffice) or Poppler
(pdftoppm) are not available.

Conversion pipeline (attempted in order):
  1. docx2pdf  →  pymupdf: DOCX → PDF (via local Word/LibreOffice) → JPEG/PNG images.
     Works on Windows and macOS when Microsoft Word is installed.
  2. mammoth: DOCX → HTML export (last resort, no image output).
     Used on Linux or any platform where step 1 fails.

Usage:
    python scripts/fallback_docx_to_image.py input.docx --outdir ./pages
    python scripts/fallback_docx_to_image.py input.docx --outdir ./pages --dpi 150 --format png

Dependencies:
    pip install docx2pdf pymupdf       # for step 1 (Win/macOS)
    pip install mammoth                # for step 2 (Linux fallback)
"""

import argparse
import sys
import tempfile
from pathlib import Path


def _convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> bool:
    """
    Convert a .docx file to PDF using docx2pdf, which drives the locally installed
    Microsoft Word (Windows/macOS). Fails gracefully on Linux or without Word.

    Args:
        docx_path: Path to the source .docx file.
        pdf_path:  Destination path for the generated PDF.

    Returns:
        True if the PDF was created successfully, False otherwise.
    """
    try:
        from docx2pdf import convert
    except ImportError:
        print(
            "docx2pdf not installed. Run: pip install docx2pdf",
            file=sys.stderr,
        )
        return False

    try:
        convert(str(docx_path), str(pdf_path))
        return pdf_path.exists()
    except Exception as exc:
        print(f"docx2pdf conversion failed: {exc}", file=sys.stderr)
        return False


def _pdf_to_images(
    pdf_path: Path,
    outdir: Path,
    dpi: int,
    fmt: str,
) -> list[Path]:
    """
    Render each page of a PDF to an image file using pymupdf (no Poppler required).
    pymupdf bundles its own renderer, so no system-level PDF library is needed.

    Args:
        pdf_path: Path to the input PDF file.
        outdir:   Directory where image files will be written.
        dpi:      Output resolution in dots per inch.
        fmt:      Image format: 'jpeg' or 'png'.

    Returns:
        List of paths to the generated image files (one per page).
        Returns an empty list if pymupdf is not installed or rendering fails.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(
            "pymupdf not installed. Run: pip install pymupdf",
            file=sys.stderr,
        )
        return []

    outdir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    ext = "jpg" if fmt == "jpeg" else "png"
    output_paths: list[Path] = []

    doc = fitz.open(str(pdf_path))
    try:
        for page_num, page in enumerate(doc, start=1):
            pixmap = page.get_pixmap(matrix=matrix)
            out_file = outdir / f"page-{page_num}.{ext}"
            if fmt == "jpeg":
                pixmap.save(str(out_file), jpg_quality=90)
            else:
                pixmap.save(str(out_file))
            output_paths.append(out_file)
    finally:
        doc.close()

    return output_paths


def _export_html(docx_path: Path, outdir: Path) -> Path | None:
    """
    Last-resort fallback: export the document as HTML using mammoth.
    Used on Linux or any platform where PDF conversion is unavailable.
    No image files are produced.

    Args:
        docx_path: Path to the source .docx file.
        outdir:    Directory where the HTML file will be written.

    Returns:
        Path to the generated HTML file, or None if mammoth is not installed
        or the export fails.
    """
    try:
        import mammoth
    except ImportError:
        print(
            "mammoth not installed. Run: pip install mammoth",
            file=sys.stderr,
        )
        return None

    outdir.mkdir(parents=True, exist_ok=True)
    html_path = outdir / f"{docx_path.stem}.html"

    try:
        with open(docx_path, "rb") as f:
            result = mammoth.convert_to_html(f)
        html_path.write_text(result.value, encoding="utf-8")
        return html_path
    except Exception as exc:
        print(f"mammoth HTML export failed: {exc}", file=sys.stderr)
        return None


def _print_degraded_notice(messages: list[str]) -> None:
    """
    Print a [DEGRADED MODE] footer to stdout.

    Args:
        messages: Lines describing what was limited and what is missing.
    """
    print("\n---")
    print(
        "[DEGRADED MODE] Output generated using fallback converter. "
        "Missing dependency: soffice (LibreOffice) and/or pdftoppm (Poppler)."
    )
    for msg in messages:
        print(msg)


def main() -> None:
    """Parse CLI arguments and run the fallback conversion pipeline."""
    parser = argparse.ArgumentParser(
        description=(
            "Fallback DOCX-to-image converter. "
            "Uses docx2pdf + pymupdf on Windows/macOS, mammoth HTML export on Linux."
        )
    )
    parser.add_argument("input", help="Path to input .docx file")
    parser.add_argument(
        "--outdir",
        default="./pages",
        help="Output directory for generated files (default: ./pages)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Image resolution in DPI (default: 150)",
    )
    parser.add_argument(
        "--format",
        choices=["jpeg", "png"],
        default="jpeg",
        help="Output image format (default: jpeg)",
    )
    args = parser.parse_args()

    docx_path = Path(args.input)
    outdir = Path(args.outdir)

    if not docx_path.exists():
        print(f"Error: File not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    if docx_path.suffix.lower() != ".docx":
        print("Error: Input file must be a .docx file", file=sys.stderr)
        sys.exit(1)

    # Pipeline step 1: docx2pdf → pymupdf
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / f"{docx_path.stem}.pdf"
        pdf_ok = _convert_docx_to_pdf(docx_path, pdf_path)

        if pdf_ok:
            images = _pdf_to_images(pdf_path, outdir, args.dpi, args.format)
            if images:
                print(f"Generated {len(images)} image(s) in: {outdir}")
                _print_degraded_notice([
                    "Images rendered via docx2pdf (Microsoft Word) + pymupdf.",
                    "For pixel-perfect rendering, install LibreOffice and Poppler.",
                ])
                return

    # Pipeline step 2: mammoth HTML export
    print(
        "Warning: PDF conversion unavailable on this platform. "
        "Falling back to HTML export.",
        file=sys.stderr,
    )
    html_path = _export_html(docx_path, outdir)
    if html_path:
        print(f"HTML export written to: {html_path}")
        _print_degraded_notice([
            "Image conversion is not available (no Microsoft Word or LibreOffice found).",
            "The document has been exported as HTML instead.",
            "To generate page images, install LibreOffice (soffice) and Poppler (pdftoppm).",
        ])
        return

    # All methods failed
    print("Error: All conversion methods failed.", file=sys.stderr)
    print(
        "Install LibreOffice (soffice) and Poppler (pdftoppm) for image conversion.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
