#!/usr/bin/env python3
"""Render static TOC entries for .docx files without Win COM."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

# Register all OOXML namespaces to preserve prefixes from docx-js output.
# Without these, ET.tostring() generates ns1/ns2/... which breaks
# mc:Ignorable and other namespace-dependent attributes.
for _prefix, _uri in [
    ("w", "http://schemas.openxmlformats.org/wordprocessingml/2006/main"),
    ("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006"),
    ("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships"),
    ("w14", "http://schemas.microsoft.com/office/word/2010/wordml"),
    ("w15", "http://schemas.microsoft.com/office/word/2012/wordml"),
    ("wpc", "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"),
    ("wp14", "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"),
    ("wp", "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"),
    ("wpg", "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"),
    ("wpi", "http://schemas.microsoft.com/office/word/2010/wordprocessingInk"),
    ("wne", "http://schemas.microsoft.com/office/word/2006/wordml"),
    ("wps", "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"),
    ("w10", "urn:schemas-microsoft-com:office:word"),
    ("o", "urn:schemas-microsoft-com:office:office"),
    ("v", "urn:schemas-microsoft-com:vml"),
    ("m", "http://schemas.openxmlformats.org/officeDocument/2006/math"),
    ("w16cid", "http://schemas.microsoft.com/office/word/2016/wordml/cid"),
    ("w16cex", "http://schemas.microsoft.com/office/word/2018/wordml/cex"),
    ("w16du", "http://schemas.microsoft.com/office/word/2023/wordml/word16du"),
]:
    ET.register_namespace(_prefix, _uri)


def w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def get_w_attr(elem: ET.Element | None, name: str) -> str:
    return elem.get(w(name), "") if elem is not None else ""


def set_w_attr(elem: ET.Element, name: str, value: str) -> None:
    elem.set(w(name), value)


def contains_toc_field(node: ET.Element) -> bool:
    for instr in node.iter(w("instrText")):
        if "TOC" in (instr.text or "").upper():
            return True
    for fld in node.iter(w("fldSimple")):
        if "TOC" in get_w_attr(fld, "instr").upper():
            return True
    return False


def extract_toc_instruction(node: ET.Element) -> str:
    parts: list[str] = []
    for instr in node.iter(w("instrText")):
        text = (instr.text or "").strip()
        if text:
            parts.append(text)
    for fld in node.iter(w("fldSimple")):
        text = get_w_attr(fld, "instr").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def parse_heading_range(instruction: str) -> tuple[int, int]:
    match = re.search(r'\\o\s*"(\d+)-(\d+)"', instruction)
    if not match:
        return (1, 3)
    start, end = int(match.group(1)), int(match.group(2))
    if start > end:
        raise ValueError(f"Invalid TOC level range: {start}-{end}")
    return (start, end)


def find_toc_block(body: ET.Element) -> ET.Element | None:
    for child in list(body):
        if contains_toc_field(child):
            return child
    return None


def paragraph_heading_level(paragraph: ET.Element) -> int | None:
    p_pr = paragraph.find("w:pPr", NS)
    if p_pr is None:
        return None
    p_style = p_pr.find("w:pStyle", NS)
    style_val = get_w_attr(p_style, "val").lower()
    style_match = re.search(r"heading\s*([1-9])$", style_val)
    if style_match:
        return int(style_match.group(1))
    outline = p_pr.find("w:outlineLvl", NS)
    outline_val = get_w_attr(outline, "val")
    return int(outline_val) + 1 if outline_val.isdigit() else None


def paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    for node in paragraph.iter():
        if node.tag == w("t"):
            parts.append(node.text or "")
        elif node.tag == w("tab"):
            parts.append(" ")
        elif node.tag == w("noBreakHyphen"):
            parts.append("-")
    return " ".join("".join(parts).split())


def iter_paragraphs_excluding_toc(body: ET.Element, toc_block: ET.Element) -> Iterable[ET.Element]:
    for child in list(body):
        if child is toc_block:
            continue
        if child.tag == w("p"):
            yield child
        else:
            yield from child.iter(w("p"))


def collect_bookmark_state(root: ET.Element) -> tuple[int, set[str]]:
    max_id = -1
    names: set[str] = set()
    for start in root.iter(w("bookmarkStart")):
        raw_id = get_w_attr(start, "id")
        if raw_id.isdigit():
            max_id = max(max_id, int(raw_id))
        name = get_w_attr(start, "name")
        if name:
            names.add(name)
    return (max_id + 1, names)


def first_bookmark_name(paragraph: ET.Element) -> str | None:
    for start in paragraph.iter(w("bookmarkStart")):
        name = get_w_attr(start, "name")
        if name and name != "_GoBack":
            return name
    return None


def add_bookmark(paragraph: ET.Element, bookmark_id: int, bookmark_name: str) -> None:
    start = ET.Element(w("bookmarkStart"))
    set_w_attr(start, "id", str(bookmark_id))
    set_w_attr(start, "name", bookmark_name)
    end = ET.Element(w("bookmarkEnd"))
    set_w_attr(end, "id", str(bookmark_id))
    insert_index = 1 if len(paragraph) > 0 and paragraph[0].tag == w("pPr") else 0
    paragraph.insert(insert_index, start)
    paragraph.append(end)


@dataclass(frozen=True)
class TocEntry:
    level: int
    text: str
    anchor: str


def make_toc_paragraph(entry: TocEntry) -> ET.Element:
    paragraph = ET.Element(w("p"))
    p_pr = ET.SubElement(paragraph, w("pPr"))
    p_style = ET.SubElement(p_pr, w("pStyle"))
    set_w_attr(p_style, "val", f"TOC{entry.level}")
    hyperlink = ET.SubElement(paragraph, w("hyperlink"))
    set_w_attr(hyperlink, "anchor", entry.anchor)
    set_w_attr(hyperlink, "history", "1")
    run = ET.SubElement(hyperlink, w("r"))
    r_pr = ET.SubElement(run, w("rPr"))
    r_style = ET.SubElement(r_pr, w("rStyle"))
    set_w_attr(r_style, "val", "Hyperlink")
    ET.SubElement(run, w("t")).text = entry.text
    return paragraph


def collect_toc_entries(
    root: ET.Element, body: ET.Element, toc_block: ET.Element, start_level: int, end_level: int
) -> tuple[list[TocEntry], int]:
    next_bookmark_id, used_names = collect_bookmark_state(root)
    added = 0
    entries: list[TocEntry] = []
    for paragraph in iter_paragraphs_excluding_toc(body, toc_block):
        level = paragraph_heading_level(paragraph)
        if level is None or not (start_level <= level <= end_level):
            continue
        text = paragraph_text(paragraph)
        if not text:
            continue
        anchor = first_bookmark_name(paragraph)
        if anchor is None:
            while True:
                anchor = f"toc_auto_{next_bookmark_id}"
                if anchor not in used_names:
                    break
                next_bookmark_id += 1
            add_bookmark(paragraph, next_bookmark_id, anchor)
            used_names.add(anchor)
            next_bookmark_id += 1
            added += 1
        entries.append(TocEntry(level=level, text=text, anchor=anchor))
    return (entries, added)


def _is_pagebreak_paragraph(elem: ET.Element) -> bool:
    """Check if a paragraph is just a page-break marker."""
    if elem.tag != w("p"):
        return False
    for br in elem.iter(w("br")):
        if br.get(w("type")) == "page":
            return True
    return False


def _has_pagebreak_before(elem: ET.Element) -> bool:
    """Check if a paragraph already has pageBreakBefore."""
    if elem.tag != w("p"):
        return False
    pPr = elem.find(w("pPr"))
    if pPr is None:
        return False
    return pPr.find(w("pageBreakBefore")) is not None


def replace_toc_block(body: ET.Element, toc_block: ET.Element, toc_entries: list[TocEntry]) -> None:
    toc_paragraphs = [make_toc_paragraph(entry) for entry in toc_entries]
    # Collect prefix content that sits before the TOC field inside an SDT
    prefix: list[ET.Element] = []
    if toc_block.tag == w("sdt"):
        sdt_content = toc_block.find("w:sdtContent", NS)
        if sdt_content is not None:
            for child in list(sdt_content):
                if contains_toc_field(child):
                    break
                prefix.append(deepcopy(child))
    # Remove the entire TOC block from body, replace with plain paragraphs.
    # Also clean up any adjacent PageBreak paragraphs (backward compat with
    # old md_to_js.py output) and convert to pageBreakBefore.
    children = list(body)
    if toc_block not in children:
        raise ValueError("TOC block not found in body children")
    index = children.index(toc_block)

    # Check for PageBreak paragraphs adjacent to the TOC block
    need_pagebreak = False
    remove_indices: list[int] = []
    if index > 0 and _is_pagebreak_paragraph(children[index - 1]):
        remove_indices.append(index - 1)
    if index + 1 < len(children) and _is_pagebreak_paragraph(children[index + 1]):
        remove_indices.append(index + 1)
        need_pagebreak = True

    # Remove: TOC block + adjacent PageBreak paragraphs (reverse order to preserve indices)
    for ri in sorted([index] + remove_indices, reverse=True):
        body.remove(children[ri])

    # Insert TOC paragraphs at the original TOC position
    insert_at = index - sum(1 for ri in remove_indices if ri < index)
    for offset, paragraph in enumerate(prefix + toc_paragraphs):
        body.insert(insert_at + offset, paragraph)

    # If the TOC was followed by a PageBreak, add pageBreakBefore to the
    # first content paragraph after the TOC entries (if it doesn't have one)
    if need_pagebreak:
        first_after = insert_at + len(prefix) + len(toc_paragraphs)
        if first_after < len(list(body)):
            next_elem = list(body)[first_after]
            if next_elem.tag == w("p") and not _has_pagebreak_before(next_elem):
                pPr = next_elem.find(w("pPr"))
                if pPr is None:
                    pPr = ET.Element(w("pPr"))
                    next_elem.insert(0, pPr)
                ET.SubElement(pPr, w("pageBreakBefore"))


def rewrite_docx_zip(input_path: Path, output_path: Path, replacements: dict[bytes, bytes]) -> None:
    """Rewrite a docx zip, replacing specified file contents.

    replacements: mapping from zip entry name (e.g. b"word/document.xml") to new bytes.
    """
    temp_path = output_path.with_name(f"{output_path.name}.tmp")
    with zipfile.ZipFile(input_path, "r") as source, zipfile.ZipFile(temp_path, "w") as target:
        for info in source.infolist():
            payload = replacements.get(info.filename.encode(), source.read(info.filename))
            copied = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
            copied.compress_type = info.compress_type
            copied.comment = info.comment
            copied.create_system = info.create_system
            copied.external_attr = info.external_attr
            copied.internal_attr = info.internal_attr
            copied.flag_bits = info.flag_bits
            target.writestr(copied, payload)
    shutil.move(str(temp_path), str(output_path))


def inject_toc_styles(styles_xml: bytes, max_level: int) -> tuple[bytes, int]:
    """Ensure TOC1..TOC<n> paragraph styles exist in styles.xml.

    The docx npm library does not emit TOC style definitions, but
    render_toc_static.py references them (e.g. TOC1, TOC2).  Word flags
    the missing styles as \"节和标题\" repair errors.

    This function parses styles.xml, checks for missing TOC styles,
    and injects minimal definitions for any that are absent.
    """
    # Capture original XML declaration and namespace declarations
    # before parsing to restore them after ET.tostring().
    styles_str = styles_xml.decode("utf-8")
    orig_decl = styles_str[: styles_str.find("?>") + 2] if styles_str.startswith("<?xml") else ""
    root_open = styles_str.find("<w:styles")
    root_close = styles_str.find(">", root_open)
    orig_ns = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', styles_str[root_open:root_close]))

    ET.register_namespace("w", W_NS)
    root = ET.fromstring(styles_xml)
    existing: set[str] = set()
    for style_el in root.iter(w("style")):
        sid = style_el.get(w("styleId"), "")
        if re.match(r"^TOC\d+$", sid):
            existing.add(sid)

    injected = 0
    for lvl in range(1, max_level + 1):
        sid = f"TOC{lvl}"
        if sid in existing:
            continue
        # Minimal TOC style definition based on Normal
        style = ET.SubElement(root, w("style"))
        style.set(w("type"), "paragraph")
        style.set(w("styleId"), sid)
        name = ET.SubElement(style, w("name"))
        name.set(w("val"), f"TOC {lvl}")
        based = ET.SubElement(style, w("basedOn"))
        based.set(w("val"), "Normal")
        # Add indent for sub-levels
        if lvl > 1:
            indent_val = 360 * lvl
            p_pr = ET.SubElement(style, w("pPr"))
            indent = ET.SubElement(p_pr, w("ind"))
            indent.set(w("left"), str(indent_val))
        injected += 1

    result = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    if injected == 0:
        return (result, injected)

    # Restore original XML declaration and missing namespace declarations
    result_str = result.decode("utf-8")
    if orig_decl:
        et_decl_end = result_str.find("?>") + 2
        if et_decl_end > 1:
            result_str = orig_decl + result_str[et_decl_end:]
    # Inject missing namespace declarations on <w:styles>
    styles_open = result_str.find("<w:styles ")
    styles_close = result_str.find(">", styles_open)
    if styles_open >= 0 and styles_close > styles_open:
        existing_ns = result_str[styles_open:styles_close]
        for prefix, uri in orig_ns.items():
            if f'xmlns:{prefix}="' not in existing_ns:
                existing_ns += f' xmlns:{prefix}="{uri}"'
        result_str = result_str[:styles_open] + existing_ns + result_str[styles_close:]
        result = result_str.encode("utf-8")

    return (result, injected)


def fix_table_properties(body: ET.Element) -> int:
    """Fix tables produced by docx npm lib that cause Word repair errors.

    The docx npm library omits several elements that Word expects:
    1. <w:tblStyle w:val="TableGrid"/> — Word's default table style
    2. <w:tblLook/> — table formatting properties
    3. <w:tcW> on each cell — explicit cell widths matching gridCol
    4. Invalid <w:tblW type=auto w=100> — corrected to type=pct w=5000
    5. gridCol sum exceeding available content width — clamped
    """
    fixed = 0

    # Determine available content width from sectPr margins
    PAGE_WIDTH = 11906  # default A4 twips (docx npm default)
    margin_left = margin_right = 1440  # default md_to_js margins
    sect_pr = body.find(w("sectPr"))
    if sect_pr is not None:
        pg_sz = sect_pr.find(w("pgSz"))
        if pg_sz is not None:
            pw = get_w_attr(pg_sz, "w")
            if pw.isdigit():
                PAGE_WIDTH = int(pw)
        pg_mar = sect_pr.find(w("pgMar"))
        if pg_mar is not None:
            ml = get_w_attr(pg_mar, "left")
            mr = get_w_attr(pg_mar, "right")
            if ml.isdigit():
                margin_left = int(ml)
            if mr.isdigit():
                margin_right = int(mr)
    available = PAGE_WIDTH - margin_left - margin_right

    for tbl in body.iter(w("tbl")):
        tbl_pr = tbl.find(w("tblPr"))
        if tbl_pr is None:
            tbl_pr = ET.Element(w("tblPr"))
            tbl.insert(0, tbl_pr)

        # Fix 1: Add w:tblStyle referencing TableGrid
        if tbl_pr.find(w("tblStyle")) is None:
            tbl_style = ET.Element(w("tblStyle"))
            set_w_attr(tbl_style, "val", "TableGrid")
            tbl_w = tbl_pr.find(w("tblW"))
            if tbl_w is not None:
                idx = list(tbl_pr).index(tbl_w)
                tbl_pr.insert(idx, tbl_style)
            else:
                tbl_pr.insert(0, tbl_style)
            fixed += 1

        # Fix 2: Add w:tblLook if missing
        if tbl_pr.find(w("tblLook")) is None:
            tbl_look = ET.Element(w("tblLook"))
            set_w_attr(tbl_look, "firstRow", "1")
            set_w_attr(tbl_look, "lastRow", "0")
            set_w_attr(tbl_look, "firstColumn", "0")
            set_w_attr(tbl_look, "lastColumn", "0")
            set_w_attr(tbl_look, "noHBand", "0")
            set_w_attr(tbl_look, "noVBand", "1")
            tbl_pr.append(tbl_look)
            fixed += 1

        # Fix 3: Correct invalid tblW type=auto w=100 -> type=pct w=5000
        tbl_w = tbl_pr.find(w("tblW"))
        if tbl_w is not None:
            tw_type = get_w_attr(tbl_w, "type")
            tw_val = get_w_attr(tbl_w, "w")
            if tw_type == "auto" and tw_val not in ("0", ""):
                set_w_attr(tbl_w, "type", "pct")
                set_w_attr(tbl_w, "w", "5000")
                fixed += 1

        # Fix 4: Clamp gridCol sum and add tcW to each cell
        tbl_grid = tbl.find(w("tblGrid"))
        if tbl_grid is not None:
            cols = tbl_grid.findall(w("gridCol"))
            if cols:
                grid_widths = [int(c.get(w("w"), "0")) for c in cols]
                total = sum(grid_widths)
                if total > available and total > 0:
                    scale = available / total
                    grid_widths = [max(int(w * scale), 100) for w in grid_widths]
                    for c, w_val in zip(cols, grid_widths):
                        set_w_attr(c, "w", str(w_val))
                    fixed += 1
                # Add tcW to each cell from gridCol widths
                for row in tbl.iter(w("tr")):
                    cells = row.findall(w("tc"))
                    for ci, cell in enumerate(cells):
                        if ci >= len(grid_widths):
                            continue
                        tc_pr = cell.find(w("tcPr"))
                        if tc_pr is None:
                            tc_pr = ET.Element(w("tcPr"))
                            cell.insert(0, tc_pr)
                        if tc_pr.find(w("tcW")) is None:
                            tc_w = ET.Element(w("tcW"))
                            set_w_attr(tc_w, "w", str(grid_widths[ci]))
                            set_w_attr(tc_w, "type", "dxa")
                            tc_pr.insert(0, tc_w)
                            fixed += 1

    return fixed


def render_static_toc(input_path: Path, output_path: Path) -> tuple[int, int, int, int, int]:
    with zipfile.ZipFile(input_path, "r") as archive:
        if "word/document.xml" not in archive.namelist():
            raise ValueError("Invalid .docx: missing word/document.xml")
        document_xml = archive.read("word/document.xml")
        styles_xml = archive.read("word/styles.xml") if "word/styles.xml" in archive.namelist() else b""
    # Capture ALL original namespace declarations from the document root
    # before parsing, because ET.tostring() drops any that are not actively
    # used by elements — but Word requires them for mc:Ignorable et al.
    doc_str = document_xml.decode("utf-8")
    orig_ns = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', doc_str[: doc_str.find(">", doc_str.find("<w:document"))]))
    # Also capture the original XML declaration to preserve standalone="yes"
    orig_decl = doc_str[: doc_str.find("?>") + 2] if doc_str.startswith("<?xml") else ""

    ET.register_namespace("w", W_NS)
    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("Invalid document.xml: missing w:body")
    toc_block = find_toc_block(body)
    if toc_block is None:
        raise ValueError("TOC field not found in document body")
    start_level, end_level = parse_heading_range(extract_toc_instruction(toc_block))
    entries, added_bookmarks = collect_toc_entries(root, body, toc_block, start_level, end_level)
    if not entries:
        raise ValueError(f"No headings found for TOC range {start_level}-{end_level}")
    replace_toc_block(body, toc_block, entries)
    table_fixes = fix_table_properties(body)
    updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Restore any original namespace declarations that ET.tostring dropped.
    # docx-js declares ~32 namespaces; ET preserves only those actively used.
    updated_str = updated_xml.decode("utf-8")
    # Restore the original XML declaration (standalone="yes" etc.)
    if orig_decl:
        et_decl_end = updated_str.find("?>") + 2
        if et_decl_end > 1:
            updated_str = orig_decl + updated_str[et_decl_end:]
    doc_open = updated_str.find("<w:document ")
    doc_close = updated_str.find(">", doc_open)
    if doc_open >= 0 and doc_close > doc_open:
        existing = updated_str[doc_open:doc_close]
        for prefix, uri in orig_ns.items():
            if f'xmlns:{prefix}="' not in existing:
                existing += f' xmlns:{prefix}="{uri}"'
        updated_str = updated_str[:doc_open] + existing + updated_str[doc_close:]
        updated_xml = updated_str.encode("utf-8")
    # Inject missing TOC style definitions into styles.xml
    toc_style_fixes = 0
    if styles_xml:
        styles_xml, toc_style_fixes = inject_toc_styles(styles_xml, end_level)
    replacements: dict[bytes, bytes] = {b"word/document.xml": updated_xml}
    if styles_xml and toc_style_fixes:
        replacements[b"word/styles.xml"] = styles_xml
    rewrite_docx_zip(input_path, output_path, replacements)
    return (len(entries), added_bookmarks, start_level, end_level, table_fixes, toc_style_fixes)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render static TOC without Win COM; output has clickable entries and no page numbers."
    )
    parser.add_argument("input", help="Path to input .docx file")
    parser.add_argument("-o", "--output", help="Optional output path; default is in-place")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve() if args.output else input_path
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    if input_path.suffix.lower() != ".docx":
        print("Error: input file must be .docx", file=sys.stderr)
        sys.exit(1)
    if not output_path.parent.exists():
        print(f"Error: output directory does not exist: {output_path.parent}", file=sys.stderr)
        sys.exit(1)
    try:
        count, bookmarks_added, start_level, end_level, table_fixes, toc_style_fixes = render_static_toc(input_path, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    msg = (
        "OK: static TOC rendered "
        f"(entries={count}, levels={start_level}-{end_level}, "
        f"bookmarks_added={bookmarks_added})"
    )
    if table_fixes:
        msg += f", table_fixes={table_fixes}"
    if toc_style_fixes:
        msg += f", toc_style_injected={toc_style_fixes}"
    msg += f" -> {output_path}"
    print(msg)


if __name__ == "__main__":
    main()
