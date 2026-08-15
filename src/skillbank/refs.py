"""统一资源统计 + body 引用一致性校验(P0 #15):

让 "skill 调 py 失败"这种 silent failure 在 SkillBank 层面可见。

- sync execute(): 部署后打印资源镜像统计 `(scripts/2, references/1, _meta.json)`
- doctor --skill <name>: 深 check body 里引用的路径(相对路径)在镜像目录是否对应文件存在

非 SkillBank 责任:LLM 真把 py 跑通(那是 skill 作者测试范畴);
SkillBank 责任:文件搬齐 + 告诉你引用与文件的对应一致性。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = ["resource_stats", "check_body_refs", "BodyRefIssue"]

# body 里相对路径引用: 反引号/引号/( 后跟 <subdir>/<file>.<ext>
# 排除 https:// URL 和 ../ (后者 scan_body_paths 管)
_REL_REF_RE = re.compile(
    r"""
    (?:`|\"|'|\(|\$\{?SKILL_DIR\}?(?:/|\b))
    (?!https?://|\.\./)
    (
      (?:scripts|references|resources|templates|prompts|fonts|rooms|agents|protocol)/
      [A-Za-z0-9_./\-]+
      \.
      (?:json|jpeg|yml|yaml|toml|html|css|csv|ottf|jpeg|jpg|png|tsv|tsx|geojson|js|ts|md|txt|py|sh|ttf|ttf)  # noqa: E501 长后缀先于短后缀防 js|ts 抢 json
    )
    """,
    re.VERBOSE,
)
# 补充: SKILL_DIR 变量引用 "${SKILL_DIR}/scripts/foo.py" 也要识
_SKILL_DIR_REF_RE = re.compile(
    r"""
    \$(?:\{SKILL_DIR\}|SKILL_DIR)[/\\]+
    (
      (?:scripts|references|resources|templates|prompts|fonts|rooms|agents|protocol)/
      [A-Za-z0-9_./\-]+\.(?:json|jpeg|yml|yaml|toml|html|css|csv|ottf|jpg|png|tsv|tsx|js|ts|md|txt|py|sh|ttf)
    )
    """,
    re.VERBOSE,
)


def _iter_files(p: Path):
    """递归 yield 所有文件(含软链)。"""
    for e in p.iterdir():
        if e.is_symlink():
            yield e
        elif e.is_dir():
            yield from _iter_files(e)
        else:
            yield e


def resource_stats(deployed_skill_dir: Path) -> str:
    """deployed 后目录里的资源构成人话统计。空返 ""。"""
    d = Path(deployed_skill_dir)
    if not d.exists():
        return ""
    items = [e for e in d.iterdir()
             if e.name not in {"SKILL.md", ".agent_overrides"} and not e.name.startswith(".")]
    if not items:
        return ""
    by_dir: dict[str, int] = {}
    misc_files = 0
    for e in items:
        if e.is_dir():
            n = sum(1 for _ in _iter_files(e))
            if n:
                by_dir[e.name] = n
        else:
            misc_files += 1
    parts = [f"{k}/{v}" for k, v in sorted(by_dir.items())]
    if misc_files:
        parts.append(f"files/{misc_files}")
    return ", ".join(parts)


@dataclass
class BodyRefIssue:
    """doctor --skill 细查时一条引用问题。"""
    severity: str          # "missing" | "ok"
    ref: str               # body 里找到的引用路径串
    detail: str            # 人话

    def __str__(self) -> str:
        mark = {"missing": "✗", "ok": "✓"}.get(self.severity, "·")
        return f"{mark} {self.ref}: {self.detail}"


def check_body_refs(body: bytes, skill_dir: Path) -> list[BodyRefIssue]:
    """check body 里相对路径引用的文件在 skill_dir 内是否存在(防 silent failure)。

    - 语意:body 写 `scripts/run.py`,_deployed skill_dir/scripts/run.py 不存在 → missing
    - 适用 canonical 与 deployed 副本(语义一致, 因为 emitter 镜像后结构相同)
    - 不报 ../ 和 https://(那些 scan_body_paths 已管 / URL 本就外部)
    """
    d = Path(skill_dir)
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return []
    issues: list[BodyRefIssue] = []
    seen_refs: set[str] = set()
    for rx in (_REL_REF_RE, _SKILL_DIR_REF_RE):
        for m in rx.finditer(text):
            ref = m.group(1)
            if ref in seen_refs:
                continue
            seen_refs.add(ref)
            target = d / ref
            if target.exists():
                issues.append(BodyRefIssue("ok", ref, "在镜像目录中存在"))
            else:
                issues.append(BodyRefIssue("missing", ref,
                                           f"在 skill 目录内找不到 {target}"))
    return issues