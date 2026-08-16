"""TeleAgent emitter — TeleAgent(OpenCode 内核)的 cp 集成。

决策:
- install_dir = ~/.config/TeleAgent/skills/<name>/, method=cp
- 字段集 = 含 name_cn / description_cn(从 canonical description_zh/name_zh 镜像)
- level manual/experimental/disable -> enabled_at: false (借用 QwenWork 的同字段语义)
  注: disable 的"sync 不再部署"由上层 caller 控制
- description 不截断(TeleAgent 实测水印不会污染 SKILL.md, 见 watermark.ts:382 硬排除)
- canonical 元字段(native_agent/requires/version/license)不写入 TeleAgent 文件

TeleAgent AIGC 水印分析(后台 agent 实测查实):
- 注入只发生在 TeleAgent 进程内的 tool.execute.after 钩子(write/edit/bash 等工具)
- 外层 cp 不走 TeleAgent 进程, 钩子不触发 -> 无水印一线兜底
- 即便进程内触达, 文件名 SKILL.MD 被 isExcludedWatermarkFile 硬排除 -> 无水印二线兜底
- 双保险, cp 落盘绝对安全

零损耗: body bytes 不动, 双语字段从前言外(frontmatter)镜像, 不进 body。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import SkillIR

__all__ = ["TeleAgentEmitter"]


class TeleAgentEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("TeleAgent")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """TeleAgent frontmatter: name + description + 双语 _cn(从 canonical _zh 镜像)。

        canonical 只让用户填一种中文(默认 _zh), emitter 对 TeleAgent 自动镜像成 _cn;
        对 QwenWork 镜像成 _zh。两侧零损失无歧义。
        """
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": ir.description,
        }
        # 双语字段镜像: canonical description_zh -> TeleAgent description_cn
        if ir.description_zh is not None:
            fm["description_cn"] = ir.description_zh
        if ir.name_zh is not None:
            fm["name_cn"] = ir.name_zh
        # level manual/experimental -> enabled_at: false
        if cfg.needs_disable_invoke(ir.level.value):
            assert cfg.disable_invoke_field == "enabled_at", "TeleAgent 配置必须用 enabled_at"
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.config/TeleAgent/skills/<name>/"""
        skill_target_dir = Path(deploy_root) / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        content = self.build_skill_md_bytes(ir, cfg, prompt_bytes, canonical_skill_dir)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)
        return EmitterResult(deployed_path=skill_md_path, method="cp")