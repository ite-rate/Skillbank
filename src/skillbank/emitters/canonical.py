"""Canonical emitter — SkillIR → canonical SKILL.md(写回中央仓)。

零损耗实现关键:
- body bytes 直接拼到 frontmatter 之后, 不 decode/encode/normalize
- frontmatter: 优先字段级透传(字节稳定)——parser 保留原始 frontmatter 字节,
  未变更的字段原字节保留, 只重写真正改动(新增/删除/修改)的字段。
  否则 safe_dump 全量重建会丢引号、改字段顺序(git diff 产生无意义噪音)。
  仅当 IR 无原始 frontmatter(如 import 新建)时, 才 safe_dump 全量生成。

roundtrip zero-loss: parse->IR0 -> emit_canonical -> parse -> IR1
    assert IR1.body == IR0.body  (字节完全等值)
    assert frontmatter 未变字段字节不变(字段级透传)
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skillbank.emitters.base import edit_frontmatter_fields
from skillbank.ir import SkillIR

__all__ = ["emit_canonical"]


def emit_canonical(ir: SkillIR, target_path: Path) -> None:
    """把 IR 写成 canonical SKILL.md。

    有原始 frontmatter(fm_raw/fm_orig)时走字段级透传(字节稳定);
    否则(如 import 新建)safe_dump 全量生成。
    Args:
        ir: SkillIR(必填 name/description)
        target_path: 写入路径(父目录需存在; 不自动建目录)
    """
    if ir.fm_raw is not None and ir.fm_orig is not None:
        raw_text = ir.fm_raw.decode("utf-8")
        edited = edit_frontmatter_fields(raw_text, ir.fm_orig, ir.to_frontmatter_dict())
        fm_bytes = edited.rstrip("\n").encode("utf-8") + b"\n"
    else:
        fm = ir.to_frontmatter_dict()
        fm_bytes = yaml.safe_dump(
            fm, sort_keys=False, allow_unicode=True,
            default_flow_style=False, width=10_000,
        ).encode("utf-8")

    out_bytes = b"---\n" + fm_bytes + b"---\n" + ir.body
    Path(target_path).write_bytes(out_bytes)
