"""M6 sync 引擎测试 — collect / show / execute 全链路。

用假 repo(skills/ + manifests/) + 内存 MachinesConfig(指向 tmp 目录)跑:
- deploy 新 skill: cp 落盘 + body 零损耗 + manifest 记录 + ir_hash
- 资源结构保真: scripts/ references/ 镜像到目标, body 相对路径有效
- keep: 同 hash 重跑标 keep
- disable skill: 计划出 delete(本机) + pending(它机), 执行后清副本/标 pending
- 孤儿记录(manifest 有 canonical 无): sync 自动清理
- Hermes 超限 skip + 旧记录清理
- ZCode: 真实目录 deferred(不写记录);干净目标 ln
- 未配置 Agent: 不出现在计划
- dry-run 语义由 CLI 层保证(collect/show 不落盘)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skillhub.agents import AgentsConfig
from skillhub.capabilities import CapabilityMatrix
from skillhub.emitters.canonical import emit_canonical
from skillhub.ir import Level, SkillIR
from skillhub.manifest import DeploymentsManifest
from skillhub.machines import MachinesConfig
from skillhub.sync import collect, execute, show_plan

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_canonical(repo: Path, name: str, body: bytes = b"## body\n",
                     level: str = "auto", native_agent: str | None = None,
                     requires: list[str] | None = None, resources: dict[str, str] | None = None,
                     description: str = "a skill") -> Path:
    d = repo / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    ir = SkillIR(name=name, description=description, body=body,
                 level=Level(level), native_agent=native_agent, requires=requires or [])
    emit_canonical(ir, d / "SKILL.md")
    for rel, content in (resources or {}).items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    return d


def _fake_env(tmp_path: Path, agents=("ClaudeCode", "ZCode", "Hermes")):
    """假 repo + 内存 machines(全部 agent 指向 tmp)+ 空 manifest。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    agents_cfg = AgentsConfig.load(REPO_ROOT / "agents.toml")
    machines = MachinesConfig()
    machines.set_skills_dir("m1", "ClaudeCode", str(tmp_path / "claude"))
    machines.set_skills_dir("m1", "ZCode", str(tmp_path / "zcode"))
    machines.set_skills_dir("m1", "Hermes", str(tmp_path / "hermes"))
    machines.set_skills_dir("m2", "ClaudeCode", str(tmp_path / "claude2"))
    manifest = DeploymentsManifest(path=repo / "manifests" / "deployments.json")
    caps = CapabilityMatrix.load(REPO_ROOT / "capabilities.toml")
    return repo, agents_cfg, machines, manifest, caps


def test_sync_deploys_and_body_zero_loss(tmp_path):
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    body = b"## Step\n\nline\r\nCRLF\n"
    _write_canonical(repo, "demo", body=body, resources={"scripts/run.py": "print(1)\n"})

    ctx = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    kinds = {(i.kind, i.skill) for i in ctx.plan}
    assert ("deploy", "demo") in kinds or ("keep", "demo") in kinds
    rc = execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)

    assert rc == 0
    # ClaudeCode 落盘 + body 字节等值
    raw = (tmp_path / "claude" / "demo" / "SKILL.md").read_bytes()
    assert raw.endswith(body), "deployed body 必须与 canonical 字节等值"
    # 资源结构保真
    assert (tmp_path / "claude" / "demo" / "scripts" / "run.py").read_text() == "print(1)\n"
    # manifest 记录
    recs = manifest.find("demo", machine="m1", agent="ClaudeCode")
    assert len(recs) == 1 and recs[0].method == "cp" and recs[0].ir_hash.startswith("sha256:")
    # Hermes 也部署了(默认 category)
    assert (tmp_path / "hermes" / "imported" / "demo" / "SKILL.md").exists()


def test_sync_keep_when_hash_same(tmp_path):
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    _write_canonical(repo, "demo")
    ctx = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)

    ctx2 = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    assert any(i.kind == "keep" and i.skill == "demo" for i in ctx2.plan)


def test_sync_disable_cleans_local_and_pends_remote(tmp_path):
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    # 先部署到 m1
    _write_canonical(repo, "demo")
    execute(repo, "m1", collect(repo, "m1", None, None, machines, agents_cfg, manifest),
            machines, agents_cfg, caps, manifest)
    # 模拟 m2 也部署过(m2 有 ClaudeCode)
    from skillhub.manifest import DeployRecord

    m2_dir = tmp_path / "claude2" / "demo"
    m2_dir.mkdir(parents=True)
    (m2_dir / "SKILL.md").write_bytes(b"x")
    manifest.upsert(DeployRecord(skill="demo", machine="m2", agent="ClaudeCode",
                                 deploy_path=str(m2_dir / "SKILL.md"), method="cp"))

    # canonical 改 disable(helper 直接覆盖写 SKILL.md)
    _write_canonical(repo, "demo", level="disable")

    ctx = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    kinds = [i.kind for i in ctx.plan if i.skill == "demo"]
    assert "delete" in kinds and "pending" in kinds, [str(i) for i in ctx.plan]
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)

    assert not (tmp_path / "claude" / "demo").exists(), "m1 副本应被清"
    rec_m2 = manifest.find("demo", machine="m2")
    assert rec_m2 and rec_m2[0].pending_deletion is True
    # m2 sync 时执行 pending
    manifest.process_pending_deletions("m2")
    assert not m2_dir.exists()


