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

from skillbank.emitters.canonical import emit_canonical
from skillbank.ir import Level, SkillIR
from skillbank.machines import MachinesConfig
from skillbank.parsers.canonical import FRONTMATTER_RE

__all__ = ["ImportError_", "import_skill", "detect_source_agent", "import_git_url",
           "short_agent_code", "suggest_variant_name"]

# 导入失败统一抛 ValueError 语义(避免与内置 ImportError 混淆)
ImportError_ = ValueError

# Agent 名 -> 短唤(重名变体建议名用, 3-5 字符用户可识别)
_AGENT_SHORT = {
    "ClaudeCode": "claude",
    "ZCode": "zcode",
    "QwenWorkCN": "qwen",
    "TeleAgent": "tele",
    "Hermes": "hermes",
    "Codex": "codex",
    "kimi-code": "kimi",
}


def short_agent_code(agent: Optional[str]) -> str:
    if not agent:
        return "src"
    return _AGENT_SHORT.get(agent, agent.lower()[:5].replace("-", ""))


def suggest_variant_name(base_name: str, agent: Optional[str]) -> str:
    """不同 body 同名时:原名-native短码(e.g. docx-qwen / humanizer-hermes)。"""
    return f"{base_name}-{short_agent_code(agent)}"


# 跨 skill 目录的相对路径引用(见 "@" 这种通常是 HERMES 跨 skill 的插值)
_CROSS_DIR_RE = re.compile(r"\.\./[A-Za-z0-9_\-]+/")


def _strip_fm_body(skill_md_path: Path) -> bytes:
    """读 SKILL.md 切出 body 部分(用于重名时 body 比较)。

    frontmatter 边界正则用法同 parser;失败回退整文件(让比较自然走不算)。
    """
    raw = Path(skill_md_path).read_bytes()
    m = FRONTMATTER_RE.match(raw)
    return m.group("body") if m else raw


def scan_body_paths(body: bytes) -> list[str]:
    """扫 body, 找:
    - 绝对路径(/Users/ /home/ C:\\ ...)— 跨机迁移必断
    - ../ 跨 skill 目录的相对引用 — 部署到不同子目录布局后断裂
    返回人话警告描述列表(空表示没问题)。
    """
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return []
    warns: list[str] = []
    # Unix 绝对路径(空格或行首后跟 /Users/ /home/)或 Windows 盘符(C:\ D:\ E:\ ...)
    if re.search(r"(?:^|[\s\"'(])(/Users/|/home/|[A-Z]:\\)", text):
        # 抽样展示(用 .group() 最短匹;只用于诊断)
        m = re.search(r"((?:/Users/|/home/|/usr/|/opt/|/tmp/|/[a-zA-Z0-9_./-]+|[A-Z]:\\[^\s\n]+))", text)
        sample = m.group(1) if m else "..."
        warns.append(f"body 含写死的绝对路径({sample[:80]},跨机迁移必断)")
    cross = _CROSS_DIR_RE.findall(text)
    if cross:
        warns.append(f"body 含跨 skill 目录的相对引用({'../'.join(set(cross))[:60]},"
                     f"部署到 imported/ 或软链后可能失效)")
    return warns

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
    machine: Optional[str] = None,
    force: bool = False,
    rename_callback=None,
    auto_rename: bool = True,
) -> tuple[Path, list[str]]:
    """导入一个 skill 目录(须含 SKILL.md)→ skills/<name>/。

    返回 (canonical 目录, body 路径警告列表):警告描述人话字符串, [] 表示无。

    重名策略(用户拍板 2026-08-15):
    - 同 body 同名(软链共享同一份真身)       -> 静默去重;已存在的就是它,不交互
    - 不同 body 同名(客端真重名, e.g. docx 三家版) -> 交互改名;
        建议名 = 原名-native短码(e.g. docx-qwen)。rename_callback 决定终名
    - force=True  -> 同 body 也允许重入(重生成 canonical, 覆盖同 body 同名)
    """
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
    if native is None and machines is not None and machine is not None:
        native = detect_source_agent(src_dir, machines, machine)

    # === 重名处理 ===
    dst = repo_root / "skills" / name
    if dst.exists():
        existing_body = _strip_fm_body(dst / "SKILL.md")
        if existing_body == body and not force:
            # 同 body 同名:静默去重,返回已存在的(重复 import 不报错也不覆盖)
            return dst, [f"已存在同内容同名的 {dst.name}, 跳过(软链共享去重)"]
        if existing_body == body and force:
            ir_name = name  # 极少需要重写同 body, 允许
        else:
            # 不同 body 同名 -> 交互/自动改名
            suggested = suggest_variant_name(name, native)
            if rename_callback is not None:
                name = rename_callback(name, suggested, native or "")
            elif auto_rename:
                name = suggested
            else:
                raise ImportError_(
                    f"canonical 已存在且 body 不同: {dst}。"
                    f"建议名 {suggested}(本 import 仅在 CLI 交互/auto_rename=True 时生效)"
                )
            ir_name = name  # canonical 用新名
            dst = repo_root / "skills" / name
            if dst.exists() and not force:
                raise ImportError_(
                    f"改名后仍冲突 {dst}(--force 覆盖, 或用别的名)"
                )
    else:
        ir_name = name

    ir = SkillIR(
        name=ir_name,
        description=str(description),
        body=body,
        level=Level(level),
        native_agent=native,
        description_zh=str(description_zh) if description_zh else None,
        name_zh=str(name_zh) if name_zh else None,
        version=str(fm["version"]) if fm.get("version") is not None else None,
        license=str(fm["license"]) if fm.get("license") is not None else None,
    )

    if dst.exists() and force:
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

    warnings = scan_body_paths(body)
    return dst, warnings


def import_git_url(url: str, repo_root: Path, **kw) -> list[tuple[Path, list[str]]]:
    """git clone --depth 1 到临时目录, 导入其中所有含 SKILL.md 的 skill 目录。

    返回 [(canon_dir, warnings), ...]。
    """
    with tempfile.TemporaryDirectory(prefix="skillbank-add-") as td:
        tmp = Path(td) / "src"
        r = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(tmp)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise ImportError_(f"git clone 失败: {r.stderr.strip()[:300]}")
        cands = []
        if (tmp / "SKILL.md").exists():
            cands.append(tmp)
        else:
            cands = sorted(p.parent for p in tmp.glob("*/SKILL.md"))
        if not cands:
            raise ImportError_(f"{url} 里没找到任何 SKILL.md")
        return [import_skill(c, repo_root, **kw) for c in cands]
