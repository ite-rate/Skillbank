#!/usr/bin/env python3
"""
Fallback text extraction from PDF (degraded mode).

Used when system CLI tools like `pdftotext` / poppler-backed pipelines are
unavailable.

This script uses pure-Python libraries (pip-installable) to extract text
and (optionally) tables.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable


def _to_markdown_table(rows: list[list[str]]) -> str:
    """
    Convert an extracted table (rows) into a basic Markdown table.
    This is a best-effort conversion and may not preserve complex layouts.
    """

    if not rows:
        return ""

    # Assume first row is header.
    header = rows[0]
    body = rows[1:]

    def _escape(cell: str) -> str:
        cell = cell.replace("\n", " ").strip()
        return cell.replace("|", "\\|")

    header_cells = [_escape(c) for c in header]
    body_cells = [[_escape(c) for c in r] for r in body]

    col_count = max(len(header_cells), *(len(r) for r in body_cells), 0)
    header_cells += [""] * (col_count - len(header_cells))

    md = []
    md.append("| " + " | ".join(header_cells) + " |")
    md.append("| " + " | ".join(["---"] * col_count) + " |")

    for r in body_cells:
        r = r + [""] * (col_count - len(r))
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)


def extract_text_and_tables(
    pdf_path: Path,
    *,
    extract_tables: bool = False,
) -> str:
    """
    Extract text (and optionally tables) from a PDF.

    Args:
        pdf_path: Input PDF file.
        extract_tables: Whether to try table extraction.

    Returns:
        Extracted content as a text/markdown string.
    """

    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        print(
            "[DEGRADED MODE] pdfplumber is not installed.",
            "Run: pip install pdfplumber",
            file=sys.stderr,
        )
        raise exc

    chunks: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            chunks.append(f"\n## Page {page_index}\n")

            text = page.extract_text() or ""
            text = text.strip()
            if text:
                chunks.append(text)

            if extract_tables:
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
                for t_index, table in enumerate(tables, start=1):
                    if not table:
                        continue
                    md = _to_markdown_table(table)
                    if md.strip():
                        chunks.append(f"\n### Table {t_index}\n")
                        chunks.append(md)

    return "\n".join(chunks).strip() + "\n"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fallback PDF text extraction using pdfplumber.")
    parser.add_argument("input_pdf", type=Path, help="Path to input PDF.")
    parser.add_argument("--out", "--output", dest="out", type=Path, default=None, help="Write result to file. If omitted, stdout.")
    parser.add_argument("--tables", action="store_true", help="Try table extraction (best-effort).")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    print("[DEGRADED MODE] poppler/pdftotext unavailable. Using pdfplumber fallback.")
    print("For best results, install poppler-utils (pdftotext) and/or use native pipelines.")

    content = extract_text_and_tables(args.input_pdf, extract_tables=bool(args.tables))

    if args.out is None:
        sys.stdout.write(content)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content, encoding="utf-8")
        print(f"Written output to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

