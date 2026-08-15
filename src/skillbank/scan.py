"""Scan — 自动探测本机各 Agent 的 skills 目录, 供用户确认后写入 machines.toml。

探测信号分三级(按可信度):
  strong  : 目录存在且里面至少一个子目录有 SKILL.md("装了且在用, N 个 skill")
  medium  : 目录存在但没有任何 SKILL.md("空 skills 目录")
  weak    : 目录不存在但父目录存在("agent 装了, skills 目录还没建" — kimi 惰性目录这种)

候选路径来源: 三轮实地侦察的已知布局 + 通配变体(QwenWorkCN 历史路径多,
~/.qwen*/skills glob 兜底; 用户拍板过"qwen 的路径就很怪")。

设计约定: scan 只应在目标机器本机上跑(它探测的就是本机文件系统)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

__all__ = ["Candidate", "CANDIDATE_PATHS", "detect_agent", "detect_all", "pick_best"]


# 每 Agent 的候选路径(按优先级);~ 由传入的 home 展开
CANDIDATE_PATHS: dict[str, list[str]] = {
    "ClaudeCode": ["~/.claude/skills"],
    "ZCode": ["~/.zcode/skills"],
    "QwenWorkCN": [
        "~/.qwenworkcn/skills",       # Mac 实测布局
        "~/.qwen/skills",             # 文档口径 / 旧版
        "~/.qwenwork/skills",
        "~/.config/QwenWorkCN/skills",
    ],
    "TeleAgent": [
        "~/.config/TeleAgent/skills",  # Mac 实测布局
        "~/.teleagent/skills",
    ],
    "Hermes": ["~/.hermes/skills"],
    "Codex": ["~/.codex/skills"],
    "kimi-code": [
        "~/.kimi-code/skills",         # strings 实测默认 root
        "~/.kimi/skills",              # legacy
    ],
}

# glob 兜底: QwenWorkCN 路径历史杂, ~/.qwen*/skills 扫一遍
GLOB_PATTERNS: dict[str, list[str]] = {
    "QwenWorkCN": ["~/.qwen*/skills"],
}


@dataclass
class Candidate:
    agent: str
    path: Path
    confidence: str          # strong | medium | weak
    evidence: str            # 人话证据, 给确认提示用

    @property
    def rank(self) -> int:
        return {"strong": 0, "medium": 1, "weak": 2}.get(self.confidence, 3)


def _count_skills(dir_path: Path) -> int:
    """目录下含 SKILL.md 的子目录数。"""
    n = 0
    if not dir_path.is_dir():
        return 0
    for child in dir_path.iterdir():
        if child.is_dir() and (child / "SKILL.md").exists():
            n += 1
    return n


def _probe(agent: str, raw: str, home: Path) -> Optional[Candidate]:
    p = Path(raw.replace("~", str(home), 1)) if raw.startswith("~") else Path(raw)
    if p.exists():
        n = _count_skills(p)
        if n > 0:
            return Candidate(agent, p, "strong", f"找到 {n} 个 skill")
        return Candidate(agent, p, "medium", "目录存在但没有任何 SKILL.md")
    if p.parent.exists():
        return Candidate(agent, p, "weak", f"agent 装在 {p.parent}, skills 目录尚未创建")
    return None


def detect_agent(agent: str, home: Optional[Path] = None) -> list[Candidate]:
    """探测单个 Agent 的候选路径, 按可信度排序返回(可为空)。"""
    home = home or Path.home()
    found: list[Candidate] = []
    for raw in CANDIDATE_PATHS.get(agent, []):
        c = _probe(agent, raw, home)
        if c:
            found.append(c)
    for pat in GLOB_PATTERNS.get(agent, []):
        pat_full = pat.replace("~", str(home), 1)
        # 仅取 glob 命中且不在已知候选里的(去重)
        known = {
            Path(r.replace("~", str(home), 1)) for r in CANDIDATE_PATHS.get(agent, [])
        }
        for p in sorted(home.glob(pat_full.replace(str(home) + "/", "", 1))):
            if p not in known:
                c = _probe(agent, str(p), home)
                if c:
                    found.append(c)
    # strong > medium > weak;同级保候选顺序
    found.sort(key=lambda c: c.rank)
    return found


def detect_all(agent_names: list[str], home: Optional[Path] = None) -> dict[str, list[Candidate]]:
    return {a: detect_agent(a, home) for a in agent_names}


def pick_best(cands: list[Candidate]) -> Optional[Candidate]:
    """非交互模式取最优:strong > medium > weak,同级取第一个。"""
    return min(cands, key=lambda c: c.rank) if cands else None
