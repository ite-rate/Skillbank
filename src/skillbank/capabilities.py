"""CapabilityMatrix — capabilities.toml 加载 + 查询 + 推荐 Agent。

对 emitter/prompt_inject 暴露三个查询能力:
- query(capability_tag, agent_name) -> state_str
- recommend_agents(capability_tag, exclude=...) -> list[agent_name]   # 该能力 supported 的 agent
- recommendations_skip(agent, requires) -> 留给 M2 prompt_inject 用
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from skillbank.prompt_inject import CapabilityState

__all__ = ["CapabilityMatrix"]


@dataclass
class CapabilityMatrix:
    """capabilities.toml 驻内存视图。"""

    tags: list[str]
    agents: dict[str, dict[str, str]]   # {agent -> {cap_tag -> state_str}}, 含 evidence/note 等元字段

    @classmethod
    def load(cls, toml_path: Path) -> "CapabilityMatrix":
        with open(toml_path, "rb") as fh:
            d = tomllib.load(fh)
        tags = list(d["capability_tags"])
        agents = {}
        for agent_name, agent_def in d["agents"].items():
            # 仅保留能力标签项; evidence/note 等元字段 cap_lookup 不需(matrix 单值语义)
            agents[agent_name] = {
                t: agent_def.get(t, CapabilityState.UNKNOWN)
                for t in tags
            }
        return cls(tags=tags, agents=agents)

    def query(self, tag: str, agent: str) -> str:
        """该 Agent 对该能力的状态(默认 unknown, 不抛错; 双语/未知能力标签更不该崩 emitter)。"""
        if tag not in self.tags:
            return CapabilityState.UNKNOWN
        return self.agents.get(agent, {}).get(tag, CapabilityState.UNKNOWN)

    def recommend_agents(self, tag: str, exclude: Optional[str] = None) -> list[str]:
        """该能力 supported 的 Agent(排除 exclude) — UNSUPPORTED 硬警告里的"建议改用..."。

        partial 不建议(因为支持不完整); unknown 不建议(不编造)。
        """
        out: list[str] = []
        for agent_name, caps in self.agents.items():
            if agent_name == exclude:
                continue
            if caps.get(tag) == CapabilityState.SUPPORTED:
                out.append(agent_name)
        return out

    def recommendation_skips(self, agent: str, requires: Iterable[str]) -> tuple[list[str], list[str]]:
        """返回 (missing_caps, unknown_caps) — e.g. ([cap], []) 用于 caller 判断是否需注入。

        给 emitter 用的便捷 API, prompt_inject 也直接 query;二者解耦。
        """
        missing = [c for c in requires if self.query(c, agent) == CapabilityState.UNSUPPORTED]
        unknown = [c for c in requires if self.query(c, agent) == CapabilityState.UNKNOWN]
        return missing, unknown