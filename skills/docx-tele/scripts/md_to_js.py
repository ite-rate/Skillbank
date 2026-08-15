#!/usr/bin/env python3
"""
md_to_js.py - 将 Markdown 文件转换为 docx-js 的 JS 文件
用法: python md_to_js.py --input <input.md> --output <output.js> [--docx-output <output.docx>] [--font <font>] [--font-size <N>] [--indent <twips>] [--line-spacing <N>] [--margin-* <twips>]
生成后执行: node <output.js>
"""
import re
import argparse
from pathlib import Path


# ========== Markdown 解析 ==========

def parse_inline(text):
    """
    解析行内格式，返回 runs 列表。
    支持: **bold**, *italic*, ***bold italic***, [text](url), `code`
    链接文字内嵌格式: [**bold text**](url), [*italic text*](url), [***bold italic***](url)
    外包裹格式: **[text](url)**, *[text](url)*, ***[text](url)***
    """
    runs = []
    # 阶段1：匹配块级元素
    # - 外包裹链接: **[text](url)** / *[text](url)* / ***[text](url)***
    # - 内嵌格式链接: [**text**](url) / [*text*](url) / [***text***](url)
    # - 普通链接: [text](url)
    # - 加粗斜体/加粗/斜体/代码
    
    # 外包裹链接模式：(*|**|***) [text](url) \1
    # 注意：外包裹需放在普通 bold/italic 之前，避免被单独匹配
    outer_link_pat = re.compile(
        r'\*\*\*(\[[^\]]+?\]\([^\)]+?\))\*\*\*'   # ***[text](url)***
        r'|\*\*(\[[^\]]+?\]\([^\)]+?\))\*\*'       # **[text](url)**
        r'|\*(\[[^\]]+?\]\([^\)]+?\))\*'           # *[text](url)*
    )
    
    # 内嵌格式链接模式：[ (*|**|***)text\1 ](url)
    inner_fmt_link_pat = re.compile(
        r'\[(\*\*\*.+?\*\*\*)\]\((.+?)\)'          # [***text***](url)
        r'|\[(\*\*.+?\*\*)\]\((.+?)\)'             # [**text**](url)
        r'|\[(\*.+?\*)\]\((.+?)\)'                  # [*text*](url)
    )
    
    # 普通链接模式
    link_pat = re.compile(r'\[([^\]]+?)\]\((.+?)\)')
    
    # 行内格式模式（不含链接）
    inline_pat = re.compile(
        r'(\*\*\*(.+?)\*\*\*)'    # ***bold italic***
        r'|(\*\*(.+?)\*\*)'       # **bold**
        r'|(\*(.+?)\*)'           # *italic*
        r'|(`(.+?)`)'             # `code`
    )
    
    pos = 0
    
    # 使用统一的正则匹配所有可能模式
    # 按优先级：外包裹链接 > 内嵌格式链接 > 普通链接 > 加粗斜体 > 加粗 > 斜体 > 代码
    master_pat = re.compile(
        r'(?P<outer_bi>\*\*\*\[[^\]]+?\]\([^\)]+?\)\*\*\*)'
        r'|(?P<outer_b>\*\*\[[^\]]+?\]\([^\)]+?\)\*\*)'
        r'|(?P<outer_i>\*\[[^\]]+?\]\([^\)]+?\)\*)'
        r'|(?P<inner_bi>\[\*\*\*.+?\*\*\*\]\(.+?\))'
        r'|(?P<inner_b>\[\*\*.+?\*\*\]\(.+?\))'
        r'|(?P<inner_i>\[\*.+?\*\]\(.+?\))'
        r'|(?P<link>\[[^\]]+?\]\([^\)]+?\))'
        r'|(?P<bi>\*\*\*.+?\*\*\*)'
        r'|(?P<b>\*\*.+?\*\*)'
        r'|(?P<i>\*.+?\*)'
        r'|(?P<code>`.+?`)'
    )
    
    for m in master_pat.finditer(text):
        start = m.start()
        if start > pos:
            runs.append({"text": text[pos:start]})
        
        if m.group("outer_bi"):
            # ***[text](url)*** → bold+italic+link
            inner = re.match(r'\*\*\*\[([^\]]+?)\]\((.+?)\)\*\*\*', m.group("outer_bi"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "bold": True, "italic": True})
        elif m.group("outer_b"):
            # **[text](url)** → bold+link
            inner = re.match(r'\*\*\[([^\]]+?)\]\((.+?)\)\*\*', m.group("outer_b"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "bold": True})
        elif m.group("outer_i"):
            # *[text](url)* → italic+link
            inner = re.match(r'\*\[([^\]]+?)\]\((.+?)\)\*', m.group("outer_i"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "italic": True})
        elif m.group("inner_bi"):
            # [***text***](url) → bold+italic+link
            inner = re.match(r'\[\*\*\*(.+?)\*\*\*\]\((.+?)\)', m.group("inner_bi"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "bold": True, "italic": True})
        elif m.group("inner_b"):
            # [**text**](url) → bold+link
            inner = re.match(r'\[\*\*(.+?)\*\*\]\((.+?)\)', m.group("inner_b"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "bold": True})
        elif m.group("inner_i"):
            # [*text*](url) → italic+link
            inner = re.match(r'\[\*(.+?)\*\]\((.+?)\)', m.group("inner_i"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2), "italic": True})
        elif m.group("link"):
            # [text](url) → plain link
            inner = re.match(r'\[([^\]]+?)\]\((.+?)\)', m.group("link"))
            runs.append({"type": "link", "text": inner.group(1), "url": inner.group(2)})
        elif m.group("bi"):
            content = re.match(r'\*\*\*(.+?)\*\*\*', m.group("bi")).group(1)
            runs.append({"text": content, "bold": True, "italic": True})
        elif m.group("b"):
            content = re.match(r'\*\*(.+?)\*\*', m.group("b")).group(1)
            runs.append({"text": content, "bold": True})
        elif m.group("i"):
            content = re.match(r'\*(.+?)\*', m.group("i")).group(1)
            runs.append({"text": content, "italic": True})
        elif m.group("code"):
            content = re.match(r'`(.+?)`', m.group("code")).group(1)
            runs.append({"text": content, "font": "Consolas"})
        
        pos = m.end()
    
    if pos < len(text):
        runs.append({"text": text[pos:]})
    
    # 合并相邻纯文本 run
    merged = []
    for r in runs:
        if (merged and "type" not in r and "bold" not in r 
                and "italic" not in r and "font" not in r
                and "type" not in merged[-1] and "bold" not in merged[-1]
                and "italic" not in merged[-1] and "font" not in merged[-1]):
            merged[-1]["text"] += r["text"]
        else:
            merged.append(r)
    
    return merged


