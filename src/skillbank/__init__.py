"""Skillbank: central skill repository syncing canonical SKILL.md to 7 AI agents.

pipeline:
    canonical SKILL.md (skills/<name>/SKILL.md)
        -> parser -> SkillIR (dataclass; body kept as bytes for zero-loss)
            -> emitter (per Agent) -> deployed copy on target machine

hard constraint: body is bytes, byte-identical across parser/emitter roundtrip.
cross-machine sync via git pull (Mac main edit -> laptop periodic -> server manual).

see README.md / agents.toml / capabilities.toml / machines.toml.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]