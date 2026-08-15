#!/usr/bin/env python3
"""
merge.py — Merge cover.pdf + body.pdf → final.pdf and print a QA report.

Usage:
    python3 merge.py --cover cover.pdf --body body.pdf --out final.pdf
    python3 merge.py --cover cover.pdf --body body.pdf --output final.pdf --title "My Report" --author "Me" --subject "Quarterly plan"

Metadata defaults:
    Explicit CLI args win. Missing fields are inherited from cover/body metadata.
    If no title is available, the output filename stem is used. If no author is
    available, TeleAgent is used.

Exit codes: 0 success, 1 bad args/missing file, 2 missing dep, 3 merge error
"""

import argparse
import importlib.util
import json
import os
import sys


def ensure_deps():
    if importlib.util.find_spec("pypdf") is None:
        import subprocess

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--break-system-packages",
                "-q",
                "pypdf",
            ]
        )


ensure_deps()

from pypdf import PdfWriter, PdfReader


def _clean_meta_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _first_metadata_value(readers: list, key: str) -> str:
    placeholders = {
        "/Title": {"untitled", "(anonymous)"},
        "/Author": {"anonymous", "(anonymous)"},
        "/Subject": {"unspecified", "(unspecified)"},
    }
    for reader in readers:
        try:
            value = _clean_meta_value(reader.metadata.get(key))
        except Exception:
            value = ""
        if value and value.lower() not in placeholders.get(key, set()):
            return value
    return ""


def _filename_title(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    return stem.replace("_", " ").replace("-", " ").strip() or "Untitled Document"


def _pdf_metadata(title: str = "", author: str = "", subject: str = "") -> dict:
    meta = {
        "/Creator": "TeleAgent PDF skill",
        "/Producer": "TeleAgent PDF skill",
    }
    if title:
        meta["/Title"] = title
    if author:
        meta["/Author"] = author
    if subject:
        meta["/Subject"] = subject
    return meta


def merge(
    cover_path: str,
    body_path: str,
    out_path: str,
    title: str = "",
    author: str = "",
    subject: str = "",
) -> dict:
    writer = PdfWriter()
    readers = []

    for fpath, label in [(cover_path, "cover"), (body_path, "body")]:
        if not os.path.exists(fpath):
            return {"status": "error", "error": f"{label} file not found: {fpath}"}
        reader = PdfReader(fpath)
        readers.append(reader)
        for page in reader.pages:
            writer.add_page(page)

    title = title or _first_metadata_value(readers, "/Title") or _filename_title(out_path)
    author = author or _first_metadata_value(readers, "/Author") or "TeleAgent"
    subject = subject or _first_metadata_value(readers, "/Subject")

    # Set PDF metadata so browsers and PDF readers show a useful tab title.
    writer.add_metadata(_pdf_metadata(title, author, subject))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)

    size_kb = os.path.getsize(out_path) // 1024
    total_pages = len(writer.pages)

    # ── QA checks ─────────────────────────────────────────────────────────────
    warnings = []

    # Page count sanity
    cover_pages = len(PdfReader(cover_path).pages)
    body_pages = len(PdfReader(body_path).pages)
    if cover_pages != 1:
        warnings.append(f"Cover PDF has {cover_pages} pages (expected 1)")

    # File size sanity
    if size_kb < 20:
        warnings.append(f"Output is very small ({size_kb} KB) — may have blank pages")
    if size_kb > 50_000:
        warnings.append(
            f"Output is very large ({size_kb} KB) — consider compressing images"
        )

    report = {
        "status": "ok",
        "out": out_path,
        "total_pages": total_pages,
        "cover_pages": cover_pages,
        "body_pages": body_pages,
        "size_kb": size_kb,
    }
    if warnings:
        report["warnings"] = warnings

    return report


def main():
    parser = argparse.ArgumentParser(description="Merge cover + body PDFs")
    parser.add_argument("--cover", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--out", "--output", dest="out", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--subject", default="")
    args = parser.parse_args()

    result = merge(args.cover, args.body, args.out, args.title, args.author, args.subject)

    if result["status"] == "error":
        print(json.dumps(result), file=sys.stderr)
        sys.exit(3)

    print(json.dumps(result))

    # Human-readable QA summary
    print(f"\n-- Build complete ------------------------------------------")
    print(f"  Output  : {result['out']}")
    print(
        f"  Pages   : {result['total_pages']} total (1 cover + {result['body_pages']} body)"
    )
    print(f"  Size    : {result['size_kb']} KB")
    if result.get("warnings"):
        print(f"  [!] Warnings:")
        for w in result["warnings"]:
            print(f"     - {w}")
    else:
        print(f"  [OK] No issues detected")
    print(f"------------------------------------------------------------\n")


if __name__ == "__main__":
    main()
