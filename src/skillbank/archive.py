"""Archive 机制 — 长时间不用但未来可能用的 skill 归档/恢复。

归档 = mv skills/<name>/ → skills/.archive/<name>/ + 清已部署副本 + manifest 标记。
  - sync 不扫 .archive/(不部署)
  - list 默认不显示归档; --archived 看清单
  - canonical 仍在 git 里(100% 可恢复)
  - 未来用: skillbank unarchive <name> → 移回 skills/ + set-level manual

与 disable 的区别:
  disable: skill 仍在 skills/ 里, list 显示, sync 不推但可见 — "出了问题被下架"
  archive: skill 移到 .archive/, list 默认不显示 — "暂存将来可能用"
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from skillbank.manifest import DeploymentsManifest

__all__ = ["archive_skill", "unarchive_skill", "list_archived", "ARCHIVE_DIR"]

ARCHIVE_DIR_NAME = ".archive"


def _archive_root(repo_root: Path) -> Path:
    return Path(repo_root) / "skills" / ARCHIVE_DIR_NAME


def _skill_exists(repo_root: Path, name: str) -> bool:
    return (Path(repo_root) / "skills" / name / "SKILL.md").exists()


def _archived_exists(repo_root: Path, name: str) -> bool:
    return (_archive_root(repo_root) / name / "SKILL.md").exists()


def archive_skill(
    repo_root: Path,
    name: str,
    manifest: Optional[DeploymentsManifest] = None,
    *, machine: str,
) -> str:
    """归档 skill: mv 到 .archive/ + 清已部署副本。

    返回人话结果描述。
    """
    repo_root = Path(repo_root)
    if not _skill_exists(repo_root, name):
        if _archived_exists(repo_root, name):
            return f"already archived: {name}"
        return f"canonical 不存在: skills/{name}/"

    src = repo_root / "skills" / name
    dst_dir = _archive_root(repo_root)
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / name

    if dst.exists():
        # 归档区已有同名(可能旧归档残留), 覆盖
        shutil.rmtree(dst)

    shutil.move(str(src), str(dst))

    # 清已部署副本(走 manifest 删除链)
    notes = []
    if manifest is not None:
        actions = manifest.delete_local(name, machine)
        if actions:
            notes.append(f"清本机副本 {len(actions)} 个")
        n_pending = manifest.mark_pending_deletion(name, except_machine=machine)
        if n_pending:
            notes.append(f"其它机器 {n_pending} 个标 pending")
        manifest.save()

    return f"已归档 {name} → skills/.archive/{name}" + (f"({', '.join(notes)})" if notes else "")


def unarchive_skill(repo_root: Path, name: str) -> str:
    """恢复归档 skill: mv 回 skills/ + set-level manual(默认不自动触发)。

    返回人话结果描述。
    """
    import re
    import yaml

    from skillbank.emitters.canonical import emit_canonical
    from skillbank.ir import Level
    from skillbank.parsers.canonical import parse_canonical

    repo_root = Path(repo_root)
    if not _archived_exists(repo_root, name):
        return f"归档区不存在: skills/.archive/{name}/"

    src = _archive_root(repo_root) / name
    dst = repo_root / "skills" / name

    if dst.exists():
        return f"skills/{name}/ 已存在(同名冲突, 先 rm 或 rename 再 unarchive)"

    shutil.move(str(src), str(dst))

    # set-level manual(恢复后默认不自动触发, 你审过再改 auto)
    skill_md = dst / "SKILL.md"
    ir = parse_canonical(skill_md)
    if ir.level != Level.MANUAL:
        old = ir.level.value
        ir.level = Level.MANUAL
        emit_canonical(ir, skill_md)
        return f"已恢复 {name} ← .archive, level: {old} → manual(审过再 set-level auto)"
    return f"已恢复 {name} ← .archive(level 已是 manual)"


def list_archived(repo_root: Path) -> list[str]:
    """归档区 skill 名列表。"""
    root = _archive_root(repo_root)
    if not root.exists():
        return []
    return sorted(
        d.name for d in root.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    )