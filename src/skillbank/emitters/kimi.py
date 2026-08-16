"""kimi-code emitter — kimi(moonshot kimi-code)的 cp 集成。

实测决策(M4 strings 直读 kimi 二进制确认):
- install_dir = ~/.kimi-code/skills/<name>/  <- kimi 默认 user skills root
  strings 证据: kimi 内部逻辑含 "默认 user skills root ~/.kimi-code/skills/"
            + "Copy the user's legacy skills tree (~/.kimi/skills/) into kimi-code's default"
  也即 kimi 自带的"从 legacy 路径自动迁移"机制会复制 ~/.kimi/skills 到 ~/.kimi-code/skills,
 证实默认 discovery 是 ~/.kimi-code/skills/。emitter 直接 cp 到那里, 无需 --skills-dir。
- 字段集 = name + description(kimi 走 Anthropic Skill 标准子集, 实测无优先级字段)
- level manual/experimental/disable -> kimi 不支持 frontmatter 禁止触发字段,
  无 disable_invoke_field 配置 -> 不写(canonical level 信息不上 kimi frontmatter
  但不影响功能, manual skill 仍通过 kimi 调用 keyword / 项目用 skill)
  注:这一条等 M6 反向 parser 接 kimi 既有 skill 时再深查
- description 不截断(kimi 实测无 1024 限制)
- canonical 元字段(native_agent/requires/version/license)不写入 kimi 文件

kimi 模型能力实测(K3 1M ctx): thinking/image_in/video_in/tool_use/web_search/web_fetch
capability matrix 中 file/bash 等字段记 unknown(已查实, 不编造)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import SkillIR

__all__ = ["KimiEmitter"]


class KimiEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("kimi-code")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """kimi frontmatter: name + description(Anthropic Skill 标准子集)。

        level 映射: kimi 无 frontmatter 禁止触发字段(cfg.disable_invoke_field is None),
        emitter 不写额外字段。
        """
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": ir.description,
        }
        # 仅当 cfg 配了 disable_invoke_field 才写(目前 kimi 没配, 留作扩展位)
        if cfg.disable_invoke_field and cfg.needs_disable_invoke(ir.level.value):
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.kimi-code/skills/<name>/"""
        skill_target_dir = Path(deploy_root) / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        content = self.build_skill_md_bytes(ir, cfg, prompt_bytes, canonical_skill_dir)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)
        return EmitterResult(deployed_path=skill_md_path, method="cp")