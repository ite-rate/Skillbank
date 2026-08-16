"""Hermes emitter — NousResearch Hermes 的 cp 集成 + category 子目录 + 100k 文件超限跳过。

决策:
- install_dir = ~/.hermes/skills/<category>/<name>/
    实测 Hermes 目录结构混合:creative/ 子目录(39 个 skill) + 顶层混合软链/agora
    emitter 用 imported/ 作为默认 category, 不污染 creative/
    (Hermes 自带 .hub/.curator_state 管家, 只丢文件让其自洽, 不动其状态)
- 字段集 = name + description (+ disable-model-invocation 在 metadata.hermes 命名空间下)
- description 截断 <= 1024 字符(Hermes 限制; 复用 Codex 截断方式)
- file_size_max = 100000: 单 SKILL.md 总字符数(指 deployed 产物)
    超限 -> emitter 不部署到 Hermes + 加 note("file_size_max exceeded, skipped")
    body 零损耗不被破(Hermes 缺席此 skill, 其他 Agent 正常同步)
- body 不动(零损耗); description 截断只 impact frontmatter

Hermes 单文件 ≤100k 的判断口径:
- 指 deployed SKILL.md 总字符数(含 frontmatter + body)
- 用 Unicode 字符数 len(str), 非 len(bytes)
- 超限 -> 取 EmitterResult.method='skipped' + note, 不写盘, 不算部署成功
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillbank.agents import AgentConfig
from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.ir import SkillIR

__all__ = ["HermesEmitter"]

HERMES_DESC_MAX = 1024
HERMES_FILE_MAX = 100_000
HERMES_DEFAULT_CATEGORY = "imported"
ELLIPSIS = "..."


class HermesEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("Hermes")

    @staticmethod
    def _truncate_description(desc: str, max_chars: int = HERMES_DESC_MAX) -> str:
        if len(desc) <= max_chars:
            return desc
        clip = max_chars - len(ELLIPSIS)
        return desc[:clip] + ELLIPSIS if clip > 0 else ELLIPSIS

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """Hermes frontmatter: name + description; level 映射走 metadata.hermes 命名空间。"""
        fm: dict[str, Any] = {
            "name": ir.name,
            "description": self._truncate_description(
                ir.description, cfg.description_max or HERMES_DESC_MAX
            ),
        }
        if cfg.needs_disable_invoke(ir.level.value):
            # Hermes 的禁止自动触发字段在 metadata.hermes 命名空间下
            # yaml.safe_dump 会把 dict metadata.hermes 序化成块
            assert cfg.disable_invoke_field == "metadata.hermes.disable-model-invocation", (
                "Hermes 配置必须用 metadata.hermes.disable-model-invocation"
            )
            fm["metadata"] = {"hermes": {"disable-model-invocation": cfg.disable_invoke_value}}
        return fm

    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path,
    ) -> EmitterResult:
        """cp 到 ~/.hermes/skills/<category>/<name>/(category 默认 imported/); 100k 超限跳过。"""
        # 先拼字节流算总字符数(决定是否超限)
        content = self.build_skill_md_bytes(ir, cfg, canonical_skill_dir)
        total_chars = len(content.decode("utf-8", errors="replace"))
        file_max = cfg.file_size_max or HERMES_FILE_MAX
        if total_chars > file_max:
            return EmitterResult(
                deployed_path=Path("/dev/null"),
                method="skipped",
                note=(
                    f"file_size_max exceeded: deployed SKILL.md would be "
                    f"{total_chars} chars > Hermes limit {file_max}; skipped (body zero-loss intact)"
                ),
            )

        category = cfg.default_category or HERMES_DEFAULT_CATEGORY
        skill_target_dir = Path(deploy_root) / category / ir.name
        skill_target_dir.mkdir(parents=True, exist_ok=True)
        skill_md_path = skill_target_dir / "SKILL.md"
        self.write_skill_md(content, skill_md_path)
        self.write_resources(ir, skill_target_dir, canonical_skill_dir)

        note_parts: list[str] = []
        if len(ir.description) > (cfg.description_max or HERMES_DESC_MAX):
            note_parts.append("description truncated to 1024")
        if category != HERMES_DEFAULT_CATEGORY:
            note_parts.append(f"category={category}")
        return EmitterResult(
            deployed_path=skill_md_path,
            method="cp",
            note="; ".join(note_parts),
        )