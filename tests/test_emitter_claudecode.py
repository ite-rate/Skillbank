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

from skillhub.agents import AgentsConfig
from skillhub.capabilities import CapabilityMatrix
from skillhub.emitters.claudecode import ClaudeCodeEmitter
from skillhub.ir import Level, SkillIR
from skillhub.prompt_inject import inject_prompts

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def agents_cfg():
    return AgentsConfig.load(REPO_ROOT / "agents.toml")


@pytest.fixture()
def cap_matrix():
    return CapabilityMatrix.load(REPO_ROOT / "capabilities.toml")


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


def test_claude_body_identical_after_emit(agents_cfg, tmp_path):
    """body 字节经过 emitter deploy 后仍与原 IR body 字节等值(前言在外)。"""
    body = b"## Step 1\n\nLine A\nLine B\r\nCRLF preserved\r\n"
    ir = _make_ir(body=body, level=Level.AUTO)
    cfg = agents_cfg.get("ClaudeCode")

    deploy_root = tmp_path / "claude-skills"
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, deploy_root, cfg, tmp_path / "canonical" / "demo", prompt_bytes=b"")

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


def test_claude_crlf_preserved_in_deployed(agents_cfg, tmp_path):
    body = b"CRLF\r\nmust not be LF\n"
    ir = _make_ir(body=body)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo", prompt_bytes=b"")
    raw = result.deployed_path.read_bytes()
    assert b"CRLF\r\nmust not be LF\n" in raw, "CRLF body 被 emitter 改成 LF — 零损耗破"


def test_claude_auto_level_no_disable_invoke(agents_cfg, tmp_path):
    """level=auto -> frontmatter 不写 disable-model-invocation(允许模型自动触发)。"""
    ir = _make_ir(level=Level.AUTO)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo")
    raw = result.deployed_path.read_bytes()
    parts = raw.split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm == {"name": "demo", "description": "a demo skill"}, \
        f"auto 级 frontmatter 应只剩 name+description, got: {fm}"
    assert "disable-model-invocation" not in fm


def test_claude_manual_level_emits_disable_invoke_true(agents_cfg, tmp_path):
    """level=manual -> frontmatter 加 disable-model-invocation: true。"""
    ir = _make_ir(level=Level.MANUAL)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo")
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["name"] == "demo"
    assert fm["disable-model-invocation"] is True, \
        f"manual 级应映射 disable-model-invocation: true, got fm: {fm}"


def test_claude_experimental_level_also_emits_disable_invoke(agents_cfg, tmp_path):
    """level=experimental -> 与 manual 同样禁止自动触发。"""
    ir = _make_ir(level=Level.EXPERIMENTAL)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo")
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["disable-model-invocation"] is True


def test_claude_canonical_meta_fields_not_polluting(agents_cfg, tmp_path):
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
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo")
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    for forbidden in ("native_agent", "requires", "description_zh", "name_zh", "version", "license", "level"):
        assert forbidden not in fm, f"canonical 元字段 {forbidden!r} 污染 Claude frontmatter"


def test_claude_long_description_not_truncated(agents_cfg, tmp_path):
    """Claude Code 无 description 字符限制; 长描述应原样保留。"""
    long_desc = "A very long description. " * 100  # > 2000 chars
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("ClaudeCode")
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo")
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert fm["description"] == long_desc, "Claude description 被截断 — 不应有长度限制"


def test_claude_prompt_injection_with_capabilities(agents_cfg, cap_matrix, tmp_path):
    """requires 中 unsupported 能力 + native_agent 前言应当拼在 body 前。

    用真实 capabilities.toml 矩阵: ClaudeCode 的 image_generation = unsupported,
    取 requires=[image_generation], 期望出现"建议换 Agent"硬警告。
    """
    ir = _make_ir(
        native_agent="Hermes",
        requires=["image_generation"],
        body=b"## generate image\n\ndo it\n",
    )
    cfg = agents_cfg.get("ClaudeCode")
    prompt_bytes = inject_prompts(ir, "ClaudeCode", cap_matrix)

    # 期望前言含两种: native_agent 提示 + image_generation unsupported 警告
    assert "\U0001faa7".encode() in prompt_bytes, "native_agent 来源提示符号未出现"
    assert "\u26a0\ufe0f".encode() in prompt_bytes, "能力缺失硬警告未注入"
    assert b"image_generation" in prompt_bytes, "缺失能力名未出现在前言"
    assert b"Hermes" in prompt_bytes, "推荐 Agent Hermes 未出现在前言"

    # 通过 emitter deploy 写出来, body 在前言之后仍字节等值
    em = ClaudeCodeEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, tmp_path / "c" / "demo", prompt_bytes=prompt_bytes)
    raw = result.deployed_path.read_bytes()
    # body 必须完整出现在文件末尾(前言拼前)
    body_pos = raw.find(ir.body)
    assert body_pos != -1 and raw[body_pos:] == ir.body, "body 应完整出现在前言之后"


def test_claude_known_supported_capability_no_warning(agents_cfg, cap_matrix, tmp_path):
    """requires = [web_search] 时 ClaudeCode(SUPPORTED)应不注警告。"""
    assert cap_matrix.query("web_search", "ClaudeCode") == "supported"
    ir = _make_ir(requires=["web_search"], body=b"search the web\n")
    prompt_bytes = inject_prompts(ir, "ClaudeCode", cap_matrix)
    # native_agent=None, web_search=supported -> 前言应为空
    assert prompt_bytes == b"", f"supported 能力不应注入前言, got: {prompt_bytes!r}"