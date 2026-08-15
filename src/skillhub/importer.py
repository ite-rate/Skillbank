"""Importer — 把既有 skill(各 Agent 目录 / 本地路径 / git URL)反向导入中央仓。

只读源目录, 全部产物写进 repo 的 skills/<name>/:
  skills/<name>/SKILL.md                  canonical frontmatter + body 原字节
  skills/<name>/<原目录其它文件/子目录>     保真镜像(body 里的相对路径继续有效)
  skills/<name>/.agent_overrides/<agent>.toml   Agent 专有字段(不污染 canonical)

字段映射规则:
  name / description      直传(缺 name 用目录名; 缺 description 报错)
  level                   默认 manual(新导入未审, 不自动触发; --level 覆盖)
  native_agent            --agent 指定, 或按源路径前缀匹配本机 machines.toml 探测
  description_zh/name_zh  取 description_zh/name_zh(QwenWorkCN) 或
                          description_cn/name_cn(TeleAgent) 映射到 canonical _zh
  version/license         直传(canonical 认识这两个字段)
  其余全部字段            → .agent_overrides/<agent>.toml(或 _unknown.toml)

零损耗: body bytes 原样直传 canonical SKILL.md。
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from skillhub.emitters.canonical import emit_canonical
from skillhub.ir import Level, SkillIR
from skillhub.machines import MachinesConfig
from skillhub.parsers.canonical import FRONTMATTER_RE

__all__ = ["ImportError_", "import_skill", "detect_source_agent", "import_git_url"]

# 导入失败统一抛 ValueError 语义(避免与内置 ImportError 混淆)
ImportError_ = ValueError

# canonical 认识的字段(不进 overrides)
_CANONICAL_FIELDS = {
    "name", "description", "level", "native_agent", "requires",
    "description_zh", "name_zh", "version", "license",
}


def detect_source_agent(src_dir: Path, machines: MachinesConfig,
                        machine: str) -> Optional[str]:
    """源目录在哪个 Agent 的 skills_dir 下 → 那个 Agent 名;探测不到 None。"""
    src = src_dir.resolve()
    m = machines.get_machine(machine)
    for a_name in m.agents:
        root = Path(m.agents[a_name].skills_dir).resolve()
        if src == root or root in src.parents:
            return a_name
    return None


def import_skill(
    src_dir: Path,
    repo_root: Path,
    level: str = "manual",
    agent: Optional[str] = None,
    machines: Optional[MachinesConfig] = None,
    machine: str = "mac-main",
    force: bool = False,
) -> Path:
    """导入一个 skill 目录(须含 SKILL.md)→ skills/<name>/;返回 canonical 目录。"""
    src_dir = Path(src_dir).resolve()
    skill_md = src_dir / "SKILL.md"
    if not skill_md.exists():
        raise ImportError_(f"源目录无 SKILL.md: {src_dir}")

    raw = skill_md.read_bytes()
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ImportError_(f"SKILL.md 无 frontmatter 边界: {skill_md}")
    fm = yaml.safe_load(m.group("fm").decode("utf-8"))
    if not isinstance(fm, dict):
        raise ImportError_(f"frontmatter 不是 YAML mapping: {skill_md}")
    body = m.group("body")

    name = str(fm.get("name") or src_dir.name)
    description = fm.get("description")
    if not description:
        raise ImportError_(f"frontmatter 缺 description(必填): {skill_md}")

    # 双语: _zh 直传(QwenWorkCN), _cn 映射到 canonical _zh(TeleAgent)
    description_zh = fm.get("description_zh") or fm.get("description_cn")
    name_zh = fm.get("name_zh") or fm.get("name_cn")

    # native_agent: 显式 > 路径探测
    native = agent
    if native is None and machines is not None:
        native = detect_source_agent(src_dir, machines, machine)

    ir = SkillIR(
        name=name,
        description=str(description),
        body=body,
        level=Level(level),
        native_agent=native,
        description_zh=str(description_zh) if description_zh else None,
        name_zh=str(name_zh) if name_zh else None,
        version=str(fm["version"]) if fm.get("version") is not None else None,
        license=str(fm["license"]) if fm.get("license") is not None else None,
    )

    dst = repo_root / "skills" / name
    if dst.exists():
        if not force:
            raise ImportError_(f"canonical 已存在 {dst}(--force 覆盖)")
        shutil.rmtree(dst)
    dst.mkdir(parents=True)

    # canonical SKILL.md(body bytes 原样)
    emit_canonical(ir, dst / "SKILL.md")

    # 其余文件/子目录保真镜像
    for e in sorted(src_dir.iterdir()):
        if e.name == "SKILL.md":
            continue
        d = dst / e.name
        if e.is_symlink():
            d.symlink_to(e.resolve())
        elif e.is_dir():
            shutil.copytree(e, d)
        else:
            shutil.copy2(e, d)

    # Agent 专有字段 → overrides
    leftovers = {k: v for k, v in fm.items() if k not in _CANONICAL_FIELDS
                 and k not in ("description_cn", "name_cn")  # 已映射
                 and v is not None}
    if leftovers:
        import tomli_w

        ov_dir = dst / ".agent_overrides"
        ov_dir.mkdir(exist_ok=True)
        ov_file = ov_dir / f"{agent or native or '_unknown'}.toml"
        ov_file.write_text(tomli_w.dumps(leftovers), encoding="utf-8")

    return dst


def import_git_url(url: str, repo_root: Path, **kw) -> list[Path]:
    """git clone --depth 1 到临时目录, 导入其中所有含 SKILL.md 的 skill 目录。"""
    with tempfile.TemporaryDirectory(prefix="skillhub-add-") as td:
        tmp = Path(td) / "src"
        r = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(tmp)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise ImportError_(f"git clone 失败: {r.stderr.strip()[:300]}")
        # 根目录本身是 skill?
        cands = []
        if (tmp / "SKILL.md").exists():
            cands.append(tmp)
        else:  # 仓库是 skills 集合: 每个含 SKILL.md 的一级子目录
            cands = sorted(p.parent for p in tmp.glob("*/SKILL.md"))
        if not cands:
            raise ImportError_(f"{url} 里没找到任何 SKILL.md")
        return [import_skill(c, repo_root, **kw) for c in cands]