def test_sync_orphan_record_cleaned(tmp_path):
    """manifest 有记录但 canonical 已删(git rm 后 sync)→ 自动清理。"""
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    d = tmp_path / "claude" / "ghost"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(b"x")
    from skillhub.manifest import DeployRecord

    manifest.upsert(DeployRecord(skill="ghost", machine="m1", agent="ClaudeCode",
                                 deploy_path=str(d / "SKILL.md"), method="cp"))
    ctx = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    assert any(i.kind == "delete" and i.skill == "ghost" for i in ctx.plan)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    assert not d.exists() and manifest.find("ghost") == []


def test_sync_hermes_oversize_skipped_and_stale_cleaned(tmp_path):
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    huge = ("line\n" * 20_100).encode()
    _write_canonical(repo, "big", body=huge)

    # 第一次: Hermes skip, 但 ClaudeCode cp
    ctx = collect(repo, "m1", ["big"], None, machines, agents_cfg, manifest)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    assert (tmp_path / "claude" / "big" / "SKILL.md").exists()
    assert not (tmp_path / "hermes" / "imported" / "big").exists()
    assert manifest.find("big", machine="m1", agent="Hermes") == []

    # 伪造一份旧的 Hermes 记录(历史部署过), 再 sync 应清掉
    from skillhub.manifest import DeployRecord

    stale = tmp_path / "hermes" / "imported" / "big"
    stale.mkdir(parents=True)
    (stale / "SKILL.md").write_bytes(b"old")
    manifest.upsert(DeployRecord(skill="big", machine="m1", agent="Hermes",
                                 deploy_path=str(stale / "SKILL.md"), method="cp"))
    ctx = collect(repo, "m1", ["big"], None, machines, agents_cfg, manifest)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    assert not stale.exists(), "Hermes skip 后旧副本应清"
    assert manifest.find("big", machine="m1", agent="Hermes") == []


def test_sync_zcode_real_dir_deferred_clean_target_ln(tmp_path):
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    canon = _write_canonical(repo, "demo")

    # 目标已是真实目录 → deferred, 不写记录不动盘
    real = tmp_path / "zcode" / "demo"
    real.mkdir(parents=True)
    (real / "SKILL.md").write_bytes(b"user real")
    ctx = collect(repo, "m1", ["demo"], ["ZCode"], machines, agents_cfg, manifest)
    assert any(i.kind == "deferred" for i in ctx.plan)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    assert (real / "SKILL.md").read_bytes() == b"user real"
    assert manifest.find("demo", machine="m1", agent="ZCode") == []

    # 干净目标 → ln
    real2 = tmp_path / "zcode" / "fresh"
    canon2 = _write_canonical(repo, "fresh")
    ctx = collect(repo, "m1", ["fresh"], ["ZCode"], machines, agents_cfg, manifest)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    assert real2.is_symlink() and real2.resolve() == canon2.resolve()
    rec = manifest.find("fresh", machine="m1", agent="ZCode")
    assert rec and rec[0].method == "ln"


def test_sync_agent_not_on_machine_not_planned(tmp_path):
    """机器没配的 Agent(如 m1 无 Codex)不出现在计划。"""
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    _write_canonical(repo, "demo")
    ctx = collect(repo, "m1", None, None, machines, agents_cfg, manifest)
    assert all(i.agent != "Codex" for i in ctx.plan)


def test_sync_prompt_injected_for_missing_capability(tmp_path):
    """requires 含 ClaudeCode 不支持的能力时, deployed 顶部应有 ⚠️ 前言(body 仍零损耗)。"""
    repo, agents_cfg, machines, manifest, caps = _fake_env(tmp_path)
    body = b"## gen\n\nmake image\n"
    _write_canonical(repo, "img", body=body, requires=["image_generation"],
                     native_agent="Hermes")
    ctx = collect(repo, "m1", ["img"], ["ClaudeCode"], machines, agents_cfg, manifest)
    execute(repo, "m1", ctx, machines, agents_cfg, caps, manifest)
    raw = (tmp_path / "claude" / "img" / "SKILL.md").read_bytes()
    assert "\u26a0\ufe0f".encode() in raw, "缺能力硬警告应注入"
    assert raw.endswith(body), "body 仍字节等值(前言在外面)"
