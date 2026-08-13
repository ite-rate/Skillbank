"""SkillHub emitters — SkillIR → 各 Agent 目录的 SKILL.md(+ resources)。

canonical.py — 写回中央仓 canonical 格式(回环测试 + add/import 落地)
(M2-M4 加 emitters/<agent>.py: claudecode/zcode/qwenworkcn/teleagent/hermes/codex/kimi-code)
"""

from skillhub.emitters.canonical import emit_canonical

__all__ = ["emit_canonical"]