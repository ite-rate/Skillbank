"""CapabilityMatrix — capabilities.toml 加载 + 查询 + 推荐 Agent。

对 emitter 暴露三个查询能力:
- query(capability_tag, agent_name) -> state_str
- recommend_agents(capability_tag, exclude=...) -> list[agent_name]
- recommendation_skips(agent, requires) -> (missing, unknown)
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

__all__ = ["CapabilityMatrix", "CapabilityState"]


class CapabilityState:
    """与 capabilities.toml 中的四态对应(字符串)。"""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    PARTIAL = "partial"


@dataclass
class CapabilityMatrix:
    """capabilities.toml 驻内存视图。"""

    tags: list[str]
    agents: dict[str, dict[str, str]]

    @classmethod
    def load(cls, toml_path: Path) -> "CapabilityMatrix":
        with open(toml_path, "rb") as fh:
            d = tomllib.load(fh)
        tags = list(d["capability_tags"])
        agents = {}
        for agent_name, agent_def in d["agents"].items():
            agents[agent_name] = {
                t: agent_def.get(t, CapabilityState.UNKNOWN)
                for t in tags
            }
        return cls(tags=tags, agents=agents)

    def query(self, tag: str, agent: str) -> str:
        if tag not in self.tags:
            return CapabilityState.UNKNOWN
        return self.agents.get(agent, {}).get(tag, CapabilityState.UNKNOWN)

    def recommend_agents(self, tag: str, exclude: Optional[str] = None) -> list[str]:
        out: list[str] = []
        for agent_name, caps in self.agents.items():
            if agent_name == exclude:
                continue
            if caps.get(tag) == CapabilityState.SUPPORTED:
                out.append(agent_name)
        return out

    def recommendation_skips(self, agent: str, requires: Iterable[str]) -> tuple[list[str], list[str]]:
        missing = [c for c in requires if self.query(c, agent) == CapabilityState.UNSUPPORTED]
        unknown = [c for c in requires if self.query(c, agent) == CapabilityState.UNKNOWN]
        return missing, unknown