"""
Code processing pipeline for LLM-generated diagram code.
Ported from the Node.js modules: code-processor.js, fixUnclosed.js, optimizeArrows.js
"""

import re
import json


# ==================== Cleaning ====================

def clean_bom(code):
    """Remove BOM and zero-width characters."""
    if not code or not isinstance(code, str):
        return code
    code = code.replace('\ufeff', '')
    code = re.sub('[\u200b-\u200d\u2060]', '', code)
    return code.strip()


# ==================== Extraction ====================

def extract_code_fence(code, lang=None):
    """Extract code from markdown fences (```lang ... ```)."""
    if not code or not isinstance(code, str):
        return code

    if lang:
        pattern = re.compile(
            r'```\s*' + lang + r'\s*([\s\S]*?)```', re.IGNORECASE
        )
        m = pattern.search(code)
        if m and m.group(1):
            return m.group(1).strip()

    m = re.search(r'```\s*([\s\S]*?)```', code)
    if m and m.group(1):
        return m.group(1).strip()

    return code.strip()


def unescape_html(code):
    """Unescape HTML entities only when needed."""
    if not code or not isinstance(code, str):
        return code

    has_raw_tags = bool(re.search(r'<[a-z!?]', code, re.IGNORECASE))
    has_escaped = bool(re.search(r'&lt;\s*[a-z!?]', code, re.IGNORECASE))

    if not has_raw_tags and has_escaped:
        code = (code
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&amp;', '&')
                .replace('&quot;', '"')
                .replace('&#39;', "'"))
    return code


# ==================== XML-specific ====================

def extract_xml(code):
    """Extract XML content (find mxfile/mxGraphModel/diagram tags)."""
    if not code or not isinstance(code, str):
        return code

    m = re.search(r'<(mxfile|mxGraphModel|diagram)([\s>])', code, re.IGNORECASE)
    start = m.start() if m else -1
    end = code.rfind('>')

    if start != -1 and end != -1 and end > start:
        return code[start:end + 1]
    return code


_MX_TAG_MAP = {
    'mxgraphmodel': 'mxGraphModel',
    'mxcell': 'mxCell',
    'mxgeometry': 'mxGeometry',
    'mxpoint': 'mxPoint',
}


def normalize_mx_tags(code):
    """Fix case of mxgraph tags to canonical form."""
    if not code or not isinstance(code, str):
        return code

    def _replace(m):
        prefix = m.group(1)
        tag = m.group(2)
        return prefix + _MX_TAG_MAP.get(tag.lower(), tag)

    return re.sub(
        r'(<\s*/?)(mxgraphmodel|mxcell|mxgeometry|mxpoint)\b',
        _replace, code, flags=re.IGNORECASE,
    )


# ==================== JSON-specific ====================

def extract_json(code):
    """Extract JSON content (find first { or [)."""
    if not code or not isinstance(code, str):
        return code

    obj_start = code.find('{')
    obj_end = code.rfind('}')
    arr_start = code.find('[')
    arr_end = code.rfind(']')

    if arr_start != -1 and arr_end != -1 and (obj_start == -1 or arr_start < obj_start):
        return code[arr_start:arr_end + 1]
    if obj_start != -1 and obj_end != -1:
        return code[obj_start:obj_end + 1]
    return code


def extract_json_array_strict(code):
    """Strict JSON array extraction with bracket depth tracking, ignoring strings."""
    if not code or not isinstance(code, str):
        return code

    text = code
    length = len(text)
    start = -1
    depth = 0
    in_string = False
    escaped = False

    for i in range(length):
        ch = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            escaped = False
            continue

        if ch == '[':
            if start == -1:
                start = i
            depth += 1
        elif ch == ']':
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    return text[start:i + 1]

    return extract_json(code)


