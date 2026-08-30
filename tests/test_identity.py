"""Identity(本机身份绑定)测试 — .skillbank-machine 读写 + resolve_machine 语义。

- binding 写/读回环(含空文件、尾随换行)
- resolve:显式 flag 优先 / 绑定生效 / 未绑定报错(含 use/scan 指引)/ 绑定过期报错
- CLI `use` 绑定(猴补 REPO_ROOT 到假 repo, 不动真 repo)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skillbank.agents import AgentsConfig
from skillbank.identity import (BINDING_FILENAME, binding_path, read_binding,
                                resolve_machine, write_binding)
from skillbank.machines import MachinesConfig

REPO_ROOT = Path(__file__).resolve().parents[1]


def _machines(*names: str) -> MachinesConfig:
    m = MachinesConfig()
    for name in names:
        m.set_skills_dir(name, "ClaudeCode", f"/tmp/nowhere-{name}/skills")
    return m


# --- binding 读写回环 ---


def test_binding_roundtrip(tmp_path):
    p = write_binding(tmp_path, "laptop")
    assert p == binding_path(tmp_path)
    assert p.name == BINDING_FILENAME
    assert p.read_text() == "laptop\n"
    assert read_binding(tmp_path) == "laptop"


def test_binding_overwrite_and_strip(tmp_path):
    write_binding(tmp_path, "m1")
    write_binding(tmp_path, "  m2  ")
    assert read_binding(tmp_path) == "m2"


def test_binding_missing_or_empty(tmp_path):
    assert read_binding(tmp_path) is None
    binding_path(tmp_path).write_text("\n")
    assert read_binding(tmp_path) is None


# --- resolve_machine ---


def test_resolve_explicit_wins_without_binding(tmp_path):
    """未绑定但显式传 machine 的命令可用(旧行为保留)。"""
    assert resolve_machine(tmp_path, _machines("m1", "m2"), "m2") == "m2"


def test_resolve_explicit_unknown_machine_errors(tmp_path):
    with pytest.raises(ValueError, match="未知机器"):
        resolve_machine(tmp_path, _machines("m1"), "ghost")


def test_resolve_uses_binding(tmp_path):
    write_binding(tmp_path, "m1")
    assert resolve_machine(tmp_path, _machines("m1", "m2")) == "m1"


def test_resolve_unbound_gives_guidance(tmp_path):
    machines = _machines("m1", "m2")
    with pytest.raises(ValueError, match="skillbank use"):
        resolve_machine(tmp_path, machines)


def test_resolve_stale_binding_errors(tmp_path):
    write_binding(tmp_path, "gone")
    with pytest.raises(ValueError, match="不在 machines.toml"):
        resolve_machine(tmp_path, _machines("m1"))


# --- CLI: use 绑定 + list 用绑定默认值(猴补 REPO_ROOT, 不动真 repo) ---


@pytest.fixture
def fake_cli_repo(tmp_path, monkeypatch):
    """带最小 agents.toml/machines.toml/skills/ 的假 repo, 猴补 cli.REPO_ROOT。"""
    from skillbank import cli

    repo = tmp_path / "repo"
    (repo / "skills").mkdir(parents=True)
    (repo / "agents.toml").write_text(
        '[agents.ClaudeCode]\ninstall_dir = "~/.claude/skills"\n', encoding="utf-8")
    (repo / "machines.toml").write_text(
        "[machines.m1]\ndisplay_name = \"m1\"\n\n"
        "[machines.m1.agents.ClaudeCode]\nskills_dir = \"/tmp/nowhere-m1/skills\"\n",
        encoding="utf-8")
    monkeypatch.setattr(cli, "REPO_ROOT", repo)
    return repo


def test_cli_use_and_list_use_binding(fake_cli_repo, capsys):
    from skillbank import cli

    # 未绑定: list 拒绝执行并给指引
    with pytest.raises(SystemExit):
        cli.main(["list"])
    out = capsys.readouterr().out
    assert "skillbank use" in out

    # use 绑定 → 后续命令默认走 m1;list 空 manifest 但不再报错
    assert cli.main(["use", "m1"]) == 0
    assert (fake_cli_repo / BINDING_FILENAME).read_text() == "m1\n"
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "[list] machine=m1" in out

    # use 无参数 = 查看当前绑定
    assert cli.main(["use"]) == 0
    assert "当前绑定" in capsys.readouterr().out


def test_cli_use_unknown_machine(fake_cli_repo, capsys):
    from skillbank import cli

    assert cli.main(["use", "ghost"]) == 2
    assert "未知机器" in capsys.readouterr().out