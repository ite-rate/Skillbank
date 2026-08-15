"""Skillbank emitters — SkillIR → 各 Agent 目录的 SKILL.md(+ 资源)。

canonical.py — 写回中央仓 canonical 格式(回环测试 + add/import 落地)
各 Agent emitter: claudecode / zcode / qwenworkcn / teleagent / hermes / codex / kimi

EMITTERS 注册表: agent 名(agents.toml/machines.toml 的键) → emitter 类。
"""

from skillbank.emitters.base import BaseEmitter, EmitterResult
from skillbank.emitters.canonical import emit_canonical
from skillbank.emitters.claudecode import ClaudeCodeEmitter
from skillbank.emitters.codex import CodexEmitter
from skillbank.emitters.hermes import HermesEmitter
from skillbank.emitters.kimi import KimiEmitter
from skillbank.emitters.qwenworkcn import QwenWorkCNEmitter
from skillbank.emitters.teleagent import TeleAgentEmitter
from skillbank.emitters.zcode import ZCodeEmitter

__all__ = [
    "emit_canonical",
    "BaseEmitter",
    "EmitterResult",
    "EMITTERS",
    "get_emitter",
]

EMITTERS: dict[str, type[BaseEmitter]] = {
    "ClaudeCode": ClaudeCodeEmitter,
    "ZCode": ZCodeEmitter,
    "QwenWorkCN": QwenWorkCNEmitter,
    "TeleAgent": TeleAgentEmitter,
    "Hermes": HermesEmitter,
    "Codex": CodexEmitter,
    "kimi-code": KimiEmitter,
}


def get_emitter(agent_name: str) -> BaseEmitter:
    if agent_name not in EMITTERS:
        raise KeyError(f"no emitter for agent {agent_name!r}(可用: {sorted(EMITTERS)})")
    return EMITTERS[agent_name]()
