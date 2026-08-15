#!/usr/bin/env python3
"""
Fallback text extraction from .docx files using python-docx.

Used when `pandoc` is not available. Extracts document content (headings, paragraphs,
tables, lists) to Markdown format. Tracked changes are detected and flagged, but are
NOT fully rendered: deleted text is hidden and inserted text is shown as accepted.

Usage:
    python scripts/fallback_text_extract.py input.docx -o output.md
    python scripts/fallback_text_extract.py input.docx        # prints to stdout

Dependencies:
    pip install python-docx
"""

import argparse
import sys
from pathlib import Path


def _check_dependencies() -> None:
    """Verify python-docx is installed; exit with a helpful message if not."""
    try:
        import docx  # noqa: F401
    except ImportError:
        print(
            "Error: python-docx is not installed. Run: pip install python-docx",
            file=sys.stderr,
        )
        sys.exit(1)


def _heading_level(style_name: str) -> int | None:
    """
    Map a Word paragraph style name to a Markdown heading level (1–6).

    Args:
        style_name: The paragraph style name from python-docx.

    Returns:
        Heading level (1–6) if the style is a heading, otherwise None.
    """
    name = style_name.lower()
    for level in range(1, 7):
        if f"heading {level}" in name:
            return level
    return None


def _has_tracked_changes(para_elem) -> bool:
    """
    Check whether a paragraph XML element contains any tracked change tags.

    Args:
        para_elem: The lxml element for a w:p paragraph.

    Returns:
        True if w:ins or w:del elements are present anywhere in the paragraph.
    """
    from docx.oxml.ns import qn

    return (
        para_elem.find(f".//{qn('w:ins')}") is not None
        or para_elem.find(f".//{qn('w:del')}") is not None
    )


def _para_text_accepted(para_elem) -> str:
    """
    Extract the "accepted" text from a paragraph: include w:t runs, skip w:delText.

    Args:
        para_elem: The lxml element for a w:p paragraph.

    Returns:
        Concatenated text content with deletions omitted.
    """
    from docx.oxml.ns import qn

    parts: list[str] = []
    for node in para_elem.iter():
        if node.tag == qn("w:t"):
            parts.append(node.text or "")
        # w:delText is intentionally skipped (deleted content)
    return "".join(parts).strip()


def _paragraph_to_md(para) -> str:
    """
    Convert a python-docx Paragraph object to a Markdown string.

    Handles headings (mapped from Word styles), bullet lists, numbered lists,
    and plain paragraphs. Appends a tracked-change annotation when present.

    Args:
        para: A python-docx Paragraph instance.

    Returns:
        Markdown-formatted string, or empty string if the paragraph has no text.
    """
    elem = para._element
    text = _para_text_accepted(elem)
    if not text:
        return ""

    tracked = _has_tracked_changes(elem)
    annotation = " *(contains tracked changes)*" if tracked else ""
    style_name = para.style.name if para.style else ""

    # Heading styles
    level = _heading_level(style_name)
    if level:
        return f"{'#' * level} {text}{annotation}"

    # List styles
    lower_style = style_name.lower()
    if "list bullet" in lower_style:
        return f"- {text}{annotation}"
    if "list number" in lower_style:
        return f"1. {text}{annotation}"

    return f"{text}{annotation}"


def _table_to_md(table) -> str:
    """
    Convert a python-docx Table object to a Markdown table string.

    The first row is treated as the header row with a separator line inserted below it.
    Newlines within cells are collapsed to spaces.

    Args:
        table: A python-docx Table instance.

    Returns:
        Multi-line Markdown table string.
    """
    lines: list[str] = []
    for i, row in enumerate(table.rows):
        cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
        lines.append("| " + " | ".join(cells) + " |")
        if i == 0:
            lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(lines)


def extract_to_markdown(docx_path: Path) -> tuple[str, bool]:
    """
    Extract the content of a .docx file to a Markdown string.

    Iterates over body children in document order so that paragraphs and tables
    are interleaved correctly. Returns the content and whether tracked changes
    were detected anywhere in the document.

    Args:
        docx_path: Path to the .docx file.

    Returns:
        A tuple of (markdown_content, has_tracked_changes).
    """
    docx_document_factory = getattr(__import__("docx"), "Document")
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = docx_document_factory(str(docx_path))
    blocks: list[str] = []
    has_tracked_changes = False

    for child in doc.element.body:
        tag = child.tag
        if tag == qn("w:p"):
            para = Paragraph(child, doc)
            md_line = _paragraph_to_md(para)
            if md_line:
                if "*(contains tracked changes)*" in md_line:
                    has_tracked_changes = True
                blocks.append(md_line)
        elif tag == qn("w:tbl"):
            table = Table(child, doc)
            blocks.append(_table_to_md(table))

    return "\n\n".join(blocks), has_tracked_changes


def _build_degraded_notice(has_tracked_changes: bool) -> str:
    """
    Build the [DEGRADED MODE] footer appended to fallback output.

    Args:
        has_tracked_changes: Whether any tracked changes were detected in the document.

    Returns:
        Multi-line notice string.
    """
    lines = [
        "",
        "---",
        "[DEGRADED MODE] Output generated using python-docx fallback. Missing dependency: pandoc.",
    ]
    if has_tracked_changes:
        lines.append(
            "Tracked changes detected but NOT fully rendered: "
            "deleted text is hidden, inserted text shown as accepted."
        )
    lines.append("Install pandoc for complete tracked-change rendering.")
    return "\n".join(lines)


def main() -> None:
    """Parse CLI arguments, run extraction, and write output."""
    parser = argparse.ArgumentParser(
        description=(
            "Fallback DOCX text extraction via python-docx. "
            "Use when pandoc is not available."
        )
    )
    parser.add_argument("input", help="Path to input .docx file")
    parser.add_argument(
        "-o", "--output", help="Output Markdown file path (omit to print to stdout)"
    )
    args = parser.parse_args()

    _check_dependencies()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() != ".docx":
        print("Error: Input file must be a .docx file", file=sys.stderr)
        sys.exit(1)

    content, has_tracked_changes = extract_to_markdown(input_path)
    output = content + _build_degraded_notice(has_tracked_changes)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        print(f"Output written to: {output_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
