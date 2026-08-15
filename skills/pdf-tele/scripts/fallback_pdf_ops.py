#!/usr/bin/env python3
"""
Fallback PDF operations (degraded mode).

Used when system CLI tools like `qpdf` / `pdftk` are unavailable.
This script provides basic operations using pure-Python `pypdf`:
  - merge
  - split (into individual page PDFs)
  - rotate pages
  - encrypt (optional; requires passwords)

Limitations:
  - Does not aim to replicate all qpdf/pdftk advanced behaviors.
  - Only basic operations are guaranteed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable


def _require_pypdf():
    try:
        import pypdf  # type: ignore
    except ImportError as exc:
        print(
            "[DEGRADED MODE] pypdf is not installed.",
            "Run: pip install pypdf",
            file=sys.stderr,
        )
        raise exc
    return pypdf


def merge_pdfs(input_pdfs: list[Path], out_pdf: Path) -> None:
    pypdf = _require_pypdf()
    PdfReader = pypdf.PdfReader  # type: ignore
    PdfWriter = pypdf.PdfWriter  # type: ignore

    writer = PdfWriter()
    for pdf_path in input_pdfs:
        reader = PdfReader(str(pdf_path))
        for page in reader.pages:
            writer.add_page(page)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def split_to_pages(input_pdf: Path, out_dir: Path) -> list[Path]:
    pypdf = _require_pypdf()
    PdfReader = pypdf.PdfReader  # type: ignore
    PdfWriter = pypdf.PdfWriter  # type: ignore

    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(input_pdf))

    out_paths: list[Path] = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = out_dir / f"page_{i}.pdf"
        with out_path.open("wb") as f:
            writer.write(f)
        out_paths.append(out_path)

    return out_paths


def rotate_pdf(input_pdf: Path, out_pdf: Path, *, degrees: int) -> None:
    if degrees % 90 != 0:
        raise ValueError("degrees must be a multiple of 90")

    pypdf = _require_pypdf()
    PdfReader = pypdf.PdfReader  # type: ignore
    PdfWriter = pypdf.PdfWriter  # type: ignore

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(degrees)
        writer.add_page(page)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def encrypt_pdf(input_pdf: Path, out_pdf: Path, *, user_password: str, owner_password: str) -> None:
    pypdf = _require_pypdf()
    PdfReader = pypdf.PdfReader  # type: ignore
    PdfWriter = pypdf.PdfWriter  # type: ignore

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(user_password, owner_password)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with out_pdf.open("wb") as f:
        writer.write(f)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fallback PDF operations using pypdf.")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_merge = sub.add_parser("merge", help="Merge multiple PDFs into one.")
    p_merge.add_argument("inputs", nargs="+", type=Path, help="Input PDF files.")
    p_merge.add_argument("--out", "--output", dest="out", type=Path, required=True, help="Output merged PDF.")

    p_split = sub.add_parser("split", help="Split PDF into per-page PDFs.")
    p_split.add_argument("input", type=Path, help="Input PDF file.")
    p_split.add_argument("--outdir", type=Path, required=True, help="Output directory for pages.")

    p_rotate = sub.add_parser("rotate", help="Rotate all pages by N degrees.")
    p_rotate.add_argument("input", type=Path, help="Input PDF file.")
    p_rotate.add_argument("--out", "--output", dest="out", type=Path, required=True, help="Output PDF.")
    p_rotate.add_argument("--degrees", type=int, default=90, help="Rotation degrees (multiple of 90).")

    p_encrypt = sub.add_parser("encrypt", help="Encrypt PDF with user/owner passwords.")
    p_encrypt.add_argument("input", type=Path, help="Input PDF file.")
    p_encrypt.add_argument("--out", "--output", dest="out", type=Path, required=True, help="Output PDF.")
    p_encrypt.add_argument("--user-password", type=str, required=True)
    p_encrypt.add_argument("--owner-password", type=str, required=True)

    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    print("[DEGRADED MODE] qpdf/pdftk unavailable. Using pypdf-based basic operations.")
    print("For best compatibility, install qpdf / pdftk (as appropriate).")

    if args.cmd == "merge":
        merge_pdfs(args.inputs, args.out)
        print(f"Written merged PDF: {args.out}")
    elif args.cmd == "split":
        pages = split_to_pages(args.input, args.outdir)
        print(f"Written {len(pages)} page PDFs to: {args.outdir}")
    elif args.cmd == "rotate":
        rotate_pdf(args.input, args.out, degrees=args.degrees)
        print(f"Written rotated PDF: {args.out}")
    elif args.cmd == "encrypt":
        encrypt_pdf(
            args.input,
            args.out,
            user_password=args.user_password,
            owner_password=args.owner_password,
        )
        print(f"Written encrypted PDF: {args.out}")
    else:
        raise RuntimeError("Unknown command")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

