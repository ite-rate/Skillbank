"""Emitter base — 7 个 Agent emitter 统一接口 + 公共 frontmatter 重组逻辑。

emitter 输出格式(全部 Agent 都遵循):
    b'---\\n' + yaml_frontmatter_dict + b'---\\n' + maybe_prompt_bytes + ir.body

各 Agent override:
- transform_frontmatter(ir, cfg) -> dict: 重排 frontmatter 字段为该 Agent 兼容子集
- deploy(ir, target_path, ...): cp 写 SKILL.md + resources(全部 Agent 均 cp)

公共逻辑(放在 base):
- 拼最终 bytes (frontmatter + 顶前言 + body)
- 目录创建 / cp
- frontmatter yaml 序化(allow_unicode, sort_keys=False 保顺序)
- 描述截断(各 Agent emitter 不重写)
"""

from __future__ import annotations

import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from skillbank.agents import AgentConfig
from skillbank.ir import SkillIR

__all__ = ["EmitterResult", "BaseEmitter", "emit_frontmatter_block",
           "edit_frontmatter_fields"]

# 顶层字段行: `key:` 开头且行首无缩进。block scalar/缩进续行属于上一个字段。
_TOP_LEVEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")


def _dump_field(key: str, value) -> str:
    """按 safe_dump 风格序列化单个字段(供新增/变更字段用)。"""
    block = yaml.safe_dump(
        {key: value}, sort_keys=False, allow_unicode=True,
        default_flow_style=False, width=10_000,
    )
    return block.rstrip("\n")


def edit_frontmatter_fields(raw_text: str, fm_orig: dict, new: dict) -> str:
    """字段级透传: 未变更字段保原始字节, 仅重写变更/新增/删除字段。

    raw_text: frontmatter 原始文本(不含 --- 边界)。
    fm_orig:  原始解析出的 dict。
    new:      目标 frontmatter dict。

    规则:
    - 无任何语义变更 -> 原样返回(完美字节稳定)
    - 未变更字段 -> 保留原始行(含引号/缩进/顺序)
    - 变更/新增字段 -> 用 safe_dump 重写该字段
    - 删除字段(在 orig 不在 new) -> 丢弃
    """
    if new == fm_orig:
        return raw_text

    lines = raw_text.split("\n")
    # 定位每个顶层字段 `key:` 的行区间(含其块/续行/注释)。
    keys_ordered: list[str] = []
    key_start: dict[str, int] = {}
    for i, ln in enumerate(lines):
        m = _TOP_LEVEL_RE.match(ln)
        if m and not ln[:1].isspace():
            keys_ordered.append(m.group(1))
            key_start[m.group(1)] = i
    # 字段 i 的区间 = [start_i, start_{i+1})
    spans: dict[str, tuple[int, int]] = {}
    for j, key in enumerate(keys_ordered):
        end = key_start[keys_ordered[j + 1]] if j + 1 < len(keys_ordered) else len(lines)
        spans[key] = (key_start[key], end)

    blocks: list[str] = []
    for key in keys_ordered:
        if key not in new:
            continue  # 已删除字段 -> 丢弃
        s, e = spans[key]
        if fm_orig.get(key) == new[key]:
            blocks.append("\n".join(lines[s:e]))  # 未变 -> 保原始字节
        else:
            blocks.append(_dump_field(key, new[key]))  # 变更 -> 重写该字段
    for key in new:
        if key not in key_start:
            blocks.append(_dump_field(key, new[key]))  # 新增字段
    return "\n".join(blocks)


def emit_frontmatter_block(fm: dict, raw_text: Optional[str] = None,
                           fm_orig: Optional[dict] = None) -> bytes:
    """把 frontmatter dict 序化成 `---\\n<yaml>\\n---\\n` bytes。

    allow_unicode=True 让中文不转义; sort_keys=False 保用户字段顺序;
    width=10_000 防长行 description 被折成多行。

    传入 raw_text+fm_orig 时走字段级透传(未变更字段保原始字节, 引号不丢),
    否则 safe_dump 全量生成。
    """
    if raw_text is not None and fm_orig is not None:
        edited = edit_frontmatter_fields(raw_text, fm_orig, fm)
        yaml_bytes = (edited.rstrip("\n") + "\n").encode("utf-8")
    else:
        yaml_bytes = yaml.safe_dump(
            fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=10_000
        ).encode("utf-8")
    # yaml 输出末尾自带 \\n; 我们拼 `---\\n<yaml>---\\n`(yaml 后 \\n 即边界):
    return b"---\n" + yaml_bytes + b"---\n"


@dataclass
class EmitterResult:
    """emitter 一次 emit 的结果(给 manifest + CLI 展示用)。"""

    deployed_path: Path
    method: str             # cp | skipped
    note: str = ""          # 跳过/警告原因(file_size_max 超 / Agent 不在 machines 列表 等)


def _merge_override_field(fm_val, ov_val):
    """override 合并: dict 递归并集(emitter 已写值优先), 非 dict 保 emitter 值。

    场景: Hermes emitter 已写 metadata={hermes:{disable-model-invocation}}, overrides
    里还有 metadata.hermes.{tags, related_skills} —— 若整键跳过会丢市场/作者元数据。
    dict 递归合并让两边的 metadata.hermes 子键共存, 不互相覆盖。
    """
    if isinstance(fm_val, dict) and isinstance(ov_val, dict):
        merged = dict(fm_val)
        for k, v in ov_val.items():
            if k not in merged:
                merged[k] = v
            else:
                merged[k] = _merge_override_field(merged[k], v)
        return merged
    return fm_val  # emitter 已写字段优先, 不覆盖


