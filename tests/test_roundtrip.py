"""零损耗硬约束 — CI 门。

roundtrip: parse(canonical) -> IR0 -> emit_canonical -> parse -> IR1
        assert IR1.body == IR0.body (字节完全等值)

覆盖场景:
- 纯 ASCII body
- 含 unicode 中文 body
- 含 \\r\\n (Windows 换行) body — 不被规整成 \\n
- 含 BOM-less 中英混排 + 特殊字符 \\t \\x00 等
- body 开头是空行 / 多空行 / 紧贴 frontmatter
- 各种 level / native_agent / requires / 双语字段组合
- 空 body (frontmatter 紧跟空)
"""

from __future__ import annotations

import pytest

from skillhub.emitters.canonical import emit_canonical
from skillhub.ir import Level
from skillhub.parsers.canonical import parse_canonical


def _roundtrip(tmp_path, content_bytes: bytes) -> tuple[bytes, bytes]:
    """canonical -> parse -> emit -> parse, 返回 (IR0.body, IR1.body)。"""
    src = tmp_path / "src"
    src.mkdir()
    src_skill = src / "SKILL.md"
    src_skill.write_bytes(content_bytes)
    ir0 = parse_canonical(src_skill)

    dst = tmp_path / "dst"
    dst.mkdir()
    dst_skill = dst / "SKILL.md"
    emit_canonical(ir0, dst_skill)
    ir1 = parse_canonical(dst_skill)
    return ir0.body, ir1.body


def test_ascii_body_roundtrip_identical(tmp_path):
    original = b"""\
---
name: demo
description: a demo skill
level: auto
---

body line 1
body line 2
    indented line
"""
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(ASCII)\n原 body: {b0!r}\n往返 body: {b1!r}"


def test_unicode_chinese_body_roundtrip_identical(tmp_path):
    original = (
        b"---\n"
        b"name: canvas\n"
        b"description: \xe5\x88\x9b\xe6\x84\x8f\xe6\xb5\xb7\xe6\x8a\xa5\n"
        b"level: auto\n"
        b"description_zh: \xe6\xb5\xb7\xe6\x8a\xa5\n"
        b"---\n"
        b"\xe6\xad\xa3\xe6\x96\x87\xe5\xbc\x80\xe5\xa7\x8b\n"
        b"# \xe4\xb8\xad\xe6\x96\x87\xe6\xa0\x87\xe9\xa2\x98\n"
    )
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(Unicode)\n原 body: {b0!r}\n往返 body: {b1!r}"


def test_crlf_body_not_normalized_to_lf(tmp_path):
    """关键场景: canonical 用 \\n; 但 Agent 既有 skill 反向导入时可能含 \\r\\n。
    parser/emitter 不得把 \\r\\n 改成 \\n。"""
    # canonical frontmatter 用 \n; body 含 \r\n
    original = b"---\r\nname: crlf\ndescription: x\r\nlevel: auto\r\n---\r\nfirst\r\nsecond\r\n"
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(CRLF)\n原 body: {b0!r}\n往返 body: {b1!r}"
    # 特别校验: 原 CRLF 必须存在, 不被改成 LF
    assert b"\r\n" in b1, "CRLF body 被规整成 LF — 零损耗破"


def test_body_with_tabs_and_null_byte(tmp_path):
    original = b"---\nname: tabs\ndescription: x\nlevel: auto\n---\n\ta\tb\x00c\nend\n"
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(tabs/null)\n原 body: {b0!r}\n往返 body: {b1!r}"


def test_body_starts_with_blank_lines(tmp_path):
    original = b"---\nname: blanks\ndescription: x\nlevel: auto\n---\n\n\n\nbody after blanks\n"
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(空行起首)\n原 body: {b0!r}\n往返 body: {b1!r}"
    # 校验空行还在
    assert b1.startswith(b"\n\n\n"), "leading blank lines 被吞"


def test_body_starts_immediately_after_frontmatter(tmp_path):
    """body 紧贴 frontmatter(无空行)——确认 body 前的第 1 字节没被吞。"""
    original = b"---\nname: adj\ndescription: x\nlevel: auto\n---\nno-blank-here\n"
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(紧贴)\n原 body: {b0!r}\n往返 body: {b1!r}"
    assert b1 == b"no-blank-here\n", "body 首字节被吞"


