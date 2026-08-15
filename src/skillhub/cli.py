"""SkillHub CLI — subcommand dispatcher.

M0 status: framework + subcommand stubs (real logic lands in M1-M7).

subcommands:
    sync      parse canonical -> emit to selected agents x machine
              (interactive menu if no flags)
    add       import a new skill (local path / agent dir / market URL -> canonical)
    rm        remove skill from canonical + clean deployed copies (manifest-driven)
    list      tabular deployment state (skill x agent x machine)
    import    reverse-import an existing skill from an agent's dir into canonical
    doctor    validate environment (agent dirs / git / manifest / kimi --skills-dir)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

__all__ = ["main", "build_parser"]

# /Users/ss/Documents/main_store/temp/SkillHub/src/skillhub/cli.py -> repo root
# parents[0]=skillhub  [1]=src  [2]=SkillHub
REPO_ROOT = Path(__file__).resolve().parents[2]


# --- subcommand stubs (real implementations land in later milestones) ---


def _cmd_sync(args: argparse.Namespace) -> int:
    """M1-M2+: parse canonical -> emit to selected agents x machine."""
    # TODO(M1): load canonical skill(s) -> parser -> SkillIR
    # TODO(M2-M4): per-Agent emitter (cp/ln + frontmatter rewrite + prompt inject)
    # TODO(M5): write deployments.json manifest records
    # TODO(M6): interactive skill x agent x machine menu when no flags
    print("[sync] TODO (M1-M6): parse canonical -> emit to agents x machine")
    if args.skills:
        print(f"  --skills: {args.skills}")
    if args.agents:
        print(f"  --agents: {args.agents}")
    print(f"  --to:     {args.machine}")
    print(f"  --dry-run: {args.dry_run}   --yes: {args.yes}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    """M6: import skill from path/URL -> skills/<name>/ canonical."""
    print(f"[add] TODO (M6): import skill from {args.source!r} -> skills/<name>/")
    return 0


def _cmd_rm(args: argparse.Namespace) -> int:
    """M5: removal chain — delete deployed copies per manifest, keep canonical."""
    from skillhub.manifest import DeploymentsManifest

    manifest_path = REPO_ROOT / "manifests" / "deployments.json"
    manifest = DeploymentsManifest.load(manifest_path)
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
        for a in manifest.process_pending_deletions(machine, dry_run=True):
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
    print(f"  manifest 已更新: {manifest_path}")
    print(f"  canonical 保留在 {REPO_ROOT / 'skills' / args.name}(disable 语义=stash, git 可恢复)")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    """M6: tabular skill x agent x machine deployment state."""
    print("[list] TODO (M6): tabular skill x agent x machine")
    for f in ("agent", "level", "machine"):
        v = getattr(args, f)
        if v:
            print(f"  --{f}: {v}")
    return 0


def _cmd_import(args: argparse.Namespace) -> int:
    """M6: reverse-import an existing skill from an agent's dir into canonical."""
    print(f"[import] TODO (M6): reverse-import skill from {args.path!r}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    """M6: validate environment."""
    print("[doctor] TODO (M6): env check")
    print("  - agent install dirs exist (per machines.toml + agents.toml)")
    print("  - git status clean")
    print("  - manifest vs actual deployment consistency")
    print("  - kimi --skills-dir configured (or note to add)")
    return 0


def _cmd_scan(args: argparse.Namespace) -> int:
    """扫描本机各 Agent 的 skills 目录, 确认后写入 machines.toml。

    只应在目标机器本机跑(探测的是本机文件系统)。
    已配置且盘上存在的路径保持不动;缺失/无效的给候选让用户选。
    """
    import sys

    from skillhub.agents import AgentsConfig
    from skillhub.machines import MachinesConfig
    from skillhub.scan import detect_agent, pick_best

    agents_cfg = AgentsConfig.load(REPO_ROOT / "agents.toml")
    machines = MachinesConfig.load(
        REPO_ROOT / "machines.toml", known_agents=set(agents_cfg.agents)
    )
    machine = args.machine

    agent_order = list(agents_cfg.agents)  # agents.toml 的顺序
    changes: dict[str, str] = {}           # agent -> 新 skills_dir

    print(f"[scan] 机器 {machine!r} — 探测本机 7 个 Agent 的 skills 目录\n")

    for agent in agent_order:
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
            best = pick_best(cands)
            print(f"    (dry-run) 将选 [{cands.index(best) + 1}] {best.path}")
            continue
        if args.yes or not sys.stdin.isatty():
            best = pick_best(cands)
            changes[agent] = str(best.path)
            print(f"    → 自动选 {best.path}({best.confidence})")
            continue
        # 交互: 序号选择 / 手输路径 / 回车跳过
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


# --- argparse wiring ---


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skillhub",
        description="Central skill repository -> 7 AI agents (body byte-identical, no loss).",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sp = sub.add_parser(
        "sync",
        help="Sync canonical skills -> agents x machine (interactive if no flags)",
    )
    sp.add_argument("-s", "--skill", action="append", dest="skills", help="skill name (repeatable)")
    sp.add_argument("-a", "--agent", action="append", dest="agents", help="agent (repeatable)")
    sp.add_argument(
        "--to",
        dest="machine",
        default="mac-main",
        help="target machine alias from machines.toml (default: mac-main)",
    )
    sp.add_argument("--dry-run", action="store_true", help="show diff, do not write")
    sp.add_argument("--yes", action="store_true", help="skip confirmation prompt")
    sp.set_defaults(func=_cmd_sync)

    sp = sub.add_parser("add", help="Import a new skill (local path / agent dir / market URL)")
    sp.add_argument("source", help="source path or git URL")
    sp.set_defaults(func=_cmd_add)

    sp = sub.add_parser(
        "rm",
        help="Remove a skill + clean deployed copies (manifest-driven; canonical kept)",
    )
    sp.add_argument("name", help="canonical skill name")
    sp.add_argument("--machine", default="mac-main", help="当前机器别名(machines.toml)")
    sp.add_argument("--dry-run", action="store_true", help="只报告不动盘")
    sp.set_defaults(func=_cmd_rm)

    sp = sub.add_parser("list", help="List deployment state (skill x agent x machine)")
    sp.add_argument("--agent")
    sp.add_argument("--level", choices=["auto", "manual", "experimental", "disable"])
    sp.add_argument("--machine")
    sp.set_defaults(func=_cmd_list)

    sp = sub.add_parser(
        "import",
        help="Reverse-import an existing skill from an agent's dir into canonical",
    )
    sp.add_argument("path", help="agent's skill dir (must contain SKILL.md)")
    sp.set_defaults(func=_cmd_import)

    sp = sub.add_parser(
        "doctor",
        help="Validate environment: agent dirs / git / manifest / kimi --skills-dir",
    )
    sp.set_defaults(func=_cmd_doctor)

    sp = sub.add_parser(
        "scan",
        help="扫描本机各 Agent skills 目录, 确认后写入 machines.toml(在目标机器上跑)",
    )
    sp.add_argument("--machine", default="mac-main", help="当前机器别名(machines.toml)")
    sp.add_argument("--yes", action="store_true", help="非交互: 每项自动选最优候选")
    sp.add_argument("--dry-run", action="store_true", help="只展示探测结果, 不确认不写")
    sp.set_defaults(func=_cmd_scan)

    return p


def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())