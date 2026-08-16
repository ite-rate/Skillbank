"""ClaudeCode emitter — Anthropic Skill 标准本尊(最简单的 emitter)。

集成方式(决策):
- install_dir = ~/.claude/skills/<name>/
- method = cp  整目录(SKILL.md + resources/)
- 字段集 = Anthropic Skill 标准 frontmatter(name + description), canonical 其余字段一律不污染
  - level manual/experimental -> disable-model-invocation: true
  - level disable     -> emitter 不调用(上层 caller 在 sync 时筛掉 disable skill)
  - canonical 的 native_agent/requires/description_zh/name_zh/version/license 都是元字段,
    不要写到 Agent 文件(它们是 emitter 决策依据, 不是给 Agent LLM 看的)
- description 不截断(Claude Code 无硬字符限制)
- 不做 lang_duplication(Claude 用 description 单字段, 不需要中文镜像)
- keep_native_fields = [](canonical 不污染 Claude)

零损耗保证: body 经 prompt_inject 顶前言 + 直接 bytes 拼接, body 字节本身不变。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import Level, SkillIR

__all__ = ["ClaudeCodeEmitter"]


class ClaudeCodeEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("ClaudeCode")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict:
        """只输出 name + description(+ 可选 disable-model-invocation)。

        Anthropic Skill 标准: 字段集保最小, 不带多余字段。
        """
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": ir.description,
        }
        # level manual/experimental/disable 都映射到 disable-model-invocation: true
        # (disable 还包括"sync 不再部署"由上层 sync caller 控制, emitter 不会被 disable skill 调)
        if cfg.needs_disable_invoke(ir.level.value):
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.claude/skills/<name>/。"""
        deploy_root = Path(deploy_root)
        skill_target_dir = deploy_root / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)

        content = self.build_skill_md_bytes(ir, cfg, prompt_bytes, canonical_skill_dir)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        # resources 拷过去
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)

        return EmitterResult(
            deployed_path=skill_md_path,
            method="cp",
            note="",
        )