def parse_table_rows(lines):
    """解析 Markdown 表格行"""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        # 去首尾 |
        line = line[1:-1] if line.endswith('|') else line[1:]
        cells = [c.strip() for c in line.split('|')]
        # 跳过分隔行（---|---|---）
        if all(re.match(r'^[-:]+$', c) for c in cells):
            continue
        rows.append(cells)
    return rows


def parse_markdown(md_text):
    """
    解析 Markdown 文本，返回结构化内容列表。
    每个元素是 {"type": ..., ...}
    """
    blocks = []
    lines = md_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 空行跳过
        if not stripped:
            i += 1
            continue
        
        # 目录标记 [TOC]
        if stripped == '[TOC]':
            blocks.append({"type": "toc"})
            i += 1
            continue

        # 水平线 --- / *** / ___ 直接跳过
        if re.match(r'^-{3,}$|^\*{3,}$|^_{3,}$', stripped):
            i += 1
            continue

        # 标题
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if heading_match:
            level = min(len(heading_match.group(1)), 4)
            text = heading_match.group(2)
            runs = parse_inline(text)
            blocks.append({"type": "heading", "level": level, "runs": runs})
            i += 1
            continue
        
        # 无序列表
        if re.match(r'^[-*+]\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^[-*+]\s+', lines[i].strip()):
                item_text = re.sub(r'^[-*+]\s+', '', lines[i].strip())
                items.append({"runs": parse_inline(item_text)})
                i += 1
            blocks.append({"type": "bullet_list", "items": items})
            continue
        
        # 有序列表
        if re.match(r'^\d+\.\s+', stripped):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s+', lines[i].strip()):
                item_text = re.sub(r'^\d+\.\s+', '', lines[i].strip())
                items.append({"runs": parse_inline(item_text)})
                i += 1
            blocks.append({"type": "numbered_list", "items": items})
            continue
        
        # 表格
        if stripped.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table_rows(table_lines)
            if rows:
                blocks.append({"type": "table", "rows": rows})
            continue
        
        # 图片
        img_match = re.match(r'^!\[(.*?)\]\((.+?)\)\s*$', stripped)
        if img_match:
            alt = img_match.group(1)
            path = img_match.group(2)
            blocks.append({"type": "image", "alt": alt, "path": path})
            i += 1
            continue

        # 围栏代码块 ```
        if re.match(r'^`{3,}', stripped):
            info = re.sub(r'^`{3,}\s*', '', stripped)  # 语言标识，忽略
            code_lines = []
            i += 1
            while i < len(lines):
                if re.match(r'^`{3,}\s*$', lines[i].strip()):
                    i += 1  # 跳过闭合 ```
                    break
                code_lines.append(lines[i])
                i += 1
            blocks.append({"type": "code_block", "lines": code_lines, "info": info})
            continue

        # 普通段落（可能跨行，直到空行或下一个块级元素）
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                break
            if (re.match(r'^#{1,6}\s', l) or re.match(r'^[-*+]\s', l)
                    or re.match(r'^\d+\.\s', l) or l.startswith('|')
                    or re.match(r'^!\[', l)
                    or re.match(r'^`{3,}', l)):
                break
            para_lines.append(l)
            i += 1
        
        if para_lines:
            text = ' '.join(para_lines)
            runs = parse_inline(text)
            blocks.append({"type": "paragraph", "runs": runs})
    
    return blocks


