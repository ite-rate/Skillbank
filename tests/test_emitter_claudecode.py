"""ClaudeCode emitter 单元测试 + 零损耗保留 + 字段映射验证。

重点:
- emitted SKILL.md 的 body 与 IR body 字节一致(前言拼到外面, body 不动)
- frontmatter 含 disable-model-invocation: true 当 level manual/experimental
- description 不截断(Claude Code 无硬限)
- canonical 元字段(native_agent/requires/description_zh 等)不污染 Claude frontmatter
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from skillbank.agents import AgentsConfig
from skillbank.emitters.claudecode import ClaudeCodeEmitter
from skillbank.ir import Level, SkillIR

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
    name: str = "demo",
    description: str = "a demo skill",
    body: bytes = b"## Step 1\n\ndo something\n",
    level: Level = Level.AUTO,
    native_agent: str | None = None,
    requires: list[str] | None = None,
    description_zh: str | None = None,
) -> SkillIR:
    return SkillIR(
        name=name,
        description=description,
        body=body,
        level=level,
        native_agent=native_agent,
        requires=requires or [],
        description_zh=description_zh,
    )


def test_claude_body_identical_after_emit(agents_cfg, tmp_path, canon):
    """body 字节经过 emitter deploy 后仍与原 IR body 字节等值(前言在外)。"""
    body = b"## Step 1\n\nLine A\nLine B\r\nCRLF preserved\r\n"
    ir = _make_ir(body=body, level=Level.AUTO)
    cfg = agents_cfg.get("ClaudeCode")

    deploy_root = tmp_path / "claude-skills"
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, deploy_root, cfg, tmp_path / "canonical" / "demo")

    # 读回 deployed SKILL.md, 切出 body(从第二个 '---\\n' 之后)
    raw = result.deployed_path.read_bytes()
    # canonical frontmatter 边界正则也可用; 这里手算简单检验
    parts = raw.split(b"---\n", 2)
    assert len(parts) == 3, "deployed SKILL.md 应有 frontmatter 边界"
    # parts[1] 是 frontmatter yaml, parts[2] 是 body (可能含前言)
    assert parts[2].endswith(body), "body 应完整保留在 deployed SKILL.md 末尾"
    # 进一步: body 段在前言之后, 直接 substring 检验
    body_pos = raw.find(body)
    assert body_pos != -1 and raw[body_pos:] == body, \
        f"body 字节必须出现在 deployed 文件末尾且与原 IR 等值\ngot tail: {raw[body_pos:]!r}"


def test_claude_crlf_preserved_in_deployed(agents_cfg, tmp_path, canon):
    body = b"CRLF\r\nmust not be LF\n"
    ir = _make_ir(body=body)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    raw = result.deployed_path.read_bytes()
    assert b"CRLF\r\nmust not be LF\n" in raw, "CRLF body 被 emitter 改成 LF — 零损耗破"


def test_claude_auto_level_no_disable_invoke(agents_cfg, tmp_path, canon):
    """level=auto -> frontmatter 不写 disable-model-invocation(允许模型自动触发)。"""
    ir = _make_ir(level=Level.AUTO)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    raw = result.deployed_path.read_bytes()
    parts = raw.split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm == {"name": "demo", "description": "a demo skill"}, \
        f"auto 级 frontmatter 应只剩 name+description, got: {fm}"
    assert "disable-model-invocation" not in fm


def test_claude_manual_level_emits_disable_invoke_true(agents_cfg, tmp_path, canon):
    """level=manual -> frontmatter 加 disable-model-invocation: true。"""
    ir = _make_ir(level=Level.MANUAL)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "demo"
    assert fm["disable-model-invocation"] is True, \
        f"manual 级应映射 disable-model-invocation: true, got fm: {fm}"


def test_claude_experimental_level_also_emits_disable_invoke(agents_cfg, tmp_path, canon):
    """level=experimental -> 与 manual 同样禁止自动触发。"""
    ir = _make_ir(level=Level.EXPERIMENTAL)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["disable-model-invocation"] is True


def test_claude_canonical_meta_fields_not_polluting(agents_cfg, tmp_path, canon):
    """canonical 的 native_agent/requires/description_zh/name_zh/version/license 不写进 Claude frontmatter。"""
    ir = _make_ir(
        native_agent="TeleAgent",
        requires=["image_generation", "file_write"],
        description_zh="中文描述",
    )
    ir.name_zh = "中文名"
    ir.version = "1.0.0"
    ir.license = "MIT"
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    for forbidden in ("native_agent", "requires", "description_zh", "name_zh", "version", "license", "level"):
        assert forbidden not in fm, f"canonical 元字段 {forbidden!r} 污染 Claude frontmatter"


def test_claude_long_description_not_truncated(agents_cfg, tmp_path, canon):
    """Claude Code 无 description 字符限制; 长描述应原样保留。"""
    long_desc = "A very long description. " * 100  # > 2000 chars
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["description"] == long_desc, "Claude description 被截断 — 不应有长度限制"


def test_claude_frontmatter_quote_preserved_when_parsed(tmp_path, agents_cfg):
    """从带引号真实 canonical 解析(字段级透传): 未截断 description 引号保留。

    回归: 部署侧 safe_dump 全量重建曾去掉引号, 导致部署产物与 canonical 字节不一致。
    """
    from skillbank.parsers.canonical import parse_canonical

    canon = tmp_path / "canonical" / "demo"
    canon.mkdir(parents=True)
    content = (
        "---\n"
        "name: demo\n"
        "description: 'Quoted description with (1) parens (2) and (3) list.'\n"
        "level: manual\n"
        "---\n"
        "# body\n"
    )
    (canon / "SKILL.md").write_text(content, encoding="utf-8")
    ir = parse_canonical(canon / "SKILL.md")
    assert ir.fm_raw is not None, "parse_canonical 应保留 frontmatter 原始字节"

    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", agents_cfg.get("ClaudeCode"), canon)
    raw = result.deployed_path.read_text("utf-8")

    assert "description: 'Quoted description with (1) parens (2) and (3) list.'" in raw, \
        "部署产物 description 原始引号被丢掉(字段级透传应保留)"
    assert "disable-model-invocation: true" in raw, "manual 级应翻译成 disable-model-invocation"
    # canonical 的 level 不应出现在部署 frontmatter
    parts = raw.split("---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert "level" not in fm, "canonical level 字段不应污染部署产物"



