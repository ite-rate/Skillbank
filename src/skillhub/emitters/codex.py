"""Codex emitter — OpenAI Codex 的 cp 集成 + description ≤1024 硬截断。

决策:
- install_dir = ~/.codex/skills/<name>/
- 字段集 = name + description (+ disable-model-invocation 当 level manual/experimental/disable)
- description 截断 <= 1024 字符(Codex 加载硬限; 超了加载失败)
    截断方式: 后缀省略号 '...'(决策倾向: 不动 description 源, canonical 保留全长,
    只 emitter 产物截断)
- body 不动(零损耗; 截断只 impact frontmatter description)

注意: description 含 emoji/中文等多字节 UTF-8 字符时, "1024 字符"指 Unicode 字符数,
不是字节数。用 len(str) 而非 len(bytes)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillhub.agents import AgentConfig
from skillhub.emitters.base import BaseEmitter, EmitterResult
from skillhub.ir import SkillIR

__all__ = ["CodexEmitter"]

CODEX_DESC_MAX = 1024
ELLIPSIS = "..."


class CodexEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("Codex")

    @staticmethod
    def _truncate_description(desc: str, max_chars: int = CODEX_DESC_MAX) -> str:
        """后缀省略号截断 — 保 Unicode 字符数(非字节数); 不动 description 源, 只截 emitter 产物。"""
        if len(desc) <= max_chars:
            return desc
        # 留 '...' 的位置
        clip = max_chars - len(ELLIPSIS)
        if clip <= 0:
            return ELLIPSIS  # 1024 < 3 极端不可能, 但健壮兜底
        return desc[:clip] + ELLIPSIS

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        fm: dict[str, Any] = {
            "name": ir.name,
            # description 截断(若 cfg.description_max 配了)
            "description": self._truncate_description(
                ir.description, cfg.description_max or CODEX_DESC_MAX
            ),
        }
        if cfg.needs_disable_invoke(ir.level.value):
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.codex/skills/<name>/"""
        skill_target_dir = Path(deploy_root) / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        content = self.build_skill_md_bytes(ir, cfg, prompt_bytes)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)
        # 告知 manifest 与 caller: description 被截过
        desc_truncated = len(ir.description) > (cfg.description_max or CODEX_DESC_MAX)
        note = "description truncated to 1024 chars (Codex load limit)" if desc_truncated else ""
        return EmitterResult(deployed_path=skill_md_path, method="cp", note=note)