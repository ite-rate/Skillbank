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
- install_dir (仅文档参考! 部署路径唯一真相源是 machines.toml 的手填 skills_dir)
      / level 映射 / description_max / file_size_max / default_category / note

    全部 Agent 一律 cp 部署(7 个 emitter 均硬编码 cp; method 字段已删)。
    双语字段镜像(_zh <-> _cn)在对应 emitter 里硬编码, 不走配置。

    2026-08-15 决策:删除 resolve_install_dir(home 展开)。
    实测同一 Agent 跨机器路径不保证一致(QwenWorkCN), 显式手填 machines.toml 最稳;
    此处 install_dir 保留仅为 README 表格/文档参考, 代码不消费。
    """

    name: str
    display_name: str
    install_dir: str            # 仅文档参考, 部署不用它
    disable_invoke_field: Optional[str] = None
    disable_invoke_value: object = None
    description_max: Optional[int] = None
    file_size_max: Optional[int] = None
    default_category: Optional[str] = None
    skills_dir_config_key: Optional[str] = None
    note: str = ""

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
                disable_invoke_field=body.get("disable_invoke_field"),
                disable_invoke_value=body.get("disable_invoke_value"),
                description_max=body.get("description_max"),
                file_size_max=body.get("file_size_max"),
                default_category=body.get("default_category"),
                skills_dir_config_key=body.get("skills_dir_config_key"),
                note=body.get("note", ""),
            )
        return cls(agents=agents)

    def get(self, name: str) -> AgentConfig:
        return self.agents[name]