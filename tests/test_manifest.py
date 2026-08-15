"""M5 — DeploymentsManifest + 删除链测试。

覆盖:
- load/save 往返 + 原子写 + version 校验
- upsert 按 (skill,machine,agent) 替换
- delete_local: cp 目录删 / 软链 unlink(不动链接目标) / 已消失容错
- mark_pending_deletion: except_machine 语义
- process_pending_deletions: 另一台机器 sync 时执行 pending
- 用户手放/内置 skill(不在 manifest)不被触碰 — 删除链只动 manifest 记录的路径
- check_consistency 对账
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skillhub.manifest import MANIFEST_VERSION, DeployRecord, DeploymentsManifest


def _rec(skill="demo", machine="mac-main", agent="ClaudeCode", deploy_path="",
         method="cp", pending=False, ir_hash="sha256:abc") -> DeployRecord:
    return DeployRecord(
        skill=skill, machine=machine, agent=agent,
        deploy_path=deploy_path or "/tmp/nonexistent/demo",
        method=method, ir_hash=ir_hash, pending_deletion=pending,
    )


# --- load / save ---


def test_manifest_save_load_roundtrip(tmp_path):
    m = DeploymentsManifest(path=tmp_path / "deployments.json")
    # 造一个真实文件路径让 consistency 不吵
    skill_dir = tmp_path / "agents" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(b"---\nname: demo\n---\nbody\n")
    m.upsert(DeployRecord(
        skill="demo", machine="mac-main", agent="ClaudeCode",
        deploy_path=str(skill_dir / "SKILL.md"), method="cp", ir_hash="sha256:x",
    ))
    m.save()

    m2 = DeploymentsManifest.load(tmp_path / "deployments.json")
    assert len(m2.records) == 1
    r = m2.records[0]
    assert r.skill == "demo" and r.machine == "mac-main" and r.agent == "ClaudeCode"
    assert r.method == "cp" and r.ir_hash == "sha256:x"
    assert r.deployed_at  # 自动填了时间戳
    # 文件头是 version 字段
    d = json.loads((tmp_path / "deployments.json").read_text())
    assert d["version"] == MANIFEST_VERSION


def test_manifest_load_missing_file_returns_empty(tmp_path):
    m = DeploymentsManifest.load(tmp_path / "nope.json")
    assert m.records == []
    assert m.path == tmp_path / "nope.json"


def test_manifest_load_bad_version_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"version": 99, "records": []}))
    with pytest.raises(ValueError, match="version"):
        DeploymentsManifest.load(p)


def test_manifest_save_atomic_no_tmp_left(tmp_path):
    m = DeploymentsManifest(path=tmp_path / "d.json")
    m.upsert(_rec(deploy_path=str(tmp_path / "x")))
    m.save()
    assert not (tmp_path / "d.tmp").exists()
    assert not list(tmp_path.glob("*.tmp")), "原子写不应留 tmp 文件"


# --- upsert ---


def test_upsert_same_key_replaces(tmp_path):
    m = DeploymentsManifest()
    m.upsert(_rec(ir_hash="sha256:old"))
    m.upsert(_rec(ir_hash="sha256:new"))
    assert len(m.records) == 1
    assert m.records[0].ir_hash == "sha256:new"


def test_upsert_different_keys_append(tmp_path):
    m = DeploymentsManifest()
    m.upsert(_rec(agent="ClaudeCode"))
    m.upsert(_rec(agent="Codex"))
    m.upsert(_rec(machine="laptop", agent="ClaudeCode"))
    assert len(m.records) == 3


# --- delete_local ---


def test_delete_local_removes_cp_dir_and_record(tmp_path):
    """cp 记录:deploy_path 指向 <dir>/SKILL.md -> 删整个 skill 目录 + 清记录。"""
    skill_dir = tmp_path / "claude-skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(b"body")

    m = DeploymentsManifest()
    m.upsert(DeployRecord(
        skill="demo", machine="mac-main", agent="ClaudeCode",
        deploy_path=str(skill_dir / "SKILL.md"), method="cp",
    ))
    actions = m.delete_local("demo", "mac-main")
    assert any("deleted" in a for a in actions), actions
    assert not skill_dir.exists(), "cp 的 skill 目录应被删"
    assert m.find("demo") == [], "记录应清"


def test_delete_local_unlinks_symlink_not_target(tmp_path):
    """ln 记录(ZCode):删软链本身,链接目标(canonical)必须完好。"""
    canonical = tmp_path / "SkillHub" / "skills" / "demo"
    canonical.mkdir(parents=True)
    (canonical / "SKILL.md").write_bytes(b"canonical body")

    zcode_skills = tmp_path / "zcode-skills"
    zcode_skills.mkdir()
    link = zcode_skills / "demo"
    link.symlink_to(canonical.resolve())

    m = DeploymentsManifest()
    m.upsert(DeployRecord(
        skill="demo", machine="mac-main", agent="ZCode",
        deploy_path=str(link), method="ln",
    ))
    actions = m.delete_local("demo", "mac-main")
    assert any("unlinked" in a for a in actions), actions
    assert not link.exists() and not link.is_symlink(), "软链应被删"
    assert canonical.exists() and (canonical / "SKILL.md").read_bytes() == b"canonical body", \
        "canonical 目标绝不能被删除链碰到"


def test_delete_local_missing_path_tolerated(tmp_path):
    m = DeploymentsManifest()
    m.upsert(DeployRecord(
        skill="ghost", machine="mac-main", agent="Codex",
        deploy_path=str(tmp_path / "gone" / "SKILL.md"), method="cp",
    ))
    actions = m.delete_local("ghost", "mac-main")
    assert any("already gone" in a for a in actions), actions
    assert m.find("ghost") == []


def test_delete_local_dry_run_no_touch(tmp_path):
    skill_dir = tmp_path / "s" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(b"b")
    m = DeploymentsManifest()
    m.upsert(DeployRecord(
        skill="demo", machine="mac-main", agent="ClaudeCode",
        deploy_path=str(skill_dir / "SKILL.md"), method="cp",
    ))
    actions = m.delete_local("demo", "mac-main", dry_run=True)
    assert any("WOULD DELETE" in a for a in actions)
    assert skill_dir.exists(), "dry_run 不应动盘"
    assert len(m.find("demo")) == 1, "dry_run 不应清记录"


def test_user_placed_skill_never_touched(tmp_path):
    """删除链只动 manifest 记录的路径;同目录用户手放的 skill 不受影响。"""
    shared_root = tmp_path / "claude-skills"
    managed = shared_root / "managed-skill"
    user_placed = shared_root / "user-skill"
    managed.mkdir(parents=True)
    user_placed.mkdir()
    (managed / "SKILL.md").write_bytes(b"m")
    (user_placed / "SKILL.md").write_bytes(b"u")

    m = DeploymentsManifest()
    m.upsert(DeployRecord(
        skill="managed-skill", machine="mac-main", agent="ClaudeCode",
        deploy_path=str(managed / "SKILL.md"), method="cp",
    ))
    m.delete_local("managed-skill", "mac-main")
    assert not managed.exists()
    assert user_placed.exists() and (user_placed / "SKILL.md").read_bytes() == b"u", \
        "用户手放 skill 必须原封不动"


# --- pending_deletion 跨机 ---


def test_mark_pending_deletion_except_local(tmp_path):
    m = DeploymentsManifest()
    m.upsert(_rec(skill="demo", machine="mac-main", agent="ClaudeCode", deploy_path="/tmp/a"))
    m.upsert(_rec(skill="demo", machine="laptop", agent="ClaudeCode", deploy_path="/tmp/b"))
    m.upsert(_rec(skill="demo", machine="remote", agent="Codex", deploy_path="/tmp/c"))
    n = m.mark_pending_deletion("demo", except_machine="mac-main")
    assert n == 2
    assert m.find("demo", machine="mac-main")[0].pending_deletion is False
    assert m.find("demo", machine="laptop")[0].pending_deletion is True
    assert m.find("demo", machine="remote")[0].pending_deletion is True


def test_process_pending_deletions_on_laptop(tmp_path):
    """laptop sync 时执行 pending:删 laptop 盘上的, mac-main 的不动。"""
    mac_dir = tmp_path / "mac" / "demo"; mac_dir.mkdir(parents=True)
    (mac_dir / "SKILL.md").write_bytes(b"m")
    laptop_dir = tmp_path / "laptop" / "demo"; laptop_dir.mkdir(parents=True)
    (laptop_dir / "SKILL.md").write_bytes(b"l")

    m = DeploymentsManifest()
    m.upsert(DeployRecord(skill="demo", machine="mac-main", agent="ClaudeCode",
                          deploy_path=str(mac_dir / "SKILL.md"), method="cp"))
    r = DeployRecord(skill="demo", machine="laptop", agent="ClaudeCode",
                     deploy_path=str(laptop_dir / "SKILL.md"), method="cp")
    r.pending_deletion = True
    m.upsert(r)

    actions = m.process_pending_deletions("laptop")
    assert any("pending" in a for a in actions), actions
    assert not laptop_dir.exists(), "laptop 的 pending 副本应被删"
    assert mac_dir.exists(), "mac-main(非 pending, 且不在本机)不应被动"
    assert m.find("demo", machine="laptop") == []
    assert len(m.find("demo", machine="mac-main")) == 1


# --- consistency ---


def test_check_consistency_finds_missing_on_disk(tmp_path):
    m = DeploymentsManifest()
    m.upsert(DeployRecord(skill="demo", machine="mac-main", agent="ClaudeCode",
                          deploy_path=str(tmp_path / "missing" / "SKILL.md"), method="cp"))
    issues = m.check_consistency()
    assert any("missing on disk" in i for i in issues)


def test_check_consistency_finds_duplicates(tmp_path):
    p = tmp_path / "d" / "SKILL.md"
    p.parent.mkdir()
    p.write_bytes(b"b")
    m = DeploymentsManifest()
    m.upsert(DeployRecord(skill="demo", machine="mac-main", agent="ClaudeCode",
                          deploy_path=str(p), method="cp"))
    # 手动注入重复(绕过 upsert 的替换语义)
    m.records.append(m.records[0])
    issues = m.check_consistency()
    assert any("duplicate" in i for i in issues)
