#!/usr/bin/env python3
"""
CLI entry point for rendering diagrams to PNG/SVG.
Replaces Node.js bin/smart-draw.js + bin/render.js + lib/render/*.js + lib/cli/*.js

Usage:
    python3 render.py <drawio|excalidraw> -f <file> -o <output_path> [--svg] [--no-source]
"""

import argparse
import json
import platform
import sys
from contextlib import contextmanager
from pathlib import Path

# Allow importing process_code from same directory
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _get_processors():
    """Lazy import of processors from process_code.py."""
    from process_code import drawio_processor, excalidraw_processor
    return drawio_processor, excalidraw_processor


# ==================== Font Configuration ====================

def get_font_family():
    system = platform.system()
    if system == 'Windows':
        return '"Microsoft YaHei", SimSun, "Noto Sans CJK SC", sans-serif'
    elif system == 'Darwin':
        return '"PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", sans-serif'
    else:
        return '"Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif'


def get_font_css():
    return f'* {{ font-family: {get_font_family()} !important; }}'


# ==================== Browser Management ====================

@contextmanager
def browser_page():
    """Launch headless chromium, yield a page with CJK font support, then cleanup."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = None
    context = None
    page = None
    try:
        browser = pw.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--font-render-hinting=full'],
        )
        context = browser.new_context(locale='zh-CN')
        page = context.new_page()
        page.add_style_tag(content=get_font_css())
        yield page
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        pw.stop()


# ==================== Draw.io Renderer ====================

def render_drawio_png(xml_code):
    """Render Draw.io XML to PNG bytes."""
    drawio_processor, _ = _get_processors()
    processed_xml = drawio_processor.process(xml_code)
    font_css = get_font_css()
    json_data = json.dumps({"xml": processed_xml})
    # HTML-encode ampersands so entities like &quot; survive HTML attribute parsing
    json_data_safe = json_data.replace('&', '&amp;')

    html = (
        '<!DOCTYPE html>\n<html>\n<head>\n'
        f'  <meta charset="utf-8">\n  <style>{font_css}</style>\n'
        '</head>\n<body>\n'
        f"  <div class=\"mxgraph\" style=\"max-width:100%;border:1px solid transparent;\" data-mxgraph='{json_data_safe}'></div>\n"
        '  <script type="text/javascript" src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>\n'
        '</body>\n</html>'
    )

    with browser_page() as page:
        page.set_content(html)
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('svg', state='visible', timeout=15000)
        page.wait_for_timeout(500)

        element = page.query_selector('svg')
        if not element:
            raise RuntimeError('未找到渲染的图表元素')

        return element.screenshot(type='png')


# ==================== Excalidraw Renderer ====================

def _create_excalidraw_page(page, export_func):
    """Setup an Excalidraw page with the specified export function loaded."""
    font_css = get_font_css()
    html = (
        '<!DOCTYPE html>\n<html>\n<head>\n'
        f'  <meta charset="utf-8">\n  <style>{font_css}</style>\n'
        '  <script type="module">\n'
        f"    import {{ {export_func} }} from 'https://esm.sh/@excalidraw/excalidraw';\n"
        f'    window.__{export_func} = {export_func};\n'
        '    window.__ready = true;\n'
        '  </script>\n'
        '</head>\n<body></body>\n</html>'
    )
    page.set_content(html)
    page.wait_for_function('() => window.__ready', timeout=30000)


def render_excalidraw_png(processed_json):
    """Render Excalidraw JSON to PNG bytes. Input should be already-processed JSON string."""
    with browser_page() as page:
        _create_excalidraw_page(page, 'exportToBlob')

        byte_array = page.evaluate(
            """async (json) => {
                const elements = JSON.parse(json);
                const blob = await window.__exportToBlob({
                    elements,
                    mimeType: 'image/png',
                    appState: {
                        viewBackgroundColor: '#ffffff',
                        exportWithDarkMode: false
                    },
                    files: {},
                });
                const arrayBuffer = await blob.arrayBuffer();
                return Array.from(new Uint8Array(arrayBuffer));
            }""",
            processed_json,
        )
        return bytes(byte_array)


def render_excalidraw_svg(processed_json):
    """Render Excalidraw JSON to SVG string. Input should be already-processed JSON string."""
    with browser_page() as page:
        _create_excalidraw_page(page, 'exportToSvg')

        svg_string = page.evaluate(
            """async (json) => {
                const elements = JSON.parse(json);
                const svgElement = await window.__exportToSvg({
                    elements,
                    appState: {
                        exportWithDarkMode: false
                    },
                    files: {},
                });
                return svgElement.outerHTML;
            }""",
            processed_json,
        )
        return svg_string


# ==================== Output Helpers ====================

def output_success(data):
    print(json.dumps({"status": "success", **data}))


def output_error(message, **details):
    print(json.dumps({"status": "error", "error": message, **details}))
    print(f'错误: {message}', file=sys.stderr)
    sys.exit(1)


# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(description='渲染图表为图片')
    parser.add_argument('type', choices=['drawio', 'excalidraw'], help='图表类型')
    parser.add_argument('-f', '--file', required=True, help='输入文件路径')
    parser.add_argument('-o', '--output', default='diagram.png', help='输出文件路径 (默认: diagram.png)')
    parser.add_argument('--svg', action='store_true', help='输出 SVG 格式 (仅 excalidraw)')
    parser.add_argument('--no-source', action='store_true', help='不保存源文件')
    args = parser.parse_args()

    # Validate --svg with drawio
    if args.svg and args.type == 'drawio':
        output_error('Draw.io 不支持 SVG 输出格式，仅支持 PNG')

    # Read input file
    input_path = Path(args.file).resolve()
    try:
        code = input_path.read_text(encoding='utf-8')
    except Exception as e:
        output_error('读取输入失败', reason=str(e))

    # Resolve output paths
    output_path = Path(args.output).resolve()
    source_ext = '.drawio' if args.type == 'drawio' else '.excalidraw'
    source_path = output_path.with_suffix(source_ext)

    # Render
    processed_json = None
    try:
        if args.type == 'drawio':
            rendered = render_drawio_png(code)
        else:
            # Process excalidraw code once, reuse for render + source
            _, excalidraw_processor = _get_processors()
            processed_json = excalidraw_processor.process(code)
            if args.svg:
                rendered = render_excalidraw_svg(processed_json)
            else:
                rendered = render_excalidraw_png(processed_json)
    except Exception as e:
        output_error('渲染失败', reason=str(e), suggestion='请检查输入代码格式是否正确；并确认已安装 Chromium (python -m playwright install chromium) 且网络可访问 viewer.diagrams.net/esm.sh')

    # Write output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.svg:
            output_path.write_text(rendered, encoding='utf-8')
        else:
            output_path.write_bytes(rendered)

        if not args.no_source:
            # Save as proper .excalidraw format (wrapped, not raw array)
            if args.type == 'excalidraw':
                try:
                    elements = json.loads(processed_json)
                    wrapped = {
                        "type": "excalidraw",
                        "version": 2,
                        "source": "https://excalidraw.com",
                        "elements": elements if isinstance(elements, list) else [elements],
                        "appState": {
                            "gridSize": None,
                            "viewBackgroundColor": "#ffffff"
                        },
                        "files": {}
                    }
                    source_path.write_text(
                        json.dumps(wrapped, ensure_ascii=False, indent=2),
                        encoding='utf-8',
                    )
                except (json.JSONDecodeError, ValueError):
                    source_path.write_text(code, encoding='utf-8')
            else:
                source_path.write_text(code, encoding='utf-8')
    except Exception as e:
        output_error('文件保存失败', reason=str(e))

    # Success
    result = {
        "file": str(output_path),
        "format": "svg" if args.svg else "png",
        "size": len(rendered),
    }
    if not args.no_source:
        result["sourceFile"] = str(source_path)

    output_success(result)


if __name__ == '__main__':
    main()
