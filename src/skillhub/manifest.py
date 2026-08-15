"""Deployments manifest — manifests/deployments.json 读写 + 删除链。

schema v1:
{
  "version": 1,
  "records": [
    {
      "skill": "canvas-design",
      "machine": "mac-main",
      "agent": "TeleAgent",
      "deploy_path": "/Users/ss/.config/TeleAgent/skills/canvas-design",  # 绝对路径(已按 machine home 展开)
      "deployed_at": "2026-08-15T02:00:00Z",
      "method": "cp",                       # cp | ln
      "ir_hash": "sha256:...",              # body hash(零损耗跨机验证)
      "note": "description truncated ...",  # emitter note(可空)
      "pending_deletion": false             # 跨机删除标记: true = 等那台机器下次 sync 时删
    }
  ]
}

删除链(决策 5/6):
1. skillhub rm <name> / skill 改 level=disable:
   - 本机 manifest 记录的 deploy_path -> 直接删(只删 manifest 记录的; 用户手放/内置不碰)
   - 其它机器的记录 -> pending_deletion=true, 那台机器下次 sync 时执行删除并清记录
2. skill 从 manifest 消失后, canonical 仍保留(disable 时), git 里可恢复

设计:纯 json 标准库,无第三方依赖;原子写(tmp + os.replace)防写坏。
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__all__ = ["DeployRecord", "DeploymentsManifest", "MANIFEST_VERSION"]

MANIFEST_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class DeployRecord:
    skill: str
    machine: str
    agent: str
    deploy_path: str            # 绝对路径(emitter 落盘时展开)
    deployed_at: str = ""       # ISO8601 UTC
    method: str = "cp"          # cp | ln | skipped 不入 manifest(skipped 没部署)
    ir_hash: str = ""           # body sha256(跨机零损耗验证)
    note: str = ""
    pending_deletion: bool = False

    def key(self) -> tuple[str, str, str]:
        """(skill, machine, agent) 唯一键。"""
        return (self.skill, self.machine, self.agent)


@dataclass
class DeploymentsManifest:
    records: list[DeployRecord] = field(default_factory=list)
    path: Optional[Path] = None   # 落盘位置;None = 内存态(测试用)

    # --- load / save ---

    @classmethod
    def load(cls, path: Path) -> "DeploymentsManifest":
        p = Path(path)
        if not p.exists():
            return cls(records=[], path=p)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        if d.get("version") != MANIFEST_VERSION:
            raise ValueError(f"manifest version {d.get('version')!r} != supported {MANIFEST_VERSION}: {p}")
        records = [DeployRecord(**r) for r in d.get("records", [])]
        return cls(records=records, path=p)

    def save(self, path: Optional[Path] = None) -> None:
        """原子写(tmp + os.replace);不锁,单人编辑流足够。"""
        p = Path(path or self.path)
        if p is None:
            raise ValueError("no manifest path given")
        p.parent.mkdir(parents=True, exist_ok=True)
        d = {"version": MANIFEST_VERSION, "records": [asdict(r) for r in self.records]}
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, p)

    # --- 查询 ---

    def find(self, skill: str, machine: Optional[str] = None, agent: Optional[str] = None) -> list[DeployRecord]:
        out = []
        for r in self.records:
            if r.skill != skill:
                continue
            if machine is not None and r.machine != machine:
                continue
            if agent is not None and r.agent != agent:
                continue
            out.append(r)
        return out

    def skills(self) -> list[str]:
        seen, out = set(), []
        for r in self.records:
            if r.skill not in seen:
                seen.add(r.skill)
                out.append(r.skill)
        return out

    # --- 部署记录生命周期 ---

    def upsert(self, rec: DeployRecord) -> None:
        """按 (skill, machine, agent) 替换或追加。"""
        for i, r in enumerate(self.records):
            if r.key() == rec.key():
                self.records[i] = rec
                return
        if not rec.deployed_at:
            rec.deployed_at = _now_iso()
        self.records.append(rec)

    def remove_record(self, skill: str, machine: str, agent: str) -> Optional[DeployRecord]:
        """删记录(不删盘上文件);返回被删的 record 或 None。"""
        for i, r in enumerate(self.records):
            if r.key() == (skill, machine, agent):
                return self.records.pop(i)
        return None

    # --- 删除链 ---

    def mark_pending_deletion(self, skill: str, except_machine: Optional[str] = None) -> int:
        """rm/disable 时:其它机器的记录标 pending_deletion=true。

        本机(except_machine)的记录由 delete_local 直接处理,不标 pending。
        返回标记条数。
        """
        n = 0
        for r in self.records:
            if r.skill == skill and except_machine is not None and r.machine != except_machine:
                if not r.pending_deletion:
                    r.pending_deletion = True
                    n += 1
        return n

    def delete_local(self, skill: str, machine: str, dry_run: bool = False) -> list[str]:
        """删除链·本机段:删盘上 deploy_path + 清 manifest 记录。

        只删 manifest 记录的路径(用户手放/内置 skill 从不入库,天然不碰)。
        ln 记录取 deploy_path 父目录(软链整个 skill dir);cp 记录取 deploy_path 父目录
        (SKILL.md 在 <dir>/SKILL.md, 删整个 skill 目录)。
        dry_run=True 只报告不动盘。
        返回删除的动作描述列表。
        """
        actions: list[str] = []
        recs = self.find(skill, machine=machine)
        for r in recs:
            target = Path(r.deploy_path)
            # deploy_path 指向 <skill_dir>/SKILL.md(cp 类)或软链的 skill dir(ln 类);
            # 统一删 skill 目录本身:SKILL.md 的父目录 / 软链本身
            if target.name == "SKILL.md":
                target_dir = target.parent
            else:
                target_dir = target
            if dry_run:
                actions.append(f"WOULD DELETE {target_dir} ({r.agent}, {r.method})")
                continue  # dry_run 不动盘也不清记录
            if target_dir.is_symlink():
                target_dir.unlink()
                actions.append(f"unlinked {target_dir} ({r.agent}, {r.method})")
            elif target_dir.exists():
                shutil.rmtree(target_dir)
                actions.append(f"deleted {target_dir} ({r.agent}, {r.method})")
            else:
                actions.append(f"already gone {target_dir} ({r.agent}, {r.method})")
            self.remove_record(skill, machine, r.agent)
        return actions

    def process_pending_deletions(self, machine: str, dry_run: bool = False) -> list[str]:
        """删除链·跨机段:本机 sync 时执行别的机器标记来的 pending_deletion。

        删本机 deploy_path + 清记录。返回动作描述列表。
        """
        actions: list[str] = []
        for r in list(self.records):
            if r.pending_deletion and r.machine == machine:
                target = Path(r.deploy_path)
                target_dir = target.parent if target.name == "SKILL.md" else target
                if dry_run:
                    actions.append(f"WOULD DELETE(pending) {target_dir} ({r.agent})")
                    continue  # dry_run 不动盘也不清记录
                if target_dir.is_symlink():
                    target_dir.unlink()
                    actions.append(f"unlinked(pending) {target_dir} ({r.agent})")
                elif target_dir.exists():
                    shutil.rmtree(target_dir)
                    actions.append(f"deleted(pending) {target_dir} ({r.agent})")
                else:
                    actions.append(f"already gone(pending) {target_dir} ({r.agent})")
                self.remove_record(r.skill, r.machine, r.agent)
        return actions

    # --- 一致性检查(doctor 用) ---

    def check_consistency(self) -> list[str]:
        """盘上文件 vs manifest 记录对账;返回差异描述。"""
        issues = []
        seen_keys = set()
        for r in self.records:
            if r.key() in seen_keys:
                issues.append(f"duplicate record {r.key()}")
            seen_keys.add(r.key())
            target = Path(r.deploy_path)
            if not r.pending_deletion and not target.exists():
                issues.append(f"recorded but missing on disk: {r.deploy_path} ({r.skill}@{r.machine}/{r.agent})")
        return issues