# ========== JS 生成 ==========

def escape_js_string(s):
    """转义 JS 模板字符串中的特殊字符，保留正文中的中文弯引号"""
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')


def runs_to_js(runs, indent="        "):
    """将 runs 列表转为 JS TextRun/ExternalHyperlink 代码"""
    parts = []
    for r in runs:
        if r.get("type") == "link":
            # 链接子 TextRun 的属性
            child_props = [f'text: `{escape_js_string(r["text"])}`']
            if r.get("bold"):
                child_props.append("bold: true")
            if r.get("italic"):
                child_props.append("italics: true")
            child_props.append('style: "Hyperlink"')
            child_props_str = ", ".join(child_props)
            link_js = (
                f'new ExternalHyperlink({{\n'
                f'{indent}  children: [new TextRun({{ {child_props_str} }})],\n'
                f'{indent}  link: "{r["url"]}"\n'
                f'{indent}}})'
            )
            parts.append(link_js)
        else:
            props = [f'text: `{escape_js_string(r["text"])}`']
            if r.get("bold"):
                props.append("bold: true")
            if r.get("italic"):
                props.append("italics: true")
            if r.get("font"):
                props.append(f'font: "{r["font"]}"')
            props_str = ", ".join(props)
            parts.append(f'new TextRun({{ {props_str} }})')
    
    if len(parts) == 1:
        return parts[0]
    return ",\n    ".join([f"{indent}{p}" for p in parts])


def heading_runs_to_js(runs, heading_level, font_size, font_name, indent="        ", color="000000"):
    """将 heading runs 列表转为 JS TextRun/ExternalHyperlink 代码，自动注入标题级属性"""
    heading_spacing = {1: (240, 240), 2: (180, 180), 3: (120, 120)}.get(heading_level, (120, 120))
    parts = []
    for r in runs:
        if r.get("type") == "link":
            child_props = [f'text: `{escape_js_string(r["text"])}`']
            if r.get("bold"):
                child_props.append("bold: true")
            if r.get("italic"):
                child_props.append("italics: true")
            child_props.append('style: "Hyperlink"')
            child_props_str = ", ".join(child_props)
            link_js = (
                f'new ExternalHyperlink({{\n'
                f'{indent}  children: [new TextRun({{ {child_props_str} }})],\n'
                f'{indent}  link: "{r["url"]}"\n'
                f'{indent}}})'
            )
            parts.append(link_js)
        else:
            props = [
                f'text: `{escape_js_string(r["text"])}`',
                "bold: true",
                f'size: {font_size}',
                f'color: "{color}"',
                f'font: "{font_name}"',
            ]
            if r.get("italic"):
                props.append("italics: true")
            if r.get("font"):
                props[-1] = f'font: "{r["font"]}"'
            props_str = ", ".join(props)
            parts.append(f'new TextRun({{ {props_str} }})')

    if len(parts) == 1:
        return parts[0]
    return ",\n    ".join([f"{indent}{p}" for p in parts])


