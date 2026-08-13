"""Canonical SKILL.md parser — skills/<name>/SKILL.md → SkillIR。

零损耗实现关键:
- raw 文件按 bytes 读
- 用 bytes 正则匹配 frontmatter 边界 `^---\\n ... \\n---\\n`(允许 \\r\\n)
- frontmatter bytes 解 YAML 拿 dict; body bytes 取边界后的所有原字节
- body 直接放进 IR.body, 不 decode 不修改

若文件无 frontmatter(canonical 必须有, 但 parser 对 Agent 既有 skill 反向导入时也兼容):
- 视为整个文件是 body, name/description 缺(canonical 验证失败, 反向导入可后补)。
- 此模块只对 canonical 用, 反向导入走 parsers/<agent>.py(M6)。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from skillhub.ir import SkillIR

__all__ = ["parse_canonical", "FRONTMATTER_RE", "InvalidCanonicalError"]

# byte-level frontmatter 边界匹配 — 允许 \\n 或 \\r\\n 行结束符
# group(1) = frontmatter YAML 正文  group(2) = body 全部后续字节
FRONTMATTER_RE = re.compile(rb"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z", re.DOTALL)


class InvalidCanonicalError(ValueError):
    """canonical SKILL.md 必须有 `---\\n frontmatter \\n---\\n` 边界。"""


def parse_canonical(path: Path) -> SkillIR:
    """读 canonical SKILL.md(整文件 bytes) 并解析成 SkillIR。

    Args:
        path: 必须 Path, points to skills/<name>/SKILL.md
    Returns:
        SkillIR — body 为文件字节流 frontmatter 边界后的全部原字节
    Raises:
        InvalidCanonicalError: 无 frontmatter 边界
        KeyError: frontmatter 缺 name/description(canonical 必填)
    """
    raw = Path(path).read_bytes()
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise InvalidCanonicalError(
            f"canonical SKILL.md 必须有 frontmatter 边界 `---\\n...\\n---\\n`: {path}"
        )
    fm_bytes = m.group("fm")
    body_bytes = m.group("body")
    fm = yaml.safe_load(fm_bytes.decode("utf-8"))
    if not isinstance(fm, dict):
        raise InvalidCanonicalError(f"frontmatter 必须是 YAML mapping: {path}")

    return SkillIR.from_frontmatter_dict(fm, body_bytes, source_path=Path(path))