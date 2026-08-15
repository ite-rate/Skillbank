"""
Convert each page of a PDF into image files.

Normal path:
  - Uses `pdf2image.convert_from_path` which typically requires poppler-utils.

Degraded path:
  - If pdf2image fails (missing poppler, rendering errors), falls back to a
    pure-Python renderer based on `pypdfium2`.

This script is used by `forms.md` and should therefore be robust:
it must still produce output images even when system dependencies are missing.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _load_fallback_renderer():
    """
    Import fallback renderer from the local scripts directory.
    """

    scripts_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(scripts_dir))
    try:
        from fallback_pdf_to_images import render_pdf_to_images  # type: ignore
    finally:
        # Keep sys.path clean after import.
        if str(scripts_dir) in sys.path:
            sys.path.remove(str(scripts_dir))
    return render_pdf_to_images


def convert(
    pdf_path: Path,
    output_dir: Path,
    *,
    dpi: int = 200,
    max_dim: int = 1000,
    force_fallback: bool = False,
    image_format: str = "png",
) -> list[Path]:
    """
    Convert a PDF to per-page images.

    Args:
        pdf_path: Input PDF path.
        output_dir: Output directory (created if missing).
        dpi: Render DPI for both normal and degraded paths.
        max_dim: Optional max width/height; downscales images if needed.
        force_fallback: When True, skip pdf2image and directly use degraded path.
        image_format: Output image format: 'png' or 'jpg'.

    Returns:
        List of generated image file paths.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    if force_fallback:
        render_pdf_to_images = _load_fallback_renderer()
        print("[DEGRADED MODE] --force-fallback is enabled. Using pypdfium2 renderer.")
        return render_pdf_to_images(pdf_path, output_dir, dpi=dpi, image_format=image_format)

    # Normal path: pdf2image (poppler-backed)
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(pdf_path), dpi=dpi)
        out_paths: list[Path] = []
        for i, image in enumerate(images):
            # Scale image if needed to keep width/height under `max_dim`.
            width, height = image.size
            if width > max_dim or height > max_dim:
                scale_factor = min(max_dim / width, max_dim / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height))

            ext = image_format.lower()
            image_path = output_dir / f"page_{i+1}.{ext}"
            image.save(str(image_path))
            print(f"Saved page {i+1} as {image_path} (size: {image.size})")
            out_paths.append(image_path)

        print(f"Converted {len(out_paths)} pages to {image_format.upper()} images (normal path)")
        return out_paths
    except Exception as exc:
        print(f"[DEGRADED MODE] pdf2image conversion failed: {exc}")
        print("Using pypdfium2 fallback renderer. For best results, install poppler-utils.")

        render_pdf_to_images = _load_fallback_renderer()
        return render_pdf_to_images(pdf_path, output_dir, dpi=dpi, image_format=image_format)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PDF pages to images.")
    parser.add_argument("input_pdf", type=Path, help="Path to input PDF.")
    parser.add_argument("output_directory", type=Path, help="Directory to write output images.")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI. Default: 200.")
    parser.add_argument("--max-dim", type=int, default=1000, help="Max image width/height. Default: 1000.")
    parser.add_argument(
        "--format",
        dest="image_format",
        choices=["png", "jpg", "jpeg"],
        default="png",
        help="Output image format. Default: png.",
    )
    parser.add_argument(
        "--force-fallback",
        action="store_true",
        help="Force degraded mode fallback (useful for testing).",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    fmt = args.image_format
    if fmt == "jpeg":
        fmt = "jpg"
    convert(
        args.input_pdf,
        args.output_directory,
        dpi=args.dpi,
        max_dim=args.max_dim,
        force_fallback=bool(args.force_fallback),
        image_format=fmt,
    )
