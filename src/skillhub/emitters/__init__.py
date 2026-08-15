"""SkillHub emitters — SkillIR → 各 Agent 目录的 SKILL.md(+ 资源)。

canonical.py — 写回中央仓 canonical 格式(回环测试 + add/import 落地)
各 Agent emitter: claudecode / zcode / qwenworkcn / teleagent / hermes / codex / kimi

EMITTERS 注册表: agent 名(agents.toml/machines.toml 的键) → emitter 类。
"""

from skillhub.emitters.base import BaseEmitter, EmitterResult
from skillhub.emitters.canonical import emit_canonical
from skillhub.emitters.claudecode import ClaudeCodeEmitter
from skillhub.emitters.codex import CodexEmitter
from skillhub.emitters.hermes import HermesEmitter
from skillhub.emitters.kimi import KimiEmitter
from skillhub.emitters.qwenworkcn import QwenWorkCNEmitter
from skillhub.emitters.teleagent import TeleAgentEmitter
from skillhub.emitters.zcode import ZCodeEmitter

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
