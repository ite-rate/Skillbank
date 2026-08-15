"""Skillbank CLI — subcommand dispatcher.

子命令:
    sync           canonical → 该机器 Agents(collect→show→confirm→execute;无 flag 交互选)
    add            导入新 skill(本地路径 / git URL)
    import         从某 Agent 目录反向导入既有 skill 进 canonical
    rm             删除部署副本(manifest 驱动;canonical 保留)
    list           部署状态表(skill × agent)
    doctor         环境体检(配置/路径/manifest/canonical/git)
    scan           探测本机 Agent skills 目录, 确认写入 machines.toml
    zcode-cleanup  清理 ~/.zcode/skills 真实副本(交互确认 + mv 备份 → 软链 canonical)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from skillbank.ir import Level

__all__ = ["main", "build_parser"]

# .../Skillbank/src/skillbank/cli.py -> repo root(parents[0]=skillbank [1]=src [2]=Skillbank)
REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_configs():
    from skillbank.agents import AgentsConfig
    from skillbank.capabilities import CapabilityMatrix
    from skillbank.machines import MachinesConfig

    agents_cfg = AgentsConfig.load(REPO_ROOT / "agents.toml")
    machines = MachinesConfig.load(
        REPO_ROOT / "machines.toml", known_agents=set(agents_cfg.agents)
    )
    caps = CapabilityMatrix.load(REPO_ROOT / "capabilities.toml")
    return agents_cfg, machines, caps


def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


# --- sync ---


def _cmd_sync(args: argparse.Namespace) -> int:
    from skillbank.manifest import DeploymentsManifest
    from skillbank.sync import collect, execute, show_plan

    agents_cfg, machines, caps = _load_configs()
    machine = args.machine
    if machine not in machines.machines:
        print(f"[sync] 未知机器 {machine!r}(machines.toml: {sorted(machines.machines)})")
        return 2
    manifest = DeploymentsManifest.load(REPO_ROOT / "manifests" / "deployments.json")

    skills_filter = args.skills
    agents_filter = args.agents

    # 交互:无 -s/-a 且 tty 且非 --yes → 选 skill × agent
    if not skills_filter and not agents_filter and _is_tty() and not args.yes:
        from skillbank.interactive import select_many

        from skillbank.sync import _iter_canonical_skills  # 内部函数, 轻用

        skill_dirs = _iter_canonical_skills(REPO_ROOT)
        if not skill_dirs:
            print("[sync] skills/ 为空 — 先 skillbank import <某 agent 的 skill 目录>")
            return 0
        opts = [f"{p.name} ({(p / 'SKILL.md').exists() and 'ok' or '无SKILL.md'})"
                for p in skill_dirs]
        idx = select_many("选要同步的 skill:", opts)
        skills_filter = [skill_dirs[i].name for i in idx]

        mcfg = machines.get_machine(machine)
        idx = select_many(f"选要同步到 {machine} 的 Agent:", list(mcfg.agents))
        agents_filter = [list(mcfg.agents)[i] for i in idx]

    ctx = collect(REPO_ROOT, machine, skills_filter, agents_filter, machines,
                  agents_cfg, manifest)
    print(f"[sync] machine={machine} 计划:")
    show_plan(ctx)
    if args.dry_run:
        print("[sync] dry-run 结束, 未写任何文件")
        return 0
    if not args.yes and _is_tty():
        from skillbank.interactive import confirm

        if not confirm("执行以上计划?"):
            print("[sync] 已取消")
            return 0
    failures = execute(REPO_ROOT, machine, ctx, machines, agents_cfg, caps, manifest)
    print(f"[sync] 完成" + (f"({failures} 个失败)" if failures else " ✓"))
    return 1 if failures else 0


# --- add / import ---


def _cmd_add(args: argparse.Namespace) -> int:
    from skillbank.importer import import_git_url, import_skill

    src = args.source
    try:
        if src.startswith(("http://", "https://", "git@", "ssh://")):
            results = import_git_url(src, REPO_ROOT, level=args.level, force=args.force)
            for d, warns in results:
                print(f"[add] 导入 → {d}")
                for w in warns:
                    print(f"  ⚠ {w}")
        else:
            d, warns = import_skill(Path(src).expanduser(), REPO_ROOT,
                                   level=args.level, force=args.force,
                                   machines=_load_configs()[1], machine=args.machine)
            print(f"[add] 导入 → {d}")
            for w in warns:
                print(f"  ⚠ {w}")
        print(f"[add] 下一步: skillbank sync 同步到各 Agent")
        return 0
    except ValueError as e:
        print(f"[add] ✗ {e}")
        return 1


def _cmd_import(args: argparse.Namespace) -> int:
    from skillbank.importer import import_skill

    agents_cfg, machines, _ = _load_configs()
    try:
        agent = args.agent
        if agent and agent not in agents_cfg.agents:
            print(f"[import] 未知 agent {agent!r}(agents.toml: {sorted(agents_cfg.agents)})")
            return 2
        d, warns = import_skill(Path(args.path).expanduser(), REPO_ROOT,
                                level=args.level, agent=agent,
                                machines=machines, machine=args.machine, force=args.force)
        print(f"[import] → {d}")
        for w in warns:
            print(f"  ⚠ {w}")
        print(f"[import] 下一步: skillbank sync 同步到各 Agent")
        return 0
    except ValueError as e:
        print(f"[import] ✗ {e}")
        return 1


# --- rm ---


def _cmd_rm(args: argparse.Namespace) -> int:
    from skillbank.manifest import DeploymentsManifest

    manifest = DeploymentsManifest.load(REPO_ROOT / "manifests" / "deployments.json")
    recs = manifest.find(args.name)
    if not recs:
        print(f"[rm] skill {args.name!r} 无 manifest 部署记录(未同步过或已删), 无动作")
        return 0

    machine = args.machine
    local_recs = [r for r in recs if r.machine == machine]
    remote_recs = [r for r in recs if r.machine != machine]

    print(f"[rm] {args.name!r}: 本机({machine}) {len(local_recs)} 条, 其它机器 {len(remote_recs)} 条")

    if args.dry_run:
        for a in manifest.delete_local(args.name, machine, dry_run=True):
            print(f"  [dry-run] {a}")
        print("  (dry-run: 其它机器仍会标 pending_deletion, 那边下次 sync 时删)")
        return 0

    actions = manifest.delete_local(args.name, machine)
    for a in actions:
        print(f"  {a}")
    n_pending = manifest.mark_pending_deletion(args.name, except_machine=machine)
    if n_pending:
        print(f"  标记 pending_deletion x{n_pending}(其它机器下次 sync 时删)")
    manifest.save()
    print(f"  manifest 已更新: {REPO_ROOT / 'manifests' / 'deployments.json'}")
    print(f"  canonical 保留在 {REPO_ROOT / 'skills' / args.name}(disable 语义=stash, git 可恢复)")
    return 0


# --- list ---


_AGENT_SHORT = {"ClaudeCode": "CC", "ZCode": "ZC", "QwenWorkCN": "QW", "TeleAgent": "TA",
                "Hermes": "HE", "Codex": "CX", "kimi-code": "KI"}


def _cmd_list(args: argparse.Namespace) -> int:
    from skillbank.manifest import DeploymentsManifest
    from skillbank.sync import _iter_canonical_skills

    agents_cfg, machines, _ = _load_configs()
    machine = args.machine
    if machine not in machines.machines:
        print(f"[list] 未知机器 {machine!r}")
        return 2
    manifest = DeploymentsManifest.load(REPO_ROOT / "manifests" / "deployments.json")
    mcfg = machines.get_machine(machine)
    cols = [a for a in agents_cfg.agents if a in mcfg.agents]

    # 行来源: canonical + manifest-only(孤儿)
    rows: list[tuple[str, str, str]] = []   # (skill, level, native)
    seen = set()
    import yaml

    for d in _iter_canonical_skills(REPO_ROOT):
        name = d.name
        seen.add(name)
        level, native = "?", ""
        try:
            fm = yaml.safe_load((d / "SKILL.md").read_bytes().split(b"---\n")[1])
            level = fm.get("level", "auto")
            native = fm.get("native_agent") or ""
        except Exception:  # noqa: BLE001 — 列表展示容错
            pass
        rows.append((name, level, native))
    for s in manifest.skills():
        if s not in seen:
            rows.append((s, "(孤儿)", ""))

    if args.level:
        rows = [r for r in rows if r[1] == args.level]
    if args.agent:
        cols = [args.agent]

    header = f"{'skill':<28s} {'level':<14s} {'native':<12s} " + " ".join(
        f"{_AGENT_SHORT.get(a, a[:2].upper()):>2s}" for a in cols)
    print(f"[list] machine={machine}(c=cp l=ln p=pending ·=未部署 ~=deferred)")
    print("  " + header)
    for name, level, native in sorted(rows):
        cells = []
        for a in cols:
            recs = manifest.find(name, machine=machine, agent=a)
            if not recs:
                cells.append("·")
            elif recs[0].pending_deletion:
                cells.append("p")
            elif recs[0].method == "ln":
                cells.append("l")
            else:
                cells.append("c")
        print(f"  {name:<28s} {level:<14s} {native:<12s} " + " ".join(f"{c:>2s}" for c in cells))
    return 0


# --- doctor ---


def _cmd_doctor(args: argparse.Namespace) -> int:
    from skillbank.manifest import DeploymentsManifest
    from skillbank.sync import _iter_canonical_skills

    errors: list[str] = []
    warns: list[str] = []
    print(f"[doctor] repo: {REPO_ROOT}")

    # 1. 配置互验
    try:
        agents_cfg, machines, _ = _load_configs()
        print(f"  ✓ 配置加载: {len(agents_cfg.agents)} agents, {len(machines.machines)} machines")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ 配置加载失败: {e}")
        return 1

    machine = args.machine
    if machine not in machines.machines:
        errors.append(f"未知机器 {machine!r}")
    else:
        # 2. 该机器路径存在性
        e_, w_ = machines.check_paths_exist(machine)
        for x in e_:
            errors.append(f"路径: {x}")
        for x in w_:
            warns.append(f"路径: {x}")
        print(f"  ✓/✗ 路径检查: {len(e_)} errors, {len(w_)} warnings")

    # 3. manifest 一致性
    manifest = DeploymentsManifest.load(REPO_ROOT / "manifests" / "deployments.json")
    for i in manifest.check_consistency():
        warns.append(f"manifest: {i}")
    print(f"  ✓ manifest: {len(manifest.records)} 条记录, {len(manifest.check_consistency())} 项差异")

    # 4. canonical skills 可解析 + name 一致
    from skillbank.parsers.canonical import parse_canonical

    for d in _iter_canonical_skills(REPO_ROOT):
        try:
            ir = parse_canonical(d / "SKILL.md")
            if ir.name != d.name:
                warns.append(f"canonical: {d.name} 的 frontmatter name={ir.name!r} 不一致")
        except Exception as e:  # noqa: BLE001
            errors.append(f"canonical: {d.name} 解析失败: {e}")
    print(f"  ✓/✗ canonical: {len(list(_iter_canonical_skills(REPO_ROOT)))} 个 skill")

    # 5. git 状态
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
                       capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        warns.append(f"git 工作区有未提交变更({len(r.stdout.strip().splitlines())} 文件)")
    print(f"  ✓ git: {'干净' if not r.stdout.strip() else '有未提交变更'}")

    for w in warns:
        print(f"  ⚠ {w}")
    for e in errors:
        print(f"  ✗ {e}")
    print(f"[doctor] {'FAIL' if errors else 'OK'}({len(errors)} errors, {len(warns)} warnings)")
    return 1 if errors else 0


# --- scan ---


def _cmd_scan(args: argparse.Namespace) -> int:
    from skillbank.scan import detect_agent, pick_best

    agents_cfg, machines, _ = _load_configs()
    machine = args.machine
    changes: dict[str, str] = {}

    print(f"[scan] 机器 {machine!r} — 探测本机 7 个 Agent 的 skills 目录\n")
    for agent in agents_cfg.agents:
        cur = machines.get_skills_dir(machine, agent)
        if cur is not None and cur.exists():
            print(f"  ✓ {agent:12s} 保持 {cur}(已配置且存在)")
            continue
        if cur is not None:
            print(f"  ? {agent:12s} 已配置 {cur} 但盘上不存在")
        cands = detect_agent(agent)
        if not cands:
            print(f"  ✗ {agent:12s} 未探测到(没装?), 跳过 = sync 时忽略该 Agent")
            continue
        for i, c in enumerate(cands, 1):
            print(f"    [{i}] {c.path}  ({c.confidence}: {c.evidence})")
        if args.dry_run:
            print(f"    (dry-run) 将选 [{cands.index(pick_best(cands)) + 1}] {pick_best(cands).path}")
            continue
        if args.yes or not _is_tty():
            best = pick_best(cands)
            changes[agent] = str(best.path)
            print(f"    → 自动选 {best.path}({best.confidence})")
            continue
        default_idx = cands.index(pick_best(cands)) + 1
        ans = input(f"    用哪个? [1-{len(cands)}](回车={default_idx}) / m=<路径>手输 / s跳过: ").strip()
        if ans.lower() == "s":
            print(f"    → 跳过 {agent}")
            continue
        if ans.lower().startswith("m=") and len(ans) > 2:
            changes[agent] = ans[2:]
            print(f"    → 手输 {ans[2:]}")
        else:
            try:
                idx = int(ans) if ans else default_idx
                changes[agent] = str(cands[idx - 1].path)
                print(f"    → 选 [{idx}] {cands[idx - 1].path}")
            except (ValueError, IndexError):
                print(f"    → 输入无法解析, 跳过 {agent}")
                continue

    if args.dry_run:
        print("\n[scan] dry-run 结束, 未写任何文件")
        return 0
    if not changes:
        print("\n[scan] 无变更, machines.toml 未动")
        return 0
    for agent, dir_path in changes.items():
        machines.set_skills_dir(machine, agent, dir_path)
    machines.save(REPO_ROOT / "machines.toml")
    print(f"\n[scan] machines.toml 已更新: {', '.join(changes)}")
    return 0


# --- zcode-cleanup ---


def _cmd_zcode_cleanup(args: argparse.Namespace) -> int:
    """把 ~/.zcode/skills 里的真实副本 mv 备份后软链到 canonical(逐个交互确认)。"""
    import shutil
    from datetime import datetime

    agents_cfg, machines, _ = _load_configs()
    machine = args.machine
    zdir = machines.get_skills_dir(machine, "ZCode")
    if zdir is None or not zdir.exists():
        print(f"[zcode-cleanup] ZCode skills 目录未配置/不存在(machine={machine})")
        return 2

    backup_root = zdir.parent / "skills.bak" / datetime.now().strftime("%Y%m%d-%H%M%S")
    converted = 0

    entries = sorted(zdir.iterdir())
    reals = [e for e in entries if not e.is_symlink()]
    if not reals:
        print(f"[zcode-cleanup] 无真实副本需要处理(共 {len(entries)} 项, 全是软链/文件)")
        return 0

    for e in reals:
        name = e.name
        canonical = REPO_ROOT / "skills" / name
        has_canonical = (canonical / "SKILL.md").exists()
        print(f"\n  {name}: 真实目录({sum(1 for _ in e.rglob('*'))} 项)")
        if has_canonical:
            print(f"    canonical 存在: {canonical}")
            action = "备份+软链"
        else:
            print(f"    canonical 不存在 — 先跑: skillbank import {e}")
            action = None

        if args.dry_run:
            print(f"    [dry-run] {'WOULD ' + action + f' (备份到 {backup_root / name})' if action else '仅提示 import'}")
            continue

        if not has_canonical:
            continue  # 无 canonical 不能链, 不动

        if args.yes or not _is_tty():
            do_it = True
        else:
            from skillbank.interactive import confirm

            do_it = confirm(f"    {action}: mv → {backup_root / name} 再 ln -s canonical?")
        if not do_it:
            print("    跳过")
            continue

        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(e), str(backup_root / name))
        (zdir / name).symlink_to(canonical.resolve())
        print(f"    ✓ 备份 {backup_root / name} + 软链 → {canonical}")
        converted += 1

    print(f"\n[zcode-cleanup] 完成: 转换 {converted} 个(dry-run={args.dry_run})")
    if converted and not args.dry_run:
        print(f"[zcode-cleanup] 备份在 {backup_root}(确认 ZCode 正常后可删)")
    return 0


# --- argparse wiring ---


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skillbank",
        description="Central skill repository -> 7 AI agents (body byte-identical, no loss).",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sp = sub.add_parser("sync", help="Sync canonical skills -> agents x machine")
    sp.add_argument("-s", "--skill", action="append", dest="skills", help="skill name (repeatable)")
    sp.add_argument("-a", "--agent", action="append", dest="agents", help="agent (repeatable)")
    sp.add_argument("--to", dest="machine", default="mac-main", help="machine alias (default mac-main)")
    sp.add_argument("--dry-run", action="store_true", help="show plan, do not write")
    sp.add_argument("--yes", action="store_true", help="no interactive selection/confirm")
    sp.set_defaults(func=_cmd_sync)

    sp = sub.add_parser("add", help="Import a new skill (local path / git URL)")
    sp.add_argument("source", help="source path or git URL")
    sp.add_argument("--level", default="manual", choices=[l.value for l in Level])
    sp.add_argument("--force", action="store_true", help="覆盖已存在的 canonical")
    sp.add_argument("--machine", default="mac-main")
    sp.set_defaults(func=_cmd_add)

    sp = sub.add_parser("import", help="Reverse-import an agent's skill dir into canonical")
    sp.add_argument("path", help="agent's skill dir (must contain SKILL.md)")
    sp.add_argument("--level", default="manual", choices=[l.value for l in Level])
    sp.add_argument("--agent", help="来源 agent 名(不填按路径自动探测)")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--machine", default="mac-main")
    sp.set_defaults(func=_cmd_import)

    sp = sub.add_parser("rm", help="Remove a skill + clean deployed copies (canonical kept)")
    sp.add_argument("name", help="canonical skill name")
    sp.add_argument("--machine", default="mac-main")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=_cmd_rm)

    sp = sub.add_parser("list", help="Deployment state table (skill x agent)")
    sp.add_argument("--agent")
    sp.add_argument("--level", choices=["auto", "manual", "experimental", "disable"])
    sp.add_argument("--machine", default="mac-main")
    sp.set_defaults(func=_cmd_list)

    sp = sub.add_parser("doctor", help="Env check: configs / paths / manifest / canonical / git")
    sp.add_argument("--machine", default="mac-main")
    sp.set_defaults(func=_cmd_doctor)

    sp = sub.add_parser("scan", help="探测本机 Agent skills 目录, 确认写入 machines.toml")
    sp.add_argument("--machine", default="mac-main")
    sp.add_argument("--yes", action="store_true", help="非交互: 每项自动选最优候选")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=_cmd_scan)

    sp = sub.add_parser("zcode-cleanup", help="ZCode 真实副本 → 备份 + 软链 canonical(交互)")
    sp.add_argument("--machine", default="mac-main")
    sp.add_argument("--yes", action="store_true")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=_cmd_zcode_cleanup)

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
