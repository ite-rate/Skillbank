"""Emitter base — 7 个 Agent emitter 统一接口 + 公共 frontmatter 重组逻辑。

emitter 输出格式(全部 Agent 都遵循):
    b'---\\n' + yaml_frontmatter_dict + b'---\\n' + maybe_prompt_bytes + ir.body

各 Agent override:
- transform_frontmatter(ir, cfg) -> dict: 重排 frontmatter 字段为该 Agent 兼容子集
- deploy(ir, target_path, ...): cp 写 SKILL.md + resources, 或 ln 软链整个 skill_dir

公共逻辑(放在 base):
- 拼最终 bytes (frontmatter + 顶前言 + body)
- 目录创建 / 软链接 / cp
- frontmatter yaml 序化(allow_unicode, sort_keys=False 保顺序)
- 描述截断(各 Agent emitter 不重写)
"""

from __future__ import annotations

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from skillhub.agents import AgentConfig
from skillhub.ir import SkillIR

__all__ = ["EmitterResult", "BaseEmitter", "emit_frontmatter_block"]


def emit_frontmatter_block(fm: dict) -> bytes:
    """把 frontmatter dict 序化成 `---\\n<yaml>\\n---\\n` bytes。

    allow_unicode=True 让中文不转义; sort_keys=False 保用户字段顺序;
    width=10_000 防长行 description 被折成多行。
    """
    yaml_bytes = yaml.safe_dump(
        fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10_000
    ).encode("utf-8")
    # yaml 输出末尾自带 \\n; 我们拼 `---\\n<yaml>---\\n`(yaml 后 \\n 即边界):
    return b"---\n" + yaml_bytes + b"---\n"


@dataclass
class EmitterResult:
    """emitter 一次 emit 的结果(给 manifest + CLI 展示用)。"""

    deployed_path: Path
    method: str             # cp | ln | skipped
    note: str = ""          # 跳过/警告原因(file_size_max 超 / Agent 不在 machines 列表 等)


class BaseEmitter(ABC):
    """所有 Agent emitter 继承此基类。

    子类须实现:
        transform_frontmatter(ir, cfg) -> dict
        deploy(ir, deploy_root, cfg) -> EmitterResult

    base 提供:
        build_skill_md_bytes(ir, cfg, prompt_bytes=b"") -> bytes   最终拼字节流
        write_skill_md(bytes, path)        普通文件写入
        write_resources(ir, target_skill_dir)    resources/ 拷贝
        symlink_skill_dir(canonical_dir, target_skill_dir)  ZCode 等用
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @abstractmethod
    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict:
        """重排 frontmatter 字段为该 Agent 兼容子集(关键:去除 canonical 不该污染 Agent 的字段)。"""
        ...

    @abstractmethod
    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path, prompt_bytes: bytes = b"",
    ) -> EmitterResult:
        """把 IR + 前言写到目标 Agent 目录的对应位置(cp/ln)。"""
        ...

    # --- 公共 helper ---

    def build_skill_md_bytes(self, ir: SkillIR, cfg: AgentConfig, prompt_bytes: bytes = b"") -> bytes:
        """frontmatter block + body 顶前言 + body 拼字节流。

        body bytes 不动; 前言拼在 frontmatter 之后、body 之前。
        """
        fm = self.transform_frontmatter(ir, cfg)
        return emit_frontmatter_block(fm) + prompt_bytes + ir.body

    @staticmethod
    def write_skill_md(content: bytes, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    @staticmethod
    def write_resources(ir: SkillIR, target_skill_dir: Path, canonical_skill_dir: Path) -> None:
        """resources/ 拷过去。canonical_skill_dir 是 skills/<name>/, 里面有 resources/。

        最终结构: target_skill_dir/SKILL.md + target_skill_dir/resources/...
        M0 还没有真实 skill, M2 实测真 skill 时启用。
        """
        src_res = canonical_skill_dir / "resources"
        if not src_res.exists():
            return
        # 跳过已有目标先把 resources 重建(防残留旧文件)
        dst_res = target_skill_dir / "resources"
        if dst_res.exists():
            shutil.rmtree(dst_res)
        shutil.copytree(src_res, dst_res)

    @staticmethod
    def symlink_skill_dir(canonical_skill_dir: Path, target_skill_dir: Path) -> None:
        """target_skill_dir 软链到 canonical_skill_dir(ZCode 等用)。

        若 target 已是软链/文件, unlink 再 ln; 若是真实目录(M4 清理既有真实副本 archify 等),
        由 caller 决定先备份, emitter 不动用户真实副本(决策: emitter 只对 manifest 管的 skill 操作)。
        """
        if target_skill_dir.is_symlink() or target_skill_dir.exists():
            target_skill_dir.unlink()
        target_skill_dir.parent.mkdir(parents=True, exist_ok=True)
        target_skill_dir.symlink_to(canonical_skill_dir.resolve())