def test_empty_body_after_frontmatter_newline_only(tmp_path):
    original = b"---\nname: empty\ndescription: x\nlevel: auto\n---\n"
    b0, b1 = _roundtrip(tmp_path, original)
    assert b1 == b0, f"零损耗被破(空 body)\n原 body: {b0!r}\n往返 body: {b1!r}"
    assert b0 == b"\n" or b0 == b"", f"空 body 应只剩分隔符换行: got {b0!r}"


def test_full_field_set_roundtrip_identical(tmp_path):
    """完整 canonical frontmatter 字段 + 复杂 body 往返全等。"""
    original = b"---\n" \
        b"name: full-fields\n" \
        b"description: A skill with every canonical frontmatter field exercised.\n" \
        b"level: manual\n" \
        b"native_agent: TeleAgent\n" \
        b"requires: [image_generation, file_write]\n" \
        b"description_zh: \xe5\x88\x9b\xe6\x84\x8f\n" \
        b"name_zh: \xe5\x88\x9b\xe6\x84\x8f\n" \
        b"version: 1.0.0\n" \
        b"license: MIT\n" \
        b"---\n" \
        b"\n## Step 1\n\nDo thing.\n\n```python\nprint('hi')\n```\n"
    src = tmp_path / "src"; src.mkdir()
    src_skill = src / "SKILL.md"; src_skill.write_bytes(original)
    ir0 = parse_canonical(src_skill)

    # field-level assertions
    assert ir0.name == "full-fields"
    assert ir0.level == Level.MANUAL
    assert ir0.native_agent == "TeleAgent"
    assert ir0.requires == ["image_generation", "file_write"]
    assert ir0.description_zh == "\u521b\u610f"
    assert ir0.name_zh == "\u521b\u610f"
    assert ir0.version == "1.0.0"
    assert ir0.license == "MIT"

    # roundtrip zero-loss
    dst = tmp_path / "dst"; dst.mkdir()
    dst_skill = dst / "SKILL.md"
    emit_canonical(ir0, dst_skill)
    ir1 = parse_canonical(dst_skill)
    assert ir1.body == ir0.body, f"零损耗被破(full set)\n原 body: {ir0.body!r}\n往返 body: {ir1.body!r}"

    # field-level survive
    assert ir1.name == ir0.name
    assert ir1.description == ir0.description
    assert ir1.level == ir0.level
    assert ir1.native_agent == ir0.native_agent
    assert ir1.requires == ir0.requires
    assert ir1.description_zh == ir0.description_zh
    assert ir1.name_zh == ir0.name_zh
    assert ir1.version == ir0.version
    assert ir1.license == ir0.license


def test_disable_level_roundtrip(tmp_path):
    original = b"---\nname: dis\ndescription: x\nlevel: disable\n---\nbody\n"
    src = tmp_path / "src"; src.mkdir()
    src_skill = src / "SKILL.md"; src_skill.write_bytes(original)
    ir0 = parse_canonical(src_skill)
    assert ir0.level == Level.DISABLE
    assert not ir0.level_allows_sync()
    assert not ir0.level_allows_auto_trigger()

    dst = tmp_path / "dst"; dst.mkdir()
    emit_canonical(ir0, dst / "SKILL.md")
    ir1 = parse_canonical(dst / "SKILL.md")
    assert ir1.body == ir0.body


def test_missing_frontmatter_raises(tmp_path):
    """canonical 必须有 frontmatter; 无的非法文件应抛错(M6 反向导入时由 caller 兜底)。"""
    p = tmp_path / "bad" / "SKILL.md"
    p.parent.mkdir()
    p.write_bytes(b"# just a body, no frontmatter\n")
    with pytest.raises(Exception):
        parse_canonical(p)


def test_missing_required_name_raises(tmp_path):
    p = tmp_path / "bad" / "SKILL.md"
    p.parent.mkdir()
    p.write_bytes(b"---\ndescription: x\nlevel: auto\n---\nbody\n")
    with pytest.raises(KeyError):
        parse_canonical(p)


def test_body_hash_stable(tmp_path):
    """body_hash 应稳定(同字节流两次 hash 一致), 用于 manifest 跨机器验证零损耗。"""
    original = b"---\nname: hash\ndescription: x\nlevel: auto\n---\nbody\n"
    src = tmp_path / "src"; src.mkdir()
    src_skill = src / "SKILL.md"; src_skill.write_bytes(original)
    ir0 = parse_canonical(src_skill)

    dst = tmp_path / "dst"; dst.mkdir()
    emit_canonical(ir0, dst / "SKILL.md")
    ir1 = parse_canonical(dst / "SKILL.md")

    assert ir0.body_hash() == ir1.body_hash(), "往返后 body_hash 不一致 — body 已漂移"