def generate_js(blocks, output_path, font="仿宋_GB2312", input_dir=None,
                font_size=24, font_size_h1=0, font_size_h2=0, font_size_h3=0,
                indent=0, line_spacing=0,
                margin_top=1440, margin_right=1440, margin_bottom=1440, margin_left=1440,
                heading_color="1A5276", subtitle="", tagline="", header="",
                cover=False, no_header=False, footer="", no_footer=False):
    """生成完整的 docx-js JS 文件"""

    # 图片路径基准目录：Markdown 文件所在目录
    if input_dir is None:
        input_dir = Path.cwd()

    # 标题字号：未指定时按比例自动计算
    if font_size_h1 <= 0:
        font_size_h1 = round(font_size * 1.33)
    if font_size_h2 <= 0:
        font_size_h2 = round(font_size * 1.17)
    if font_size_h3 <= 0:
        font_size_h3 = round(font_size * 1.08)

    font_name = font.replace('"', '\\"')

    # 为每个列表 block 分配唯一 reference id
    bullet_idx = 0
    num_idx = 0
    for block in blocks:
        if block["type"] == "bullet_list":
            block["_ref"] = f"bullet-list-{bullet_idx}"
            bullet_idx += 1
        elif block["type"] == "numbered_list":
            block["_ref"] = f"num-list-{num_idx}"
            num_idx += 1
    
    # 动态生成 numbering config
    numbering_parts = []
    for i in range(bullet_idx):
        numbering_parts.append(
            '      { reference: "bullet-list-' + str(i) + '",\n'
            '        levels: [{ level: 0, format: LevelFormat.BULLET, text: "\\u2022", alignment: AlignmentType.LEFT,\n'
            '          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }'
        )
    for i in range(num_idx):
        numbering_parts.append(
            '      { reference: "num-list-' + str(i) + '",\n'
            '        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,\n'
            '          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }'
        )
    numbering_str = ",\n".join(numbering_parts)
    
    children_parts = []
    
    # 检测文档是否包含 TOC，用于自动分页
    has_toc = any(b["type"] == "toc" for b in blocks)
    # 文档标题（第一个 H1 纯文本），用于页眉默认值
    doc_title = ""
    for b in blocks:
        if b["type"] == "heading" and b["level"] == 1:
            doc_title = escape_js_string("".join(r["text"] for r in b["runs"]))
            break
    if no_header:
        header_text = ""
    else:
        header_text = escape_js_string(header) if header else doc_title
    footer_text = escape_js_string(footer)
    first_h1_seen = False
    page_break_next = False

    for block in blocks:
        btype = block["type"]
        
        if btype == "heading":
            level = block["level"]
            heading_size = {1: font_size_h1, 2: font_size_h2, 3: font_size_h3}.get(level, font_size_h3)
            heading_spacing_before, heading_spacing_after = {1: (240, 240), 2: (180, 180), 3: (120, 120)}.get(level, (120, 120))
            outline_lvl = level - 1
            runs_js = heading_runs_to_js(block["runs"], level, heading_size, font_name, color=heading_color)
            pbb = "        pageBreakBefore: true,\n" if page_break_next else ""
            page_break_next = False
            if level == 1 and not first_h1_seen:
                first_h1_seen = True
                if cover:
                    # Title page: large, colored, with generous top spacing.
                    title_runs_js = heading_runs_to_js(block["runs"], level, 72, font_name, color=heading_color)
                    children_parts.append(
                        f'      new Paragraph({{\n'
                        f'{pbb}'
                        f'        heading: HeadingLevel.HEADING_{level},\n'
                        f'        outlineLevel: {outline_lvl},\n'
                        f'        alignment: AlignmentType.CENTER,\n'
                        f'        spacing: {{ before: 3600, after: 200 }},\n'
                        f'        children: [{title_runs_js}]\n'
                        f'      }})'
                    )
                    # Subtitle (optional)
                    if subtitle:
                        sub_esc = escape_js_string(subtitle)
                        children_parts.append(
                            f'      new Paragraph({{\n'
                            f'        alignment: AlignmentType.CENTER,\n'
                            f'        spacing: {{ after: 100 }},\n'
                            f'        children: [new TextRun({{ text: `{sub_esc}`, size: 36, color: "2E86C1" }})]\n'
                            f'      }})'
                        )
                    # Tagline (optional)
                    if tagline:
                        tag_esc = escape_js_string(tagline)
                        children_parts.append(
                            f'      new Paragraph({{\n'
                            f'        alignment: AlignmentType.CENTER,\n'
                            f'        children: [new TextRun({{ text: `{tag_esc}`, italics: true, size: 24, color: "5D6D7E" }})]\n'
                            f'      }})'
                        )
                    # Date (auto-generated)
                    from datetime import datetime
                    date_str = datetime.now().strftime("%Y年%m月")
                    children_parts.append(
                        f'      new Paragraph({{\n'
                        f'        spacing: {{ before: 2400 }},\n'
                        f'        alignment: AlignmentType.CENTER,\n'
                        f'        children: [new TextRun({{ text: `{date_str}`, size: 22, color: "888888" }})]\n'
                        f'      }})'
                    )
                    if not has_toc:
                        page_break_next = True
                else:
                    children_parts.append(
                        f'      new Paragraph({{\n'
                        f'{pbb}'
                        f'        heading: HeadingLevel.HEADING_{level},\n'
                        f'        outlineLevel: {outline_lvl},\n'
                        f'        spacing: {{ before: {heading_spacing_before}, after: {heading_spacing_after} }},\n'
                        f'        children: [{runs_js}]\n'
                        f'      }})'
                    )
            else:
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'        heading: HeadingLevel.HEADING_{level},\n'
                    f'        outlineLevel: {outline_lvl},\n'
                    f'        spacing: {{ before: {heading_spacing_before}, after: {heading_spacing_after} }},\n'
                    f'        children: [{runs_js}]\n'
                    f'      }})'
                )
        
        elif btype == "toc":
            # Invisible page break: title on page 1, TOC on page 2
            children_parts.append(
                '      new Paragraph({ pageBreakBefore: true, spacing: { after: 0 }, children: [] })'
            )
            children_parts.append(
                '      new TableOfContents("目录", {\n'
                '        hyperlink: true,\n'
                '        headingStyleRange: "1-3",\n'
                '      })'
            )
            page_break_next = True
        
        elif btype == "paragraph":
            runs = block["runs"]
            indent_str = f'        indent: {{ firstLine: {indent} }},\n' if indent else ""
            pbb = "        pageBreakBefore: true,\n" if page_break_next else ""
            page_break_next = False
            if len(runs) == 1 and not runs[0].get("bold") and not runs[0].get("italic") and not runs[0].get("font") and not runs[0].get("type"):
                # 简单段落
                text = escape_js_string(runs[0]["text"])
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'{indent_str}'
                    f'        children: [new TextRun(`{text}`)]\n'
                    f'      }})'
                )
            else:
                runs_js = runs_to_js(runs)
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'{indent_str}'
                    f'        children: [{runs_js}]\n'
                    f'      }})'
                )
        
        elif btype == "code_block":
            code_lines = block["lines"]
            code_size = font_size - 4  # slightly smaller than body
            pbb = "        pageBreakBefore: true,\n" if page_break_next else ""
            page_break_next = False
            for line in code_lines:
                text = escape_js_string(line.rstrip())
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'        spacing: {{ before: 0, after: 0 }},\n'
                    f'        children: [new TextRun({{ text: `{text}`, font: "Consolas", size: {code_size} }})]\n'
                    f'      }})'
                )
                pbb = ""  # only first line gets pageBreakBefore

        elif btype == "bullet_list":
            ref = block["_ref"]
            for idx, item in enumerate(block["items"]):
                runs_js = runs_to_js(item["runs"])
                pbb = "        pageBreakBefore: true,\n" if (page_break_next and idx == 0) else ""
                if idx == 0:
                    page_break_next = False
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'        numbering: {{ reference: "{ref}", level: 0 }},\n'
                    f'        children: [{runs_js}]\n'
                    f'      }})'
                )
        
        elif btype == "numbered_list":
            ref = block["_ref"]
            for idx, item in enumerate(block["items"]):
                runs_js = runs_to_js(item["runs"])
                pbb = "        pageBreakBefore: true,\n" if (page_break_next and idx == 0) else ""
                if idx == 0:
                    page_break_next = False
                children_parts.append(
                    f'      new Paragraph({{\n'
                    f'{pbb}'
                    f'        numbering: {{ reference: "{ref}", level: 0 }},\n'
                    f'        children: [{runs_js}]\n'
                    f'      }})'
                )
        
        elif btype == "table":
            rows = block["rows"]
            if not rows:
                continue

            # pageBreakBefore works on Paragraph only, not Table.
            # Insert an invisible empty paragraph to carry the page break.
            if page_break_next:
                children_parts.append(
                    '      new Paragraph({ pageBreakBefore: true, spacing: { after: 0 }, children: [] })'
                )
                page_break_next = False

            # 表头
            num_cols = max(len(r) for r in rows)
            col_width = 9026 // num_cols
            first_row = rows[0]
            header_cells = []
            for cell_text in first_row:
                runs = parse_inline(cell_text)
                cell_width_str = f'            width: {{ size: {col_width}, type: WidthType.DXA }},\n'
                if len(runs) == 1 and not runs[0].get("bold"):
                    header_cells.append(
                        f'          new TableCell({{\n'
                        f'{cell_width_str}'
                        f'            borders: cellBorders,\n'
                        f'            verticalAlign: VerticalAlign.CENTER,\n'
                        f'            shading: {{ fill: "D5E8F0", type: ShadingType.CLEAR }},\n'
                        f'            children: [new Paragraph({{ alignment: AlignmentType.CENTER, children: [new TextRun({{ text: `{escape_js_string(runs[0]["text"])}`, bold: true }})] }})]\n'
                        f'          }})'
                    )
                else:
                    runs_js = runs_to_js(runs, "            ")
                    header_cells.append(
                        f'          new TableCell({{\n'
                        f'{cell_width_str}'
                        f'            borders: cellBorders,\n'
                        f'            verticalAlign: VerticalAlign.CENTER,\n'
                        f'            shading: {{ fill: "D5E8F0", type: ShadingType.CLEAR }},\n'
                        f'            children: [new Paragraph({{ alignment: AlignmentType.CENTER, children: [{runs_js}] }})]\n'
                        f'          }})'
                    )
            
            # 数据行
            data_rows_js = []
            # 先加表头行
            header_cells_js = ",\n".join(header_cells)
            data_rows_js.append(
                f'        new TableRow({{\n'
                f'          children: [\n'
                f'{header_cells_js}\n'
                f'          ]\n'
                f'        }})'
            )
            
            for row in rows[1:]:
                cells_js = []
                for cell_text in row:
                    runs = parse_inline(cell_text)
                    cell_width_str = f'            width: {{ size: {col_width}, type: WidthType.DXA }},\n'
                    if len(runs) == 1 and not runs[0].get("bold") and not runs[0].get("italic"):
                        cells_js.append(
                            f'          new TableCell({{\n'
                            f'{cell_width_str}'
                            f'            borders: cellBorders,\n'
                            f'            verticalAlign: VerticalAlign.CENTER,\n'
                            f'            children: [new Paragraph({{ alignment: AlignmentType.CENTER, children: [new TextRun(`{escape_js_string(runs[0]["text"])}`)] }})]\n'
                            f'          }})'
                        )
                    else:
                        runs_js = runs_to_js(runs, "            ")
                        cells_js.append(
                            f'          new TableCell({{\n'
                            f'{cell_width_str}'
                            f'            borders: cellBorders,\n'
                            f'            verticalAlign: VerticalAlign.CENTER,\n'
                            f'            children: [new Paragraph({{ alignment: AlignmentType.CENTER, children: [{runs_js}] }})]\n'
                            f'          }})'
                        )
                cells_joined = ",\n".join(cells_js)
                data_rows_js.append(
                    f'        new TableRow({{\n'
                    f'          children: [\n'
                    f'{cells_joined}\n'
                    f'          ]\n'
                    f'        }})'
                )
            
            col_widths = ", ".join([str(col_width)] * num_cols)
            data_rows_joined = ",\n".join(data_rows_js)

            children_parts.append(
                f'      new Table({{\n'
                f'        width: {{ size: {col_width * num_cols}, type: WidthType.DXA }},\n'
                f'        columnWidths: [{col_widths}],\n'
                f'        alignment: AlignmentType.CENTER,\n'
                f'        rows: [\n'
                f'{data_rows_joined}\n'
                f'        ]\n'
                f'      }})'
            )
        
        elif btype == "image":
            alt = escape_js_string(block.get("alt", ""))
            img_path = Path(block["path"])
            if not img_path.is_absolute():
                img_path = (input_dir / img_path).resolve()
            ext = img_path.suffix.lstrip('.')
            if not ext:
                ext = "png"
            pbb = "        pageBreakBefore: true,\n" if page_break_next else ""
            page_break_next = False
            children_parts.append(
                f'      new Paragraph({{\n'
                f'{pbb}'
                f'        alignment: AlignmentType.CENTER,\n'
                f'        children: [new ImageRun({{\n'
                f'          type: "{ext}",\n'
                f'          data: fs.readFileSync("{str(img_path).replace(chr(92), "/")}"),\n'
                f'          transformation: {{ width: 400, height: 300 }},\n'
                f'          altText: {{ title: `{alt}`, description: `{alt}`, name: `{alt}` }}\n'
                f'        }})]\n'
                f'      }})'
            )
        

    
    children_str = ",\n".join(children_parts)
    
    # JS 模板
    default_doc = f'run: {{ font: "{font_name}", size: {font_size} }}'
    if line_spacing > 0:
        default_doc += f', paragraph: {{ spacing: {{ line: {line_spacing} }} }}'
    section_props = f'margin: {{ top: {margin_top}, right: {margin_right}, bottom: {margin_bottom}, left: {margin_left} }}'
    if header_text:
        header_section_js = (
            "    headers: {\n"
           f'      default: new Header({{ children: [new Paragraph({{ alignment: AlignmentType.RIGHT, children: [new TextRun({{ text: `{header_text}`, italics: true, size: 18, color: "999999"}})] }})] }})\n'
            "    },\n"
        )
    else:
        header_section_js = ""

    if footer_text:
        footer_js = (
            '      default: new Footer({ children: [new Paragraph({\n'
            '        alignment: AlignmentType.CENTER,\n'
           f'        children: [new TextRun({{ text: `{footer_text}`, size: 18, color: "999999" }})]\n'
            '      })] })\n'
        )
    else:
        footer_js = (
            '      default: new Footer({ children: [new Paragraph({\n'
            '        alignment: AlignmentType.CENTER,\n'
            '        children: [new TextRun({ text: `第 ` }), new TextRun({ children: [PageNumber.CURRENT] }), new TextRun({ text: ` 页` })]\n'
            '      })] })\n'
        )
    footer_section_js = "" if no_footer else "    footers: {\n" + footer_js + "    },\n"

    js_code = (
        "const _p = require('path').join(require('os').homedir(), '.local/share/TeleAgent/runtimes/node/lib/node_modules');\n"
        "module.paths.unshift(_p);\n"
        "const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,\n"
        "        ImageRun, Header, Footer, AlignmentType, LevelFormat, ExternalHyperlink,\n"
        "        HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,\n"
        "        VerticalAlign, TableOfContents } = require('docx');\n"
        "const fs = require('fs');\n"
        "\n"
        "const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: \"CCCCCC\" };\n"
        "const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };\n"
        "\n"
        "const doc = new Document({\n"
        "  styles: {\n"
       f'    default: {{ document: {{ {default_doc} }} }}\n'
        "  },\n"
        "  numbering: {\n"
        "    config: [\n"
        + numbering_str + "\n"
        "    ]\n"
        "  },\n"
        "  sections: [{\n"
        "    properties: {\n"
       f"      page: {{ {section_props} }}\n"
        "    },\n"
        + header_section_js +
        footer_section_js +
        "    children: [\n"
        + children_str + "\n"
        "    ]\n"
        "  }]\n"
        "});\n"
        "\n"
        "Packer.toBuffer(doc).then(buffer => fs.writeFileSync(\"" + str(output_path).replace("\\", "/") + "\", buffer));\n"
    )
    
    return js_code


