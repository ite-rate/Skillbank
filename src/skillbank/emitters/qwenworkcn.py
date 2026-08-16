"""QwenWorkCN emitter — 千问办公(非 Qwen Code CLI)的 cp 集成。

决策:
- install_dir = ~/.qwenworkcn/skills/<name>/
- 字段集 = name + description + description_zh(下划线 zh, 与 canonical 同名)
- level manual/experimental/disable -> enabled_at: false (实测市场 skill 已用此字段)
- description 不截断(QwenWorkCN 实测无 1024 硬限)
- canonical 元字段(native_agent/requires/version/license)不写入 QwenWorkCN 文件
- 不取作废字段:priority/paths/user-invocable/source(那些属 Qwen Code CLI 开发者版, 不属 QwenWorkCN)
- keep_native_fields 也暂不输出(避免污染; 反向导入时若是市场装来的 skill 自带
  install_source/skill_id 等元数据, M6 反向 parser 会收, M2-M3 不主动写)

实测样本(QwenWorkCN 15 个 skill frontmatter 都不统一):
- 自带 skill: name/version/description/description_zh/license
- 市场装的 skill: name/description/install_source/install_method/skill_id/enabled_at/name_zh
- 我们只发 canonical 必需字段, 让既有的市场元数据保留(反向导入收 .agent_overrides)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import SkillIR

__all__ = ["QwenWorkCNEmitter"]


class QwenWorkCNEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("QwenWorkCN")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """QwenWorkCN frontmatter: name + description + 双语 _zh(canonical 同名直传)。"""
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": ir.description,
        }
        # canonical 中文双字段名就是 _zh, 与 QwenWorkCN 同名 -> 直接传
        if ir.description_zh is not None:
            fm["description_zh"] = ir.description_zh
        if ir.name_zh is not None:
            fm["name_zh"] = ir.name_zh
        if cfg.needs_disable_invoke(ir.level.value):
            assert cfg.disable_invoke_field == "enabled_at", "QwenWorkCN 配置必须用 enabled_at"
            fm[cfg.disable_invoke_field] = cfg.disable_invoke_value
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path,
    ) -> EmitterResult:
        """cp SKILL.md + resources/ 到 ~/.qwenworkcn/skills/<name>/"""
        skill_target_dir = Path(deploy_root) / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        content = self.build_skill_md_bytes(ir, cfg, canonical_skill_dir)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)
        return EmitterResult(deployed_path=skill_md_path, method="cp")