def load_agent_overrides(canonical_skill_dir: Path, agent_name: str) -> dict:
    """从 .agent_overrides/<agent>.toml 读该 Agent 的专有字段(import 时抽的)。

    返回 dict(空则无 overrides)。这些字段是 Agent 专有的(install_source/
    skill_id/enabled_at/metadata.hermes 等), 不进 canonical, 但部署到原生
    Agent 时必须写回 deployed frontmatter —— 否则迁移后能力有损(grilling 原则)。
    """
    ov_file = Path(canonical_skill_dir) / ".agent_overrides" / f"{agent_name}.toml"
    if not ov_file.exists():
        return {}
    import tomllib
    with open(ov_file, "rb") as fh:
        return tomllib.load(fh)


def merge_agent_overrides(fm: dict, overrides: dict) -> dict:
    """把 Agent 专有 overrides 合并进部署 frontmatter。

    - override 键在 fm 里不存在 -> 直接加
    - 已存在且都是 dict -> 递归合并(metadata.hermes 子键共存)
    - 已存在且非 dict -> 保留 emitter 已写值(不覆盖)
    """
    merged = dict(fm)
    for k, v in overrides.items():
        if k not in merged:
            merged[k] = v
        elif isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _merge_override_field(merged[k], v)
    return merged


class BaseEmitter(ABC):
    """所有 Agent emitter 继承此基类。

    子类须实现:
        transform_frontmatter(ir, cfg) -> dict
        deploy(ir, deploy_root, cfg) -> EmitterResult

    base 提供:
        build_skill_md_bytes(ir, cfg) -> bytes   最终拼字节流
        write_skill_md(bytes, path)        普通文件写入
        write_resources(ir, target_skill_dir)    resources/ 拷贝
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @abstractmethod
    def transform_frontmatter(self, ir: SkillIR, cfg: AgentConfig) -> dict:
        """重排 frontmatter 字段为该 Agent 兼容子集(关键:去除 canonical 不该污染 Agent 的字段)。"""
        ...

    @abstractmethod
    def deploy(
        self, ir: SkillIR, deploy_root: Path, cfg: AgentConfig,
        canonical_skill_dir: Path,
    ) -> EmitterResult:
        """把 IR + 前言写到目标 Agent 目录的对应位置(cp)。"""
        ...

    # --- 公共 helper ---

    def build_skill_md_bytes(self, ir: SkillIR, cfg: AgentConfig,
                             canonical_skill_dir: Path | None = None) -> bytes:
        """frontmatter block + body 顶前言 + body 拼字节流。

        body bytes 不动, 直接跟在 frontmatter 后。
        如果给了 canonical_skill_dir, 会从 .agent_overrides/<agent>.toml 读
        该 Agent 专有字段叠加到 frontmatter(还原原生 Agent 能力)。
        """
        fm = self.transform_frontmatter(ir, cfg)
        # 叠加 Agent 专有字段(从 overrides 还原到 deployed frontmatter;
        # dict 递归合并, 让 metadata.hermes 等嵌套元数据与 emitter 写的字段共存)
        if canonical_skill_dir is not None:
            overrides = load_agent_overrides(canonical_skill_dir, cfg.name)
            fm = merge_agent_overrides(fm, overrides)
        # 字段级透传: 有 canonical 原始 frontmatter 时, 未被翻译/未改值的字段
        # (如 description 引号、name)保原始字节; 仅重写翻译字段/新增字段。
        raw_text = ir.fm_raw.decode("utf-8") if ir.fm_raw is not None else None
        return emit_frontmatter_block(fm, raw_text=raw_text, fm_orig=ir.fm_orig) + ir.body

    @staticmethod
    def write_skill_md(content: bytes, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    @staticmethod
    def write_resources(ir: SkillIR, target_skill_dir: Path, canonical_skill_dir: Path) -> None:
        """把 canonical skill 目录的完整结构保真同步到目标(除 SKILL.md / .agent_overrides)。

        真实 agent skill 的资源是任意结构(scripts/ references/ rooms/ _meta.json ...),
        且 SKILL.md body 里的相对路径引用必须继续有效 — 所以不能收拢进 resources/,
        必须原样镜像。同时删除目标端已不在源端的条目(防残留旧文件)。
        """
        src = Path(canonical_skill_dir)
        dst = Path(target_skill_dir)
        dst.mkdir(parents=True, exist_ok=True)
        skip = {"SKILL.md", ".agent_overrides"}

        src_entries = {e.name for e in src.iterdir()} - skip
        # 删目标端已不在源端的条目(SKILL.md 由 emitter 写, 不动)
        for e in list(dst.iterdir()):
            if e.name == "SKILL.md":
                continue
            if e.name not in src_entries:
                if e.is_symlink() or e.is_file():
                    e.unlink()
                else:
                    shutil.rmtree(e)
        # 拷源端条目(先清目标同名再拷, 保证内容一致)
        for name in sorted(src_entries):
            s = src / name
            d = dst / name
            if d.is_symlink() or d.is_file():
                d.unlink()
            elif d.exists():
                shutil.rmtree(d)
            if s.is_symlink():
                d.symlink_to(s.resolve())
            elif s.is_dir():
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

