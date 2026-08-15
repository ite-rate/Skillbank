#!/usr/bin/env python3
"""
Fallback PDF-to-images converter (degraded mode).

Used when poppler-utils / `pdf2image` cannot render the PDF.
This script uses `pypdfium2`, which is installed via pip and does not require
system-level poppler/CLI tools.

Output:
  - One image per page: page_1.png, page_2.png, ...
  - Prints a clear "[DEGRADED MODE]" message and guidance.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def render_pdf_to_images(
    pdf_path: Path,
    outdir: Path,
    *,
    dpi: int = 200,
    image_format: str = "png",
) -> list[Path]:
    """
    Render a PDF into per-page images using pypdfium2.

    Args:
        pdf_path: Input PDF.
        outdir: Output directory.
        dpi: Target DPI.
        image_format: 'png' or 'jpg'.

    Returns:
        List of generated image paths.
    """

    outdir.mkdir(parents=True, exist_ok=True)
    image_format = image_format.lower()
    if image_format == "jpeg":
        image_format = "jpg"
    if image_format not in {"png", "jpg"}:
        raise ValueError("image_format must be 'png' or 'jpg'")

    try:
        import pypdfium2 as pdfium  # type: ignore
    except ImportError as exc:
        print(
            "[DEGRADED MODE] pypdfium2 is not installed.",
            "Run: pip install pypdfium2",
            file=sys.stderr,
        )
        raise exc

    pdf = pdfium.PdfDocument(str(pdf_path))
    n_pages = len(pdf)

    # pypdfium2 uses a scale factor where 1.0 roughly corresponds to 72 DPI.
    scale = max(0.1, dpi / 72.0)

    out_paths: list[Path] = []
    for i in range(n_pages):
        page = pdf[i]
        bitmap = page.render(scale=scale)
        pil_img = bitmap.to_pil()

        out_path = outdir / f"page_{i+1}.{image_format}"
        if image_format == "jpg":
            pil_img.save(str(out_path), quality=95)
        else:
            pil_img.save(str(out_path))

        print(f"Saved page {i+1} as {out_path}")
        out_paths.append(out_path)

    return out_paths


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fallback PDF-to-images using pypdfium2.")
    parser.add_argument("input_pdf", type=Path, help="Path to input PDF.")
    parser.add_argument("--outdir", type=Path, required=True, help="Output directory for images.")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI. Default: 200.")
    parser.add_argument(
        "--format",
        dest="image_format",
        choices=["png", "jpg", "jpeg"],
        default="png",
        help="Output format. Default: png.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    print("[DEGRADED MODE] poppler/pdf2image unavailable. Using pypdfium2 renderer.")
    print("For best results, install poppler-utils for consistent rendering.")

    render_pdf_to_images(
        args.input_pdf,
        args.outdir,
        dpi=args.dpi,
        image_format=args.image_format,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

