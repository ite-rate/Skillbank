"""SkillHub parsers — 各输入源 SKILL.md → SkillIR。

canonical.py  — 中央仓 canonical SKILL.md(parser 默认入口)
(M6 各 Agent 既有 skill 反向导入时, 加 parsers/<agent>.py)
"""

from skillhub.parsers.canonical import parse_canonical

__all__ = ["parse_canonical"]