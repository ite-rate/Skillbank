"""M4 — ZCode(软链) + kimi-code(cp) emitter 测试。

ZCode 三态:
- 干净目标(不存在) -> 软链建到 SkillHub canonical
- 已是软链(可能指 claude 旧的) -> unlink 后重链到 SkillHub canonical
- 真实目录(archify 类) -> deferred, 不动, 加 note 提示 zcode-cleanup
ZCode frontmatter transform 与 Claude 同形(name+description+disable-model-invocation)

kimi:
- cp 到 ~/.kimi-code/skills/<name>/ + Anthropic Skill 子集 frontmatter
- level manual 时 kimi 无 disable_invoke_field, 不写额外字段
- body 零损耗(deployed body 等于 IR body)
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import yaml

from skillhub.agents import AgentsConfig
from skillhub.emitters.kimi import KimiEmitter
from skillhub.emitters.zcode import ZCodeEmitter
from skillhub.ir import Level, SkillIR

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def agents_cfg():
    return AgentsConfig.load(REPO_ROOT / "agents.toml")


@pytest.fixture()
def canon(tmp_path):
    """真实存在的 canonical skill 目录(write_resources 全结构镜像需要)。"""
    d = tmp_path / "canonical" / "demo"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(b"---\nname: demo\ndescription: a skill\nlevel: auto\n---\n## body\n")
    return d


def _make_ir(
    body: bytes = b"## Step\n\ndo thing\n",
    level: Level = Level.AUTO,
    description: str = "a skill",
    native_agent: str | None = None,
    requires: list[str] | None = None,
) -> SkillIR:
    return SkillIR(
        name="demo",
        description=description,
        body=body,
        level=level,
        native_agent=native_agent,
        requires=requires or [],
    )


def _split_fm_body(raw: bytes) -> tuple[dict, bytes]:
    m = re.match(rb"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z", raw, re.DOTALL)
    assert m, "deployed SKILL.md 应有 frontmatter 边界"
    return yaml.safe_load(m.group("fm")), m.group("body")


# --- ZCode 软链三态 ---


def test_zcode_clean_target_symlinked(agents_cfg, tmp_path, canon):
    """干净目标(~/.zcode/skills/demo 不存在) -> 软链建到 SkillHub canonical。"""
    ir = _make_ir()
    cfg = agents_cfg.get("ZCode")
    em = ZCodeEmitter()

    # canonical skill dir(M2 实测时构造一次)
    canonical = canon
    deploy_root = tmp_path / "zcode-skills"
    deploy_root.mkdir()
    result = em.deploy(ir, deploy_root, cfg, canonical)
    target = deploy_root / "demo"
    assert target.is_symlink(), "干净目标应由 symlink 建"
    assert os.readlink(target) == str(canonical.resolve()), \
        f"软链应指向 canonical dir, got {os.readlink(target)}"
    assert result.method == "ln"
    assert "symlinked to SkillHub canonical" in result.note


def test_zcode_existing_symlink_relinked(agents_cfg, tmp_path, canon):
    """已是软链(可能指 claude 旧版) -> unlink 后重链到 SkillHub canonical(单一来源)。"""
    ir = _make_ir()
    cfg = agents_cfg.get("ZCode")
    em = ZCodeEmitter()

    canonical = canon
    deploy_root = tmp_path / "zcode-skills"
    deploy_root.mkdir()
    target = deploy_root / "demo"

    # 预置一个"指向 claude 的旧软链"
    fake_claude = tmp_path / "claude-skills" / "demo"
    fake_claude.mkdir(parents=True)
    (fake_claude / "SKILL.md").write_bytes(b"---\nname: demo\ndescription: old\n---\n")
    target.symlink_to(fake_claude.resolve())
    assert target.is_symlink()

    result = em.deploy(ir, deploy_root, cfg, canonical)
    assert target.is_symlink(), "重链后仍应软链"
    assert os.readlink(target) == str(canonical.resolve()), "软链应已指向 SkillHub canonical"
    assert result.note == "relinked symlink -> SkillHub canonical"


def test_zcode_real_dir_deferred_not_touched(agents_cfg, tmp_path, canon):
    """真实目录(archify 类, 不是软链) -> deferred, 不删不动, 加 note 提 zcode-cleanup。"""
    ir = _make_ir()
    cfg = agents_cfg.get("ZCode")
    em = ZCodeEmitter()

    canonical = canon
    deploy_root = tmp_path / "zcode-skills"
    deploy_root.mkdir()
    target = deploy_root / "demo"
    # 预置一个"用户真实目录"(archify 类)
    target.mkdir()
    (target / "SKILL.md").write_bytes(b"-- ORIGINAL USER FILE --\n")
    original_inner = (target / "SKILL.md").read_bytes()

    result = em.deploy(ir, deploy_root, cfg, canonical)
    assert result.method == "deferred", "真实目录应 deferred, 不软链不写盘"
    assert "REAL DIR" in result.note and "zcode-cleanup" in result.note

    # 不动用户真实副本
    assert not target.is_symlink(), "真实目录不应被改成软链"
    assert (target / "SKILL.md").read_bytes() == original_inner, \
        "真实目录里的 SKILL.md 必须保持原状, emitter 不可覆盖"


# --- kimi cp ---


def test_kimi_deploys_to_kimi_code_skills(agents_cfg, tmp_path, canon):
    """kimi cp 到 ~/.kimi-code/skills/<name>/, install_dir 与 agents.toml 配置一致。"""
    ir = _make_ir()
    cfg = agents_cfg.get("kimi-code")
    assert cfg.install_dir == "~/.kimi-code/skills", \
        f"kimi install_dir 应已被 M4 实测改为 ~/.kimi-code/skills, got {cfg.install_dir}"
    em = KimiEmitter()
    result = em.deploy(ir, tmp_path / "kimi-skills", cfg, canon)
    assert result.method == "cp"
    assert result.deployed_path.parent.name == "demo"
    assert result.deployed_path.name == "SKILL.md"


def test_kimi_body_zero_loss(agents_cfg, tmp_path, canon):
    """deployed body 与 IR body 字节等值(含 CRLF 防规整)。"""
    body = b"kimi body\r\nwith CRLF\n"
    ir = _make_ir(body=body)
    cfg = agents_cfg.get("kimi-code")
    em = KimiEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    _, deployed_body = _split_fm_body(result.deployed_path.read_bytes())
    assert deployed_body == body


def test_kimi_frontmatter_minimal_subset(agents_cfg, tmp_path, canon):
    """kimi frontmatter 只剩 name + description; canonical 元字段不污染。"""
    ir = _make_ir(native_agent="Hermes", requires=["web_search"])
    ir.version = "1.0"
    ir.license = "MIT"
    cfg = agents_cfg.get("kimi-code")
    em = KimiEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_fm_body(result.deployed_path.read_bytes())
    assert set(fm.keys()) == {"name", "description"}, f"kimi fm 应只剩 name+description, got {set(fm)}"
    for forbidden in ("native_agent", "requires", "version", "license", "level"):
        assert forbidden not in fm


def test_kimi_manual_level_no_disable_invoke_field(agents_cfg, tmp_path, canon):
    """kimi 配置里 disable_invoke_field is None; manual 级不写额外 frontmatter 字段。"""
    ir = _make_ir(level=Level.MANUAL)
    cfg = agents_cfg.get("kimi-code")
    assert cfg.disable_invoke_field is None, "kimi 不应配 frontmatter 禁止触发字段"
    em = KimiEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_fm_body(result.deployed_path.read_bytes())
    assert "disable-model-invocation" not in fm
    assert "enabled_at" not in fm
    assert set(fm.keys()) == {"name", "description"}, "manual 级也不应给 kimi 加额外字段"