"""SkillIR — intermediate representation for canonical SKILL.md.

设计要点:
- body: bytes (不是 str) — 零损耗硬约束。
  不做编码归一(防 \\r\\n -> \\n / BOM strip 等)。
  parser 切分 frontmatter 与 body 时, body 收 frontmatter 边界之后的所有原字节。
- frontmatter 字段: Level enum + 7 个稳定可选字段(canonical 标准 frontmatter 约束)。
- agent_overrides: 每个 Agent 专有字段副本(反向导入 Agent skill 时抽取)。
  canonical 不承载, emitter 用时按需取(从 skills/<name>/.agent_overrides/<agent>.toml)。
- requires: 能力标签列表, 跨切关注, 用于 prompt_inject。

往返零损耗的含义(roundtrip):
    parse(canonical) -> IR0
    IR0 -> emit_canonical -> bytes
    parse -> IR1
    断言 IR1.body == IR0.body (字节完全等值)
frontmatter 字段往返允许 dict 等值即可(序化格式可漂移, body 不漂移)。
"""

from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class Level(str, enum.Enum):
    """skill 分级(决策 4.4)。

    AUTO         稳定高频, 同步 + 允许模型自动触发
    MANUAL       稳定低频, 同步 + 禁止自动触发(转 disable-model-invocation / enabled_at:false)
    EXPERIMENTAL 实验中, 同步 + 禁止自动触发(同 manual)
    DISABLE      暂停, 不同步 + 清理已部署副本(canonical 保留以便恢复)
    """

    AUTO = "auto"
    MANUAL = "manual"
    EXPERIMENTAL = "experimental"
    DISABLE = "disable"

    def __str__(self) -> str:
        return self.value


@dataclass
class SkillIR:
    """Canonical SKILL.md 的语义化中间表示。

    body 是零损耗核心: parser/emitter 全程以 bytes 流转, 不 decode/encode。
    """

    name: str
    description: str
    body: bytes                                # 零损耗核心: bytes 不 str
    level: Level = Level.AUTO
    native_agent: Optional[str] = None         # 原生 Agent(决策: emitter 注入"原生于 X"前言)
    requires: list[str] = field(default_factory=list)   # 能力标签, 对 capabilities.toml
    description_zh: Optional[str] = None      # 双语 desc(canonical 共额外, emitter 镜像到 _cn/_zh)
    name_zh: Optional[str] = None             # 双语 name
    version: Optional[str] = None
    license: Optional[str] = None
    agent_overrides: dict[str, dict] = field(default_factory=dict)
    resources: list[Path] = field(default_factory=list)
    source_path: Optional[Path] = None         # parser 溯源(写 manifest 用)

    def body_hash(self) -> str:
        """body 的 sha256 — manifest ir_hash 字段用, 跨机器确认零损耗。"""
        return "sha256:" + hashlib.sha256(self.body).hexdigest()

    def level_allows_sync(self) -> bool:
        """disable 不参与同步, 只保留 canonical。"""
        return self.level != Level.DISABLE

    def level_allows_auto_trigger(self) -> bool:
        """manual/experimental/disable 都禁止模型自动触发(转 Agent frontmatter 字段)。"""
        return self.level == Level.AUTO

    def to_frontmatter_dict(self) -> dict:
        """canonical frontmatter 字段 dict(供 emitter 序化回 SKILL.md)。"""
        fm: dict = {"name": self.name, "description": self.description, "level": self.level.value}
        if self.native_agent is not None:
            fm["native_agent"] = self.native_agent
        if self.requires:
            fm["requires"] = list(self.requires)
        if self.description_zh is not None:
            fm["description_zh"] = self.description_zh
        if self.name_zh is not None:
            fm["name_zh"] = self.name_zh
        if self.version is not None:
            fm["version"] = self.version
        if self.license is not None:
            fm["license"] = self.license
        return fm

    @classmethod
    def from_frontmatter_dict(cls, fm: dict, body: bytes, source_path: Optional[Path] = None) -> "SkillIR":
        """从 canonical frontmatter dict + body bytes 构建 IR。

        允许 frontmatter 含未识别字段(留作 leftover, 不抛错)。
        """
        # required
        name = fm["name"]
        description = fm["description"]
        level = Level(fm.get("level", "auto"))
        return cls(
            name=name,
            description=description,
            body=body,
            level=level,
            native_agent=fm.get("native_agent"),
            requires=list(fm.get("requires") or []),
            description_zh=fm.get("description_zh"),
            name_zh=fm.get("name_zh"),
            version=fm.get("version"),
            license=fm.get("license"),
            source_path=source_path,
        )