def ensure_excalidraw_array(code):
    """Ensure Excalidraw code is a JSON array string."""
    if not code or not isinstance(code, str):
        return code

    trimmed = code.strip()
    if not trimmed:
        return trimmed

    # Already array form
    if trimmed[0] == '[' and trimmed[-1] == ']':
        try:
            data = json.loads(trimmed)
            if isinstance(data, list):
                return json.dumps(data, indent=2)
            return trimmed
        except (json.JSONDecodeError, ValueError):
            return trimmed

    try:
        data = json.loads(trimmed)
        if isinstance(data, list):
            return json.dumps(data, indent=2)
        if isinstance(data, dict):
            if isinstance(data.get('elements'), list):
                return json.dumps(data['elements'], indent=2)
            if isinstance(data.get('items'), list):
                return json.dumps(data['items'], indent=2)
        return json.dumps([data], indent=2)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try wrapping with brackets
    try:
        arr = json.loads('[' + trimmed + ']')
        if isinstance(arr, list):
            return json.dumps(arr, indent=2)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting inner array
    inner_match = re.search(r'\[[\s\S]*\]', trimmed)
    if inner_match:
        try:
            arr = json.loads(inner_match.group(0))
            if isinstance(arr, list):
                return json.dumps(arr, indent=2)
        except (json.JSONDecodeError, ValueError):
            pass

    return trimmed


# ==================== fix_json (from fixUnclosed.js) ====================

def _strip_trailing_commas(text):
    """Remove trailing commas before } or ]."""
    return re.sub(r',(\s*[}\]])', r'\1', text)


def _add_missing_commas(text):
    """Insert commas between }{ and ][."""
    text = re.sub(r'}\s*(\{|\[)', r'},\1', text)
    text = re.sub(r']\s*(\{|\[)', r'],\1', text)
    return text


def _fix_json_structure(text):
    """Stack-based scanner to fix bracket mismatches and unclosed strings."""
    text = _add_missing_commas(text)

    stack = []
    in_string = False
    escaped = False
    result = []
    last_non_ws = ''

    for ch in text:
        if in_string:
            result.append(ch)
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            escaped = False
            result.append(ch)
            continue

        if ch in ('{', '['):
            stack.append(ch)
            result.append(ch)
            last_non_ws = ch
            continue

        if ch in ('}', ']'):
            need = '{' if ch == '}' else '['
            while stack and stack[-1] != need:
                unclosed = stack.pop()
                closing = '}' if unclosed == '{' else ']'
                result.append(closing)
                last_non_ws = closing
            if stack and stack[-1] == need:
                stack.pop()
            result.append(ch)
            last_non_ws = ch
            continue

        result.append(ch)
        if not ch.isspace():
            last_non_ws = ch

    if in_string:
        result.append('"')
        last_non_ws = '"'

    result_str = ''.join(result)

    if last_non_ws == ',':
        result_str = result_str.rstrip()
        if result_str.endswith(','):
            result_str = result_str[:-1]

    while stack:
        unclosed = stack.pop()
        result_str += '}' if unclosed == '{' else ']'

    return _strip_trailing_commas(result_str)


def fix_json(code):
    """Fix JSON: add missing commas, strip trailing commas, fix unclosed brackets/strings."""
    if not code or not isinstance(code, str):
        return code

    raw = code.strip()
    if not raw:
        return raw

    try:
        json.loads(raw)
        return raw
    except (json.JSONDecodeError, ValueError):
        pass

    fixed = _fix_json_structure(raw)
    try:
        json.loads(fixed)
        return fixed
    except (json.JSONDecodeError, ValueError):
        pass

    return _strip_trailing_commas(fixed)


# ==================== fix_xml (from fixUnclosed.js) ====================

_DEFAULT_VOID_TAGS = frozenset([
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr',
])


def _auto_close_angle_brackets(text):
    """Auto-close unclosed angle brackets (< without matching >)."""
    text = str(text) if text is not None else ''
    length = len(text)
    if not length:
        return text

    out = []
    i = 0

    while i < length:
        lt = text.find('<', i)
        if lt == -1:
            out.append(text[i:])
            break

        out.append(text[i:lt])

        j = lt + 1
        found_gt = -1
        found_next_lt = -1
        while j < length:
            ch = text[j]
            if ch == '>':
                found_gt = j
                break
            if ch == '<':
                found_next_lt = j
                break
            j += 1

        if found_gt != -1 and (found_next_lt == -1 or found_gt < found_next_lt):
            out.append(text[lt:found_gt + 1])
            i = found_gt + 1
            continue

        if found_next_lt == -1:
            segment = text[lt:]
            out.append(segment if segment.endswith('>') else segment + '>')
            break
        else:
            segment = text[lt:found_next_lt]
            out.append(segment if segment.endswith('>') else segment + '>')
            i = found_next_lt

    return ''.join(out)


