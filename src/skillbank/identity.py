"""Identity — 本机身份绑定(这台 clone 所在的机器是谁)。

背景(2026-08-30, 修 #1):此前所有命令的 --machine 硬编码默认 "mac-main",
在另一台机器上裸跑 sync/rm 会按 mac-main 的 manifest 记录操作本机磁盘文件
(两台机器 home 相同时 deploy_path 撞车 → 删错机器上的副本)。

机制:repo 内 gitignored 文件 `.skillbank-machine` 存一行机器别名。
- 绑定动作:`skillbank use <别名>` 或 `skillbank scan --machine <别名>`
  (scan 天然只在目标机器本机跑, 跑 scan = 声明身份)
- 默认值解析:显式 flag > 绑定值;未绑定/绑定过期 → 报错 + 指引, 不静默回退
- 显式 flag ≠ 绑定值时, CLI 层对会动本机磁盘的命令打 ⚠ 警告(见 cli._resolve_machine)

文件格式当前是裸一行别名;hostname 交叉校验等 follow-up 留在此文件扩展。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from skillbank.machines import MachinesConfig

__all__ = ["BINDING_FILENAME", "binding_path", "read_binding", "write_binding",
           "resolve_machine"]

BINDING_FILENAME = ".skillbank-machine"


def binding_path(repo_root: Path) -> Path:
    return Path(repo_root) / BINDING_FILENAME


def read_binding(repo_root: Path) -> Optional[str]:
    """读本机绑定的机器别名;文件缺失/空 → None(未绑定)。"""
    p = binding_path(repo_root)
    try:
        raw = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return raw or None


def write_binding(repo_root: Path, alias: str) -> Path:
    """原子写绑定文件(空文件覆盖场景走 tmp+replace):返回绑定文件路径。"""
    p = binding_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(BINDING_FILENAME + ".tmp")
    tmp.write_text(alias.strip() + "\n", encoding="utf-8")
    os.replace(tmp, p)
    return p


def resolve_machine(
    repo_root: Path,
    machines: MachinesConfig,
    explicit: Optional[str] = None,
) -> str:
    """解析本次命令作用的 machine 别名。

    - explicit 传了:校验在 machines.toml 里后返回(flag 显式 > 绑定)
    - 否则读本机绑定:未绑定 / 绑定值已不在 machines.toml → ValueError(人话指引)
    """
    if explicit is not None:
        if explicit not in machines.machines:
            raise ValueError(
                f"未知机器 {explicit!r}(machines.toml: {sorted(machines.machines)});"
                f"先 `skillbank scan --machine <别名>` 注册"
            )
        return explicit

    bound = read_binding(repo_root)
    if bound is None:
        raise ValueError(
            "本机身份未绑定 — 拒绝按默认机器操作(防在别的机器上误动 mac-main 的记录)。"
            f"首次在本机使用: `skillbank use <别名>` 或 `skillbank scan --machine <别名>`"
            f"(可用: {sorted(machines.machines)})"
        )
    if bound not in machines.machines:
        raise ValueError(
            f"本机绑定 {bound!r} 已不在 machines.toml(过期/被删)。"
            f"重新绑定: `skillbank use <别名>` 或 `skillbank scan --machine <别名>`"
            f"(可用: {sorted(machines.machines)})"
        )
    return bound