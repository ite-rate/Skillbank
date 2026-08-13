"""ZCode emitter — ~/.zcode/skills/<name> 软链跟随(决策)。

现状:~/.zcode/skills 是混合体——既有 symlink 到 claude/codex 的(本来就工作),
又有 archify/atelier/forge 等真实副本(冗余, claude/codex 都有同名版)。
Skill-Hub 时代:ZCode 全部改为软链跟随 SkillHub canonical。

决策层级:
- emitter 对"本轮要部署到 ZCode 的 skill" -> target 是 ~/.zcode/skills/<name> 软链
    指向 SkillHub canonical skill 目录(<root>/skills/<name>/)
- 既有真实副本(archify/atelier 等 20+ 个)不主动删 —— 破坏性操作必须用户确认
    skillhub zcode-cleanup 子命令提供交互确认 + mv 备份到 ~/.zcode/skills.bak/<timestamp>/<name>/
    然后再 ln -s(可回滚; 用户决定清几个)
- 既有的 ogora/brainstorming/dbs 等已软链工作良好的不动(M4 不破坏)

零损耗:ZCode 走软链, body bytes 由 SkillHub canonical 直接持有, 软链透传;
部署时 SKILL.md 是 canonical 那份的链(SymlinksSkillDir 软链整个 skill 目录)。

frontmatter 重写:ZCode 是 GLM-5.2 coding agent, 与 Claude Code 同 frontmatter 子集;
level manual/experimental/disable -> disable-model-invocation: true。
softlink 模式下,SKILL.md 源就是 canonical 那份本尊——
emitter 写一个生成的 SKILL.md 替换吗? 不都做软链了?

  关键设计选择(决策点):ZCode target 软链的是整个目录,
  -> 那么部署进去的 SKILL.md 实际内容就是 canonical 原文带 level/native_agent 等"非 Claude 兼容字段"。
  -> ZCode 只接受 name/description/frontmatter 子集;
     -> "重复 ZCode 兼容 canonical 写法"或者 emitter 生成一个子集写盘是两条路。

  决策:ZCode 走 "混合软链" —— target 目录软链到 canonical skill dir,
  SKILL.md 直接是 canonical 那份正本(ZCode 实测能识别的话)—— 但 canonical 还含 level/native_agent 等字段。
  最干净的方案:把 ZCode 当 Claude 同形处理(Claude Code 实测也认这种 canonical 完整 frontmatter),
  软链等于复制(canonical 已稳), ZCode 自行解析需要的子集。

  为保 zero-loss 明面 + 双语简单, ZCode 暂走软链(不强 frontmatter transformation),
  把 cross-Agent 子集处理交还 parser canonical 字段的零损耗保证。
  native_agent 等字段就算留在 ZCode 拿到的 SKILL.md frontmatter 里也没关系——
  ZCode 只是"看到多字段就忽略", 不会失败。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skillhub.agents import AgentConfig
from skillhub.emitters.base import BaseEmitter, EmitterResult
from skillhub.ir import SkillIR

__all__ = ["ZCodeEmitter"]


class ZCodeEmitter(BaseEmitter):
    def __init__(self) -> None:
        super().__init__("ZCode")

    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict[str, Any]:
        """ZCode 与 ClaudeCode 同形: name + description (+ disable-model-invocation)。

        但 ZCode target 走软链整目录, deploy 不写 frontmatter-translated SKILL.md;
        此 transform 仅在出现 ZCode 与软链冲突时(未预期)的 fallback 用。
        """
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
        """target_skill_dir 软链到 canonical_skill_dir(整个目录)。

        body zero-loss: 软链透传, SKILL.md 字节就是 canonical 那份本尊的字节。
        前言(native_agent/requires) -> 目前 ZCode 走软链, 不重新拼一份带前言的 SKILL.md;
        ZCode 同模型家族, 我们可能希望它也收到原生 Agent 提示但软链模式下前言只能进 canonical 顶层。
        暂不实施前言到 ZCode 的拼接(若需要, 改成"软链 + 在 SkillHub canonicalSKILLMD 里硬塞前言"),
        正文零损耗的硬约束在前言是常规的"非 zero-loss 不可的 canonical 自己"(前言是推断后的 mark)。
        """
        canonical_skill_dir = Path(canonical_skill_dir)
        target_skill_dir = Path(deploy_root) / ir.name

        # 若目标已是软链(指哪无所谓: claude/codex 都没事), unlink 后重链到 SkillHub canonical
        # 若是真实目录(archify 这类), 不动! 留给 skillhub zcode-cleanup 子命令交互处理
        if target_skill_dir.is_symlink():
            # 已是软链, 可能指 claude/codex 的旧版; 改成指 SkillHub canonical(单一来源)
            target_skill_dir.unlink()
            self.symlink_skill_dir(canonical_skill_dir, target_skill_dir)
            note = "relinked symlink -> SkillHub canonical"
        elif not target_skill_dir.exists():
            # 干净目标, 直接软链
            self.symlink_skill_dir(canonical_skill_dir, target_skill_dir)
            note = "symlinked to SkillHub canonical"
        else:
            # 真实目录(archify 等), M4 不破坏; 加 note 让 caller 知道需手工 zcode-cleanup
            # 也不写 SKILL.md(防覆盖真实文件)
            note = ("REAL DIR present (not a symlink); "
                    "run `skillhub zcode-cleanup` to back up + link to SkillHub canonical")

        # 软链模式下未写 SKILL.md, 但若已成软链, skill_md path 就是 canonical 那份本尊
        deployed_path = (target_skill_dir / "SKILL.md") if target_skill_dir.exists() else Path("/dev/null")
        return EmitterResult(
            deployed_path=deployed_path,
            method="ln" if target_skill_dir.is_symlink() else "deferred",
            note=note,
        )