def fix_xml(code, void_tags=None, html_mode=False):
    """Fix XML: auto-close angle brackets, track unclosed tags, append missing closing tags."""
    if not code or not isinstance(code, str):
        return code

    if void_tags is None:
        void_tags = _DEFAULT_VOID_TAGS

    text = _auto_close_angle_brackets(code)

    tag_re = re.compile(r'<([^>]+)>')
    stack = []
    out = []
    last_index = 0

    def normalize(name):
        return name.lower() if html_mode else name

    def is_void_tag(name):
        return name.lower() in void_tags

    for m in tag_re.finditer(text):
        out.append(text[last_index:m.start()])
        last_index = m.end()

        raw_tag = m.group(1).strip()

        # Comments / DOCTYPE / CDATA / processing instructions
        if (raw_tag.startswith('!--') or raw_tag.startswith('!DOCTYPE')
                or raw_tag.startswith('![CDATA[') or raw_tag.startswith('?')):
            out.append('<' + raw_tag + '>')
            continue

        # Closing tag
        if raw_tag.startswith('/'):
            parts = raw_tag[1:].split()
            raw_name = parts[0] if parts else ''
            normalized_name = normalize(raw_name)
            out.append('<' + raw_tag + '>')
            if stack and stack[-1]['normalized'] == normalized_name:
                stack.pop()
            continue

        # Opening tag
        self_closing = raw_tag.endswith('/')
        parts = raw_tag.split()
        raw_name = parts[0] if parts else ''
        normalized_name = normalize(raw_name)

        out.append('<' + raw_tag + '>')

        if not self_closing and not is_void_tag(raw_name):
            stack.append({'name': raw_name, 'normalized': normalized_name})

    out.append(text[last_index:])

    for i in range(len(stack) - 1, -1, -1):
        out.append('</' + stack[i]['name'] + '>')

    return ''.join(out)


# ==================== optimize_excalidraw_code (from optimizeArrows.js) ====================

def optimize_excalidraw_code(code_string):
    """For arrow/line elements with width=0 set to 1, height=0 set to 1."""
    if not code_string or not isinstance(code_string, str):
        return code_string

    try:
        cleaned = code_string.strip()
        array_match = re.search(r'\[[\s\S]*\]', cleaned)
        if not array_match:
            return code_string

        elements = json.loads(array_match.group(0))
        if not isinstance(elements, list):
            return code_string

        for element in elements:
            if not isinstance(element, dict):
                continue
            if element.get('type') not in ('arrow', 'line'):
                continue
            if element.get('width') == 0:
                element['width'] = 1
            if element.get('height') == 0:
                element['height'] = 1

        return json.dumps(elements, indent=2)
    except (json.JSONDecodeError, ValueError, TypeError):
        return code_string


# ==================== Pipeline ====================

class CodeProcessor:
    """Pipeline pattern: run processing steps in sequence."""

    def __init__(self, steps=None):
        self.steps = list(steps) if steps else []

    def process(self, code):
        """Execute all steps. On error in a step, keep the previous result."""
        result = code
        for step in self.steps:
            try:
                result = step(result)
            except Exception:
                pass
        return result

    def add_step(self, step):
        self.steps.append(step)
        return self


drawio_processor = CodeProcessor([
    clean_bom,
    lambda code: extract_code_fence(code, 'xml'),
    unescape_html,
    extract_xml,
    normalize_mx_tags,
    fix_xml,
])

excalidraw_processor = CodeProcessor([
    clean_bom,
    lambda code: extract_code_fence(code, 'json'),
    extract_json_array_strict,
    fix_json,
    optimize_excalidraw_code,
    ensure_excalidraw_array,
])


if __name__ == '__main__':
    pass
