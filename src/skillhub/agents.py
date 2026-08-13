"""AgentConfig — agents.toml 加载 + per-agent 集成配置查询。"""

from __future__ import annotations

import dataclasses
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = ["AgentConfig", "AgentsConfig"]


@dataclass
class AgentConfig:
    """单个 Agent 的集成方式(对应 agents.toml 里 [agents.<name>])。

    字段语义见 agents.toml 注释:
- install_dir (~ 展开) / method (cp|ln) / level 映射
      / keep_native_fields / lang_duplication / description_max / file_size_max
      / default_category / skills_dir_config_key / note
    """

    name: str
    display_name: str
    install_dir: str            # 相对 home, e.g. "~/.claude/skills"
    method: str                 # cp | ln
    disable_invoke_field: Optional[str] = None
    disable_invoke_value: object = None
    keep_native_fields: list[str] = field(default_factory=list)
    lang_duplication: dict[str, list[str]] = field(default_factory=dict)
    description_max: Optional[int] = None
    file_size_max: Optional[int] = None
    default_category: Optional[str] = None
    skills_dir_config_key: Optional[str] = None
    note: str = ""

    def resolve_install_dir(self, home: str) -> Path:
        """按目标机器 home 把 ~/.xxx 展开成绝对路径。"""
        return Path(self.install_dir.replace("~", home, 1) if self.install_dir.startswith("~") else self.install_dir)

    def needs_disable_invoke(self, level_value: str) -> bool:
        """level == manual/experimental/disable 时, emitter 写出 disable_invoke_field"""
        return self.disable_invoke_field is not None and level_value in ("manual", "experimental", "disable")


@dataclass
class AgentsConfig:
    agents: dict[str, AgentConfig]

    @classmethod
    def load(cls, toml_path: Path) -> "AgentsConfig":
        with open(toml_path, "rb") as fh:
            d = tomllib.load(fh)
        agents = {}
        for name, body in d["agents"].items():
            agents[name] = AgentConfig(
                name=name,
                display_name=body.get("display_name", name),
                install_dir=body["install_dir"],
                method=body.get("method", "cp"),
                disable_invoke_field=body.get("disable_invoke_field"),
                disable_invoke_value=body.get("disable_invoke_value"),
                keep_native_fields=list(body.get("keep_native_fields", [])),
                lang_duplication=dict(body.get("lang_duplication", {})),
                description_max=body.get("description_max"),
                file_size_max=body.get("file_size_max"),
                default_category=body.get("default_category"),
                skills_dir_config_key=body.get("skills_dir_config_key"),
                note=body.get("note", ""),
            )
        return cls(agents=agents)

    def get(self, name: str) -> AgentConfig:
        return self.agents[name]