"""Canonical emitter — SkillIR → canonical SKILL.md(写回中央仓)。

零损耗实现关键:
- body bytes 直接拼到 frontmatter 之后, 不 decode/encode/normalize
- frontmatter yaml 序化(sort_keys=False 保用户顺序 + allow_unicode 不转义中文)
- 输出 = b'---\\n' + yaml_bytes + b'---\\n' + body_bytes

roundtrip zero-loss: parse->IR0 -> emit_canonical -> parse -> IR1
    assert IR1.body == IR0.body  (字节完全等值)
frontmatter 字段往返允许 dict 等值即可(序化格式可漂移, body 不漂移)。
"""

from __future__ import annotations

from pathlib import Path

import yaml

from skillbank.ir import SkillIR

__all__ = ["emit_canonical"]


def emit_canonical(ir: SkillIR, target_path: Path) -> None:
    """把 IR 写成 canonical SKILL.md。

    Args:
        ir: SkillIR(必填 name/description)
        target_path: 写入路径(父目录需存在; 不自动建目录)
    """
    fm = ir.to_frontmatter_dict()
    # sort_keys=False 保用户在 frontmatter 写入时的字段顺序;
    # allow_unicode=True 让中文不转义成 \\uXXXX;
    # default_flow_style=False 让 list(default [a, b]) 序化成块
    #   但 requires: [a, b] 用 inline 更紧凑 -> 单独处理
    fm_bytes = yaml.safe_dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10_000
    ).encode("utf-8")
    # yaml.safe_dump 末尾自带 \\n; 我们要的格式: --- \\n <fm> \\n --- \\n <body>
    # yaml 输出已经包含 trailing \\n, 直接拼 \\n---\\n:
    out_bytes = b"---\n" + fm_bytes + b"---\n" + ir.body
    Path(target_path).write_bytes(out_bytes)