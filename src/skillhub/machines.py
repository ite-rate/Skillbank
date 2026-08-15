"""MachinesConfig — machines.toml 加载:每机器 × 每 Agent 手填完整路径。

决策(2026-08-15, 用户拍板):
- 显式手填完整绝对路径 > install_dir + home 展开(同一 Agent 跨机器路径不保证一致,
  实测 QwenWorkCN 在 Mac 是 ~/.qwenworkcn/, 换机器/版本就变)
- 不列某 Agent = 该机器没装 -> sync 跳过不报错(需求 4.6)
- agents.toml 的 install_dir 只是文档参考;代码路径解析唯一真相源是 machines.toml

load 时校验:机器里配的 agent 名必须在 agents.toml 存在(防拼写错),
路径必须以 / 开头(防有人写 ~ 相对路径)。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = ["AgentInstall", "MachineConfig", "MachinesConfig"]


@dataclass
class AgentInstall:
    skills_dir: str   # 完整绝对路径, 手填


@dataclass
class MachineConfig:
    name: str
    display_name: str
    agents: dict[str, AgentInstall] = field(default_factory=dict)

    def has_agent(self, agent: str) -> bool:
        return agent in self.agents


@dataclass
class MachinesConfig:
    machines: dict[str, MachineConfig] = field(default_factory=dict)

    @classmethod
    def load(
        cls, toml_path: Path, known_agents: Optional[set[str]] = None
    ) -> "MachinesConfig":
        """加载并校验。

        known_agents: agents.toml 里的 agent 名集合;给定时校验本文件里配的
        agent 名都在其中(拼写错早暴露)。
        """
        with open(toml_path, "rb") as fh:
            d = tomllib.load(fh)

        machines: dict[str, MachineConfig] = {}
        for m_name, m_body in d.get("machines", {}).items():
            agents: dict[str, AgentInstall] = {}
            for a_name, a_body in (m_body.get("agents", {}) or {}).items():
                if known_agents is not None and a_name not in known_agents:
                    raise ValueError(
                        f"machines.toml: machine {m_name!r} 配了未知 agent {a_name!r} "
                        f"(不在 agents.toml;检查拼写)"
                    )
                skills_dir = a_body["skills_dir"]
                if not skills_dir.startswith("/"):
                    raise ValueError(
                        f"machines.toml: {m_name}.{a_name}.skills_dir 必须是完整绝对路径"
                        f"(以 / 开头, 不支持 ~), got {skills_dir!r}"
                    )
                agents[a_name] = AgentInstall(skills_dir=skills_dir)
            machines[m_name] = MachineConfig(
                name=m_name,
                display_name=m_body.get("display_name", m_name),
                agents=agents,
            )
        return cls(machines=machines)

    # --- 查询 ---

    def get_machine(self, machine: str) -> MachineConfig:
        if machine not in self.machines:
            raise KeyError(
                f"machine {machine!r} 不在 machines.toml(可用: {sorted(self.machines)})"
            )
        return self.machines[machine]

    def get_skills_dir(self, machine: str, agent: str) -> Optional[Path]:
        """该机器上该 Agent 的 skills 目录绝对路径;没配 = None(没装, 跳过)。"""
        m = self.machines.get(machine)
        if m is None or agent not in m.agents:
            return None
        return Path(m.agents[agent].skills_dir)

    def machines_with_agent(self, agent: str) -> list[str]:
        return [name for name, m in self.machines.items() if agent in m.agents]

    def check_paths_exist(self, machine: str) -> tuple[list[str], list[str]]:
        """doctor 用:该机器配置的所有 skills_dir 盘上存在性。

        返回 (errors, warnings):
        - error:  skills_dir 连父目录都没有 → Agent 大概率没装或路径填错
        - warning: skills_dir 不存在但父目录在 → 正常(如 kimi 还没装过 skill,
                   目录惰性未建, emitter 部署时 mkdir 自动创建)
        """
        m = self.get_machine(machine)
        errors: list[str] = []
        warnings: list[str] = []
        for a_name, inst in m.agents.items():
            p = Path(inst.skills_dir)
            if p.exists():
                continue
            if p.parent.exists():
                warnings.append(f"{a_name}: {p} 尚不存在(从未部署过? emitter 会自动创建)")
            else:
                errors.append(f"{a_name}: {p} 父目录都不存在(Agent 没装? 路径填错?)")
        return errors, warnings
