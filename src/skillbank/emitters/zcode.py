"""ZCode emitter — ~/.zcode/skills/<name> cp 拷贝(与 ClaudeCode 同形)。

2026-08-16 改动: 用户拍板 ZCode 从 ln 软链改成 cp 统一。
理由: 7 个 Agent 格式各不相同, emitter 要翻译 frontmatter;
软链过去 Agent 读到的是 canonical 原文(含 level/native_agent 等元字段),
不是各 Agent 方言版。cp 让 emitter 翻译后产物是独立文件, 跟其他 6 个 Agent 统一。

ZCode 与 ClaudeCode 同形: name + description (+ disable-model-invocation)。
frontmatter 重排 + body 零损耗 + 前言注入, 跟 ClaudeCode emitter 完全一致。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import SkillIR

__all__ = ["ZCodeEmitter"]


class ZCodeEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("ZCode")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """ZCode 与 ClaudeCode 同形: name + description (+ disable-model-invocation)。"""
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": ir.description,
        }
        if cfg.needs_disable_invoke(ir.level.value):
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.zcode/skills/<name>/"""
        skill_target_dir = Path(deploy_root) / ir.name

        # 若目标是旧软链, 先 unlink 再 cp(从软链改 cp 的迁移)
        if skill_target_dir.is_symlink():
            skill_target_dir.unlink()
        elif skill_target_dir.exists() and not skill_target_dir.is_dir():
            skill_target_dir.unlink()

        skill_target_dir.mkdir(parents=True, exist_ok=True)
        content = self.build_skill_md_bytes(ir, cfg, prompt_bytes, canonical_skill_dir)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)
        return EmitterResult(deployed_path=skill_md_path, method="cp")