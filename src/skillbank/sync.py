"""Sync engine — canonical skills → 该机器配置的 Agents, 计划/展示/执行三段式。

流程:
1. collect(): 解析 canonical skills/<name>/SKILL.md → IR;
   先处理 pending_deletion(删除链跨机段);
   再处理 disable 级 skill 与孤儿记录(canonical 已删)的清理;
   最后对每个 skill × 机器上的 Agent 生成 deploy 计划。
2. show_plan(): 人话展示(dry-run 到此为止)。
3. execute(): 真 deploy(emitter) + manifest upsert/清理。

计划项 kind:
  deploy    将部署(cp/ln)
  deferred  ZCode 目标是真实目录, 不动, 需 zcode-cleanup
  skip      不部署(原因见 detail: 未装 / Hermes 超限 / 被过滤)
  delete    本机清理(该 skill 的旧部署)
  pending   其它机器标 pending_deletion
  keep      hash 相同的重部署(幂等, 标记为保持)
  warn      解析/一致性问题, 不中断
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from skillbank.agents import AgentsConfig
from skillbank.capabilities import CapabilityMatrix
from skillbank.emitters import get_emitter
from skillbank.ir import Level, SkillIR
from skillbank.manifest import DeployRecord, DeploymentsManifest
from skillbank.machines import MachinesConfig
from skillbank.parsers.canonical import parse_canonical
from skillbank.prompt_inject import inject_prompts

__all__ = ["PlanItem", "SyncContext", "collect", "show_plan", "execute"]


@dataclass
class PlanItem:
    kind: str                  # deploy | deferred | skip | delete | pending | keep | warn
    skill: str
    agent: Optional[str] = None
    detail: str = ""


@dataclass
class SyncContext:
    plan: list[PlanItem] = field(default_factory=list)
    irs: dict[str, SkillIR] = field(default_factory=dict)   # skill -> IR
    # execute 阶段要 deploy 的 (skill, agent) 对(collect 时敲定, avoid 重算过滤逻辑)
    deploy_pairs: list[tuple[str, str]] = field(default_factory=list)


# --- 阶段 1: collect ---


def _iter_canonical_skills(repo_root: Path) -> list[Path]:
    skills_dir = repo_root / "skills"
    if not skills_dir.exists():
        return []
    return sorted(p.parent for p in skills_dir.glob("*/SKILL.md"))


def _cleanup_plan_for_skill(skill: str, machine: str, manifest: DeploymentsManifest,
                            ctx: SyncContext, reason: str) -> None:
    """disable/orphan:本机记录 → delete 项, 其它机器记录 → pending 项。"""
    for r in manifest.find(skill):
        if r.machine == machine:
            ctx.plan.append(PlanItem("delete", skill, r.agent,
                                     f"{reason}; {r.deploy_path}"))
        else:
            ctx.plan.append(PlanItem("pending", skill, r.agent,
                                     f"{reason}; {r.machine} 下次 sync 时删"))


def collect(
    repo_root: Path,
    machine: str,
    skills_filter: Optional[list[str]],
    agents_filter: Optional[list[str]],
    machines: MachinesConfig,
    agents_cfg: AgentsConfig,
    manifest: DeploymentsManifest,
) -> SyncContext:
    ctx = SyncContext()
    mcfg = machines.get_machine(machine)

    # a) pending_deletion(其它机器 rm 标来的, 本机 sync 先执行)
    for r in manifest.records:
        if r.pending_deletion and r.machine == machine:
            ctx.plan.append(PlanItem("delete", r.skill, r.agent, f"pending; {r.deploy_path}"))

    # b) 孤儿记录:manifest 有但 canonical 已无此 skill
    canonical_names = {p.name for p in _iter_canonical_skills(repo_root)}
    for orphan in [s for s in manifest.skills() if s not in canonical_names]:
        _cleanup_plan_for_skill(orphan, machine, manifest, ctx, "canonical 已删除")

    # c) 解析 canonical skills
    for skill_dir in _iter_canonical_skills(repo_root):
        name = skill_dir.name
        try:
            ir = parse_canonical(skill_dir / "SKILL.md")
        except Exception as e:  # noqa: BLE001 — 单 skill 坏不中断全局
            ctx.plan.append(PlanItem("warn", name, None, f"解析失败: {e}"))
            continue
        if ir.name != name:
            ctx.plan.append(PlanItem("warn", name, None,
                                     f"frontmatter name={ir.name!r} != 目录名(以目录名为准)"))
        ctx.irs[name] = ir

        # disable 级:不同步, 且清理既有部署(决策 6)
        if ir.level == Level.DISABLE:
            if manifest.find(name):
                _cleanup_plan_for_skill(name, machine, manifest, ctx, "level=disable")
            else:
                ctx.plan.append(PlanItem("skip", name, None, "disable 且无部署记录"))
            continue

    # d) skill × agent 部署计划
    # 先按 agent 粒度判一次"装没装":skills 根的父目录(agent home)不存在 = 没装,
    # 该 agent 全部 skip(防 mkdir -p 凭空造孤儿目录;与 doctor error 语义一致)。
    installed: dict[str, bool] = {}
    for agent in agents_cfg.agents:
        if agent not in mcfg.agents:
            continue
        root = machines.get_skills_dir(machine, agent)
        installed[agent] = root is not None and root.parent.exists()

    for name, ir in ctx.irs.items():
        if ir.level == Level.DISABLE:
            continue
        if skills_filter and name not in skills_filter:
            continue
        for agent in agents_cfg.agents:            # agents.toml 顺序
            if agent not in mcfg.agents:
                continue                            # 该机器没配此 Agent = 没装
            deploy_root = machines.get_skills_dir(machine, agent)
            if not installed.get(agent):
                ctx.plan.append(PlanItem("skip", name, agent,
                                         f"agent 未安装?({deploy_root.parent} 不存在)"))
                continue
            if agents_filter and agent not in agents_filter:
                ctx.plan.append(PlanItem("skip", name, agent, "未选(过滤)"))
                continue
            detail = str(deploy_root / name)

            # ZCode 特判:目标是真实目录 → deferred(emitter 执行时也会判, 计划期先给准确预告)
            if agent == "ZCode":
                target = deploy_root / name
                if target.exists() and not target.is_symlink():
                    ctx.plan.append(PlanItem("deferred", name, agent,
                                             f"目标已是真实目录 {target}; 跑 zcode-cleanup 处理"))
                    continue

            kind = "deploy"
            rec = manifest.find(name, machine=machine, agent=agent)
            if rec and rec[0].ir_hash == ir.body_hash():
                kind = "keep"
            ctx.plan.append(PlanItem(kind, name, agent, detail))
            ctx.deploy_pairs.append((name, agent))
    return ctx


# --- 阶段 2: show ---


_KIND_MARK = {"deploy": "+", "keep": "=", "deferred": "~", "skip": "-",
              "delete": "x", "pending": "p", "warn": "!"}


def show_plan(ctx: SyncContext) -> None:
    if not ctx.plan:
        print("[sync] 无计划(无 canonical skill / 无该机器 Agent)")
        return
    for it in ctx.plan:
        mark = _KIND_MARK.get(it.kind, "?")
        agent = f" → {it.agent}" if it.agent else ""
        print(f"  [{mark}] {it.kind:8s} {it.skill}{agent}  {it.detail}")
    n = {k: sum(1 for i in ctx.plan if i.kind == k) for k in _KIND_MARK}
    parts = [f"{v} {k}" for k, v in n.items() if v]
    print(f"  合计: {', '.join(parts)}")


# --- 阶段 3: execute ---


def execute(
    repo_root: Path,
    machine: str,
    ctx: SyncContext,
    machines: MachinesConfig,
    agents_cfg: AgentsConfig,
    caps: CapabilityMatrix,
    manifest: DeploymentsManifest,
) -> int:
    """执行计划;返回非 0 表示有失败。manifest 有变更时 save。"""
    if not ctx.plan:
        return 0
    failures = 0
    manifest_dirty = False

    # 删除段:本机 delete 项(pending 项 + disable/orphan 清理)
    delete_skills = {(i.skill) for i in ctx.plan if i.kind == "delete"}
    for skill in sorted(delete_skills):
        for a in manifest.delete_local(skill, machine):
            print(f"  {a}")
            manifest_dirty = True
    # 其它机器 pending 标记(disable/orphan 的, pending kind 项)
    pending_skills = {i.skill for i in ctx.plan if i.kind == "pending"}
    for skill in sorted(pending_skills):
        n = manifest.mark_pending_deletion(skill, except_machine=machine)
        if n:
            print(f"  pending_deletion x{n}: {skill}(其它机器下次 sync 删)")
            manifest_dirty = True

    # 部署段
    for name, agent in ctx.deploy_pairs:
        ir = ctx.irs[name]
        cfg = agents_cfg.get(agent)
        deploy_root = machines.get_skills_dir(machine, agent)
        prompt = inject_prompts(ir, agent, caps)
        try:
            result = get_emitter(agent).deploy(
                ir, deploy_root, cfg, repo_root / "skills" / name, prompt_bytes=prompt
            )
        except Exception as e:  # noqa: BLE001 — 单个失败不中断其余
            print(f"  ✗ {name} → {agent}: {e}")
            failures += 1
            continue

        if result.method == "skipped":
            # Hermes 超限等:该 Agent 本轮不部署。若之前有部署记录 → 清掉旧副本+记录
            print(f"  - {name} → {agent}: SKIP({result.note})")
            recs = manifest.find(name, machine=machine, agent=agent)
            if recs:
                for a in manifest.delete_local(name, machine, agent=agent):
                    print(f"    清理旧部署: {a}")
                manifest_dirty = True
            continue
        if result.method == "deferred":
            print(f"  ~ {name} → {agent}: DEFERRED({result.note})")
            continue

        # P0#3: kimi 不支持 frontmatter 禁止触发字段, manual/experimental disable 在 kimi 失效
        if agent == "kimi-code" and ir.level in (Level.MANUAL, Level.EXPERIMENTAL):
            print(f"  ⚠ {name} → kimi-code: level={ir.level.value} 但 kimi 无禁自动触发字段, "
                  f"该 Agent 端可能仍自动触发(请靠 description 话术或下级工具显式控制)")
        elif agent == "kimi-code" and ir.level == Level.DISABLE:
            pass  # disable 不该到这 deploy 段(collect 已过滤)

        rec = DeployRecord(
            skill=name, machine=machine, agent=agent,
            deploy_path=str(result.deployed_path), method=result.method,
            ir_hash=ir.body_hash(), note=result.note,
        )
        manifest.upsert(rec)
        manifest_dirty = True
        extra = f"({result.note})" if result.note else ""
        print(f"  {result.method} {name} → {agent}{extra}")

    if manifest_dirty:
        manifest.save()
        print(f"  manifest 已更新: {manifest.path}")
    return failures
