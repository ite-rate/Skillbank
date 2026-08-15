"""machines.toml 加载器测试 — 每机器×每 Agent 手填完整路径方案。

覆盖:
- 真实 machines.toml 能加载(含 mac-main 全 7 Agent)
- get_skills_dir 返回 Path;未配 agent 返回 None(skip 语义)
- get_machine 未知机器报 KeyError(可用列表提示)
- 校验:未知 agent 名(拼写错)raise;~ 相对路径 raise
- machines_with_agent 反查
- check_paths_exist:mac-main 的 7 个目录盘上真实存在(本机实测评测)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skillbank.agents import AgentsConfig
from skillbank.machines import MachinesConfig

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def agents_cfg() -> AgentsConfig:
    return AgentsConfig.load(REPO_ROOT / "agents.toml")


@pytest.fixture()
def machines(agents_cfg) -> MachinesConfig:
    return MachinesConfig.load(
        REPO_ROOT / "machines.toml", known_agents=set(agents_cfg.agents)
    )


def test_real_machines_toml_loads(machines):
    assert "mac-main" in machines.machines
    assert "laptop" in machines.machines
    assert "remote-server" in machines.machines


def test_mac_main_has_all_seven_agents(machines):
    mac = machines.get_machine("mac-main")
    expected = {"ClaudeCode", "ZCode", "QwenWorkCN", "TeleAgent", "Hermes", "Codex", "kimi-code"}
    assert set(mac.agents) == expected


def test_get_skills_dir_absolute_path(machines):
    p = machines.get_skills_dir("mac-main", "QwenWorkCN")
    assert p == Path("/Users/ss/.qwenworkcn/skills")
    assert p.is_absolute()


def test_unconfigured_agent_returns_none(machines):
    """laptop 没配 QwenWorkCN -> None(sync 时跳过, 不报错)。"""
    assert machines.get_skills_dir("laptop", "QwenWorkCN") is None
    assert machines.get_skills_dir("remote-server", "kimi-code") is None


def test_unknown_machine_raises_with_hint(machines):
    with pytest.raises(KeyError, match="mac-main"):
        machines.get_machine("no-such-machine")


def test_unknown_agent_name_rejected(tmp_path, agents_cfg):
    """machines.toml 配了 agents.toml 没有的 agent 名 -> 拼写错早暴露。"""
    bad = tmp_path / "machines.toml"
    bad.write_text(
        '[machines.m]\ndisplay_name = "m"\n'
        '[machines.m.agents.ClaudeCodee]\nskills_dir = "/x"\n'   # 拼错: 多个 e
    )
    with pytest.raises(ValueError, match="未知 agent"):
        MachinesConfig.load(bad, known_agents=set(agents_cfg.agents))


def test_relative_or_tilde_path_rejected(tmp_path, agents_cfg):
    """skills_dir 必须以 / 开头(手填完整路径, ~ 不支持)。"""
    for bad_dir in ["~/.claude/skills", "relative/skills"]:
        bad = tmp_path / "machines.toml"
        bad.write_text(
            f'[machines.m]\n[machines.m.agents.ClaudeCode]\nskills_dir = "{bad_dir}"\n'
        )
        with pytest.raises(ValueError, match="绝对路径"):
            MachinesConfig.load(bad, known_agents=set(agents_cfg.agents))


def test_machines_with_agent(machines):
    macs = machines.machines_with_agent("ClaudeCode")
    assert "mac-main" in macs and "laptop" in macs and "remote-server" in macs
    assert machines.machines_with_agent("QwenWorkCN") == ["mac-main"]


def test_mac_main_paths_exist_on_this_machine(machines):
    """本机(Mac 主力)实测:7 个手填路径无 error(配置与真实环境一致)。

    kimi-code 允许 warning:~/.kimi-code/skills 是惰性目录(kimi 还没装过 skill,
    emitter 首次部署时 mkdir 自动建);其余 6 个应盘上存在。
    """
    errors, warnings = machines.check_paths_exist("mac-main")
    assert errors == [], f"mac-main 路径配置与实际环境不符: {errors}"
    # 恰好只有 kimi-code 是 warning(实测现状), 其余 6 个既无 error 也无 warning
    assert all("kimi-code" in w for w in warnings), f"意外 warning: {warnings}"
