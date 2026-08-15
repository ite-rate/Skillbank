"""M3 — TeleAgent / QwenWorkCN / Codex / Hermes 四个 cp emitter 测试。

每个 emitter 的关键行为:
- TeleAgent : 中文 _zh(canonical) 镜像到 _cn; level -> enabled_at: false
- QwenWorkCN: 中文 _zh 直传(同名); level -> enabled_at: false; 不取作废字段
- Codex     : description > 1024 截断加 ...; level -> disable-model-invocation: true
- Hermes    : 部署到 <category>/<name>/(默认 imported/);
              description > 1024 截断; level -> metadata.hermes.disable-model-invocation: true;
              总文件 > 100000 字符 -> skipped + 不写盘
所有 emitter: body 字节与 IR.body 等值(零损耗硬约束)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from skillbank.agents import AgentsConfig
from skillbank.emitters.codex import CodexEmitter, CODEX_DESC_MAX
from skillbank.emitters.hermes import HermesEmitter, HERMES_FILE_MAX
from skillbank.emitters.qwenworkcn import QwenWorkCNEmitter
from skillbank.emitters.teleagent import TeleAgentEmitter
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
    body: bytes = b"## Step\n\ndo something\n",
    level: Level = Level.AUTO,
    description: str = "a skill",
    description_zh: str | None = None,
    name_zh: str | None = None,
    requires: list[str] | None = None,
    native_agent: str | None = None,
) -> SkillIR:
    return SkillIR(
        name="demo",
        description=description,
        body=body,
        level=level,
        description_zh=description_zh,
        name_zh=name_zh,
        requires=requires or [],
        native_agent=native_agent,
    )


def _split_frontmatter_body(raw: bytes) -> tuple[dict, bytes]:
    """split deployed SKILL.md -> (frontmatter dict, body bytes)。"""
    m = re.match(rb"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z", raw, re.DOTALL)
    assert m, "deployed SKILL.md 应有 frontmatter 边界"
    return yaml.safe_load(m.group("fm")), m.group("body")


# --- TeleAgent ---


def test_teleagent_zh_desc_mirrored_to_cn(agents_cfg, tmp_path, canon):
    """canonical description_zh -> TeleAgent description_cn 镜像生成。"""
    ir = _make_ir(description_zh="创意海报设计", name_zh="创意海报设计")
    cfg = agents_cfg.get("TeleAgent")
    em = TeleAgentEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, body = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["description_cn"] == "创意海报设计"
    assert fm["name_cn"] == "创意海报设计"
    # body 零损耗
    assert body == ir.body


def test_teleagent_manual_level_enabled_at_false(agents_cfg, tmp_path, canon):
    """TeleAgent manual/experimental -> enabled_at: false(借用 QwenWork 同字段语义)。"""
    ir = _make_ir(level=Level.MANUAL)
    cfg = agents_cfg.get("TeleAgent")
    em = TeleAgentEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm.get("enabled_at") is False


def test_teleagent_canonical_meta_not_polluting(agents_cfg, tmp_path, canon):
    """native_agent/requires/version/license 不写入 TeleAgent frontmatter。"""
    ir = _make_ir(native_agent="Hermes", requires=["web_search"])
    ir.version = "1.0"
    ir.license = "MIT"
    cfg = agents_cfg.get("TeleAgent")
    em = TeleAgentEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    for forbidden in ("native_agent", "requires", "version", "license", "level"):
        assert forbidden not in fm


# --- QwenWorkCN ---


def test_qwenworkcn_zh_desc_direct_pass(agents_cfg, tmp_path, canon):
    """canonical description_zh 与 QwenWorkCN 同名, 直传(不镜像)。"""
    ir = _make_ir(description_zh="中文", name_zh="名")
    cfg = agents_cfg.get("QwenWorkCN")
    em = QwenWorkCNEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["description_zh"] == "中文"
    assert fm["name_zh"] == "名"
    # 不存在 description_cn / name_cn(那是 TeleAgent 的镜像后缀)
    assert "description_cn" not in fm
    assert "name_cn" not in fm


def test_qwenworkcn_no_obsolete_fields(agents_cfg, tmp_path, canon):
    """agents.toml 里 keep_native_fields 配的字段(native_agent 等)不主动写出去(防污染)。"""
    ir = _make_ir()
    ir.native_agent = "ClaudeCode"
    cfg = agents_cfg.get("QwenWorkCN")
    em = QwenWorkCNEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    # 点名作废字段(属 Qwen Code CLI 开发者版, QwenWorkCN 没有)
    for forbidden in ("priority", "paths", "user-invocable", "source"):
        assert forbidden not in fm
    # canonical 元字段也不污染
    for forbidden in ("native_agent", "level"):
        assert forbidden not in fm


# --- Codex ---


def test_codex_description_truncated_at_1024(agents_cfg, tmp_path, canon):
    """description > 1024 -> 截断加 '...' 尾。"""
    long_desc = "x" * (CODEX_DESC_MAX + 500)
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, body = _split_frontmatter_body(result.deployed_path.read_bytes())
    # 截断后含 ..., 总字符数 <= 1024
    assert fm["description"].endswith("..."), "截断应后缀省略号"
    assert len(fm["description"]) <= CODEX_DESC_MAX, "截断后长度不得超过 1024"
    # 截了 500 多字
    assert len(fm["description"]) < len(long_desc)
    # body 不动
    assert body == ir.body
    assert "truncated" in result.note


def test_codex_description_at_boundary_not_truncated(agents_cfg, tmp_path, canon):
    """description 恰好等于 1024 -> 不截(保留全长, 无 ...)。"""
    boundary_desc = "y" * CODEX_DESC_MAX
    ir = _make_ir(description=boundary_desc)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["description"] == boundary_desc
    assert "..." not in fm["description"]
    assert result.note == ""


def test_codex_unicode_chars_counted_not_bytes(agents_cfg, tmp_path, canon):
    """1024 字符限制是 Unicode 字符数, 不是字节数。中文+ASCII 混合算字符数。"""
    # 1020 个中文 + 3 个 'a' + ... = 1023 + ... 不截
    desc = "中" * 1020 + "aaa"  # 1023 chars
    ir = _make_ir(description=desc)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["description"] == desc, "1023 字符不应截"
    # 现在 1025 中文字符超限
    ir2 = _make_ir(description="中" * 1025)
    result2 = em.deploy(ir2, tmp_path / "x2", cfg, canon)
    fm2, _ = _split_frontmatter_body(result2.deployed_path.read_bytes())
    assert len(fm2["description"]) <= CODEX_DESC_MAX


def test_codex_manual_level_disable_model_invocation_true(agents_cfg, tmp_path, canon):
    ir = _make_ir(level=Level.EXPERIMENTAL)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["disable-model-invocation"] is True


# --- Hermes ---


def test_hermes_deploys_into_category_subdir(agents_cfg, tmp_path, canon):
    """Hermes 默认走 imported/<name>/ 子目录(决策:不污染 creative/)。"""
    ir = _make_ir()
    cfg = agents_cfg.get("Hermes")
    em = HermesEmitter()
    result = em.deploy(ir, tmp_path / "hermes-skills", cfg, canon)
    assert "imported/demo/SKILL.md" in str(result.deployed_path)
    assert result.method == "cp"


def test_hermes_body_zero_loss_in_category(agents_cfg, tmp_path, canon):
    """部署进 imported/ 子目录的 SKILL.md body 仍与原 IR.body 字节等值。"""
    body = b"## Hermes body\r\nCRLF\r\npreserved\n"
    ir = _make_ir(body=body)
    cfg = agents_cfg.get("Hermes")
    em = HermesEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, deployed_body = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert deployed_body == body


def test_hermes_manual_level_metadata_hermes_namespace(agents_cfg, tmp_path, canon):
    """level manual -> frontmatter 加 metadata.hermes.disable-model-invocation: true。"""
    ir = _make_ir(level=Level.MANUAL)
    cfg = agents_cfg.get("Hermes")
    em = HermesEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert fm["metadata"]["hermes"]["disable-model-invocation"] is True


def test_hermes_description_truncated(agents_cfg, tmp_path, canon):
    """Hermes description 也有 1024 截断。"""
    long_desc = "z" * (CODEX_DESC_MAX + 100)
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("Hermes")
    em = HermesEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    fm, _ = _split_frontmatter_body(result.deployed_path.read_bytes())
    assert len(fm["description"]) <= CODEX_DESC_MAX
    assert fm["description"].endswith("...")


def test_hermes_oversize_file_skipped(agents_cfg, tmp_path, canon):
    """deployed SKILL.md 总字符数 > 100_000 -> skipped + 不写盘 + 加 note。"""
    # body 100_500 字符 -> 部署后总长肯定超 100_000(Hermes 限)
    huge_body = ("line\n" * 20_100).encode()   # ~100_500 bytes
    assert len(huge_body) > HERMES_FILE_MAX
    ir = _make_ir(body=huge_body)
    cfg = agents_cfg.get("Hermes")
    em = HermesEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    assert result.method == "skipped", f"超大 body 应 skipped, got method={result.method!r}"
    assert "file_size_max" in result.note or "exceeded" in result.note
    # 不写盘: 目标 skill 目录(imported/<name>/)不应被创建
    target_dir = tmp_path / "x" / "imported" / "demo"
    assert not target_dir.exists(), "skipped 不应创建目标 skill 目录"


def test_hermes_oversize_one_agent_while_others_sync(tmp_path, agents_cfg, canon):
    """Hermes 超限跳过不影响其他 Agent(端到端语义, 这里直接单独验 Hermes 一种)。"""
    # 假设其它 Agent 没有 file_size_max 限制, 不会被跳过 — Codex 没有 file_size_max 限制
    huge_body = ("line\n" * 20_100).encode()
    ir = _make_ir(body=huge_body)
    # Codex 走 cp, body 任意长度都可
    codex_cfg = agents_cfg.get("Codex")
    codex_em = CodexEmitter()
    result_codex = codex_em.deploy(ir, tmp_path / "codex", codex_cfg, canon)
    assert result_codex.method == "cp"
    assert result_codex.deployed_path.exists()
    # Hermes 应 skipped
    hermes_cfg = agents_cfg.get("Hermes")
    hermes_em = HermesEmitter()
    result_hermes = hermes_em.deploy(ir, tmp_path / "hermes", hermes_cfg, canon)
    assert result_hermes.method == "skipped"

# --- P0 #4: Codex 截断优先保留触发关键词 ---

def test_codex_truncate_preserves_use_when_trigger(agents_cfg, tmp_path, canon):
    """长 description 含 "Use when ..." 触发短语, 截断后应保留末段(触发短语所在整句)。"""
    # 前部 1100 字无意义填充 + Use when 触发句
    long_desc = "x" * 1100 + ". Use when the user asks to generate a poster."
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x", cfg, canon)
    import re, yaml
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    desc = fm["description"]
    assert len(desc) <= CODEX_DESC_MAX, "截断后长度应 ≤ 1024"
    assert "Use when the user asks to generate a poster." in desc, \
        f"触发短语应保留, got tail: {desc[-80:]!r}"


def test_codex_truncate_no_trigger_plain_cut(agents_cfg, tmp_path, canon):
    """无触发短语时退化为普通末尾截 + ...(保持原行为)。"""
    long_desc = "纯填充内容没有任何触发关键词。" * 200  # 没触发短语
    ir = _make_ir(description=long_desc)
    cfg = agents_cfg.get("Codex")
    em = CodexEmitter()
    result = em.deploy(ir, tmp_path / "x2", cfg, canon)
    import re, yaml
    parts = result.deployed_path.read_bytes().split(b"---\n", 2)
    fm = yaml.safe_load(parts[1])
    assert len(fm["description"]) <= CODEX_DESC_MAX
    assert fm["description"].endswith("...")