# ========== 主流程 ==========

def main():
    parser = argparse.ArgumentParser(description="将 Markdown 转为 docx-js JS 文件")
    parser.add_argument("--input", required=True, help="输入 Markdown 文件路径")
    parser.add_argument("--output", required=True, help="输出 JS 文件路径")
    parser.add_argument("--docx-output", default="output.docx", help="JS 中输出的 docx 文件名")
    parser.add_argument("--font", default="仿宋_GB2312", help="文档默认字体 (默认: 仿宋_GB2312)")
    parser.add_argument("--font-size", type=int, default=24, help="正文字号 half-points (默认: 24=12pt)")
    parser.add_argument("--font-size-h1", type=int, default=0, help="H1 字号 (默认: font-size*1.33)")
    parser.add_argument("--font-size-h2", type=int, default=0, help="H2 字号 (默认: font-size*1.17)")
    parser.add_argument("--font-size-h3", type=int, default=0, help="H3 字号 (默认: font-size*1.08)")
    parser.add_argument("--indent", type=int, default=0, help="段落首行缩进 twips (中文两字符约480)")
    parser.add_argument("--line-spacing", type=int, default=0, help="行间距 (240=单倍, 360=1.5倍, 480=双倍, 0=不设)")
    parser.add_argument("--margin-top", type=int, default=1440, help="上边距 twips (默认: 1440=1inch)")
    parser.add_argument("--margin-right", type=int, default=1440, help="右边距 twips (默认: 1440)")
    parser.add_argument("--margin-bottom", type=int, default=1440, help="下边距 twips (默认: 1440)")
    parser.add_argument("--margin-left", type=int, default=1440, help="左边距 twips (默认: 1440)")
    parser.add_argument("--heading-color", default="1A5276", help="标题颜色 (默认: 1A5276=深蓝)")
    parser.add_argument("--subtitle", default="", help="封面副标题（可选）")
    parser.add_argument("--tagline", default="", help="封面标语行（可选）")
    parser.add_argument("--header", default="", help="页眉文字（可选；不传则使用第一个 H1）")
    parser.add_argument("--no-header", action="store_true", help="不生成页眉")
    parser.add_argument("--footer", default="", help="页脚文字（可选；不传则使用页码）")
    parser.add_argument("--no-footer", action="store_true", help="不生成页脚")
    parser.add_argument("--cover", action="store_true", help="将第一个 H1 生成为封面页")
    args = parser.parse_args()

    # 过滤占位符：如果智能体照抄了 <副标题> / 关键词 等占位文本，视为未传入
    def _is_placeholder(val):
        if not val:
            return True
        if val.startswith("<") and val.endswith(">"):
            return True
        if "副标题" in val or "关键词" in val:
            return True
        return False

    if _is_placeholder(args.subtitle):
        args.subtitle = ""
    if _is_placeholder(args.tagline):
        args.tagline = ""

    input_dir = Path(args.input).resolve().parent

    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    blocks = parse_markdown(md_text)
    js_code = generate_js(blocks, args.docx_output,
                          font=args.font, input_dir=input_dir,
                          font_size=args.font_size,
                          font_size_h1=args.font_size_h1,
                          font_size_h2=args.font_size_h2,
                          font_size_h3=args.font_size_h3,
                          indent=args.indent,
                          line_spacing=args.line_spacing,
                          margin_top=args.margin_top,
                          margin_right=args.margin_right,
                          margin_bottom=args.margin_bottom,
                          margin_left=args.margin_left,
                          heading_color=args.heading_color,
                          subtitle=args.subtitle,
                          tagline=args.tagline,
                          header=args.header,
                          cover=args.cover,
                          no_header=args.no_header,
                          footer=args.footer,
                          no_footer=args.no_footer)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(js_code)

    print(f"JS 文件已生成: {args.output}")
    print(f"执行命令: node {args.output}")


if __name__ == "__main__":
    main()
