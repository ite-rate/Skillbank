"""M6 importer 测试 — 反向导入:字段映射 / overrides / 资源镜像 / native 探测。

场景:
- TeleAgent 源: description_cn/name_cn → canonical description_zh/name_zh
- QwenWorkCN 源: description_zh 直传; 市场元数据(install_source/skill_id) → overrides toml
- body 零损耗: canonical SKILL.md body 与源 body 字节等值
- 资源镜像: 源 scripts/references 原样进 canonical(相对路径继续有效)
- native_agent: 按源路径前缀自动探测(machines.toml)
- 缺 description 报错; canonical 已存在报错(--force 覆盖)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import tomllib
import yaml

from skillbank.importer import detect_source_agent, import_skill
from skillbank.machines import MachinesConfig
from skillbank.parsers.canonical import parse_canonical

REPO_ROOT = Path(__file__).resolve().parents[1]


def _mk_agent_skill(base: Path, agent_dir: str, name: str, fm_lines: list[str],
                    body: bytes = b"## body\n\ncontent\r\n", files: dict[str, str] | None = None) -> Path:
    d = base / agent_dir / name
    d.mkdir(parents=True, exist_ok=True)
    content = "---\n" + "\n".join(fm_lines) + "\n---\n"
    (d / "SKILL.md").write_bytes(content.encode("utf-8") + body)
    for rel, c in (files or {}).items():
        f = d / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(c)
    return d


def _machines(tmp_path: Path) -> MachinesConfig:
    m = MachinesConfig()
    m.set_skills_dir("m1", "TeleAgent", str(tmp_path / "teleagent-skills"))
    m.set_skills_dir("m1", "QwenWorkCN", str(tmp_path / "qwen-skills"))
    return m


# --- TeleAgent 源 ---


def test_import_teleagent_cn_to_zh(tmp_path):
    home = tmp_path
    src = _mk_agent_skill(home, "teleagent-skills", "canvas-design", [
        "name: canvas-design",
        "description: Create visual art",
        'name_cn: "创意海报"',
        'description_cn: "创意海报设计工具"',
        "license: MIT",
    ], files={"prompts/p1.md": "# p1\n", "_meta.json": '{"x":1}'})

    repo = home / "repo"
    repo.mkdir()
    dst, _warns = import_skill(src, repo, machines=_machines(home), machine="m1")

    ir = parse_canonical(dst / "SKILL.md")
    assert ir.name == "canvas-design"
    assert ir.description == "Create visual art"
    assert ir.description_zh == "创意海报设计工具"      # _cn → canonical _zh
    assert ir.name_zh == "创意海报"
    assert ir.native_agent == "TeleAgent"              # 路径探测
    assert ir.license == "MIT"
    assert ir.level.value == "manual"                  # 默认 manual(未审不自动触发)
    assert ir.body == b"## body\n\ncontent\r\n"        # body 零损耗(CRLF 保留)

    # 资源镜像
    assert (dst / "prompts" / "p1.md").read_text() == "# p1\n"
    assert (dst / "_meta.json").exists()
    # 无 leftovers(license 是 canonical 字段)→ 无 overrides
    assert not (dst / ".agent_overrides").exists() or \
        not list((dst / ".agent_overrides").iterdir())


def test_import_qwen_market_metadata_to_overrides(tmp_path):
    home = tmp_path
    src = _mk_agent_skill(home, "qwen-skills", "bilibili-summary", [
        "name: bilibili-summary",
        "description: Summarize bilibili videos",
        "install_source: market",
        "skill_id: abc-123",
        "enabled_at: 2026-08-14T00:00:00Z",
        "version: 1.2.0",
    ])

    repo = home / "repo"
    repo.mkdir()
    dst, _warns = import_skill(src, repo, machines=_machines(home), machine="m1")

    ir = parse_canonical(dst / "SKILL.md")
    assert ir.native_agent == "QwenWorkCN"
    assert ir.version == "1.2.0"                        # canonical 认识 version
    # 市场元数据进 overrides, 不污染 canonical frontmatter
    ov = dst / ".agent_overrides" / "QwenWorkCN.toml"
    assert ov.exists()
    d = tomllib.loads(ov.read_text())
    assert d["install_source"] == "market"
    assert d["skill_id"] == "abc-123"
    # canonical SKILL.md 里没有这些
    fm_raw = (dst / "SKILL.md").read_bytes().split(b"---\n")[1]
    fm = yaml.safe_load(fm_raw)
    assert "install_source" not in fm and "skill_id" not in fm


# --- 边界 ---


def test_import_missing_description_raises(tmp_path):
    src = _mk_agent_skill(tmp_path, "some-skills", "bad", ["name: bad"])
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="description"):
        import_skill(src, repo)


def test_import_existing_canonical_same_body_silent_dedup(tmp_path):
    """同 body 同名(重复 import 同源) -> 静默去重返回,不 raise(用户拍板)。"""
    src = _mk_agent_skill(tmp_path, "some-skills", "dup", ["name: dup", "description: x"])
    repo = tmp_path / "repo"
    repo.mkdir()
    d1, _ = import_skill(src, repo)
    # 第二次同 body:不抛,返回已存在的,带 dedup 警告
    d2, warns = import_skill(src, repo)
    assert d1 == d2, "同 body 重复 import 应静默返回已存在的"
    assert any("去重" in w for w in warns)
    # force 仍允许重生(用户想重覆盖时)
    d3, _ = import_skill(src, repo, force=True)
    assert d3.exists()


def test_import_existing_canonical_diff_body_no_auto_rename_raises(tmp_path):
    """不同 body 同名且 auto_rename=False 且无 callback -> 仍抛(防自动覆盖)。"""
    s1 = _mk_agent_skill(tmp_path, "sk1", "dup", ["name: dup", "description: x"],
                         body=b"## A\n")
    s2 = _mk_agent_skill(tmp_path, "sk2", "dup", ["name: dup", "description: x"],
                         body=b"## B body\n")
    repo = tmp_path / "repo"; repo.mkdir()
    import_skill(s1, repo, auto_rename=False)
    with pytest.raises(ValueError, match="已存在且 body 不同"):
        import_skill(s2, repo, auto_rename=False)


def test_import_diff_body_auto_rename(tmp_path):
    """不同 body 同名 + auto_rename=True -> 自动用建议名(原名-native烖码)。"""
    s1 = _mk_agent_skill(tmp_path, "sk1", "dup", ["name: dup", "description: x"],
                         body=b"## A\n")
    s2 = _mk_agent_skill(tmp_path, "sk2", "dup", ["name: dup", "description: x"],
                         body=b"## B\n")
    repo = tmp_path / "repo"; repo.mkdir()
    d1, _ = import_skill(s1, repo, auto_rename=True, agent="ClaudeCode")
    assert d1.name == "dup"
    # 第二次不同 body 来自 TeleAgent -> 自动建议名 dup-tele
    d2, _ = import_skill(s2, repo, auto_rename=True, agent="TeleAgent")
    assert d2.name == "dup-tele", f"建议名应为 dup-tele, got {d2.name}"
    assert (repo / "skills" / "dup").exists() and (repo / "skills" / "dup-tele").exists()


def test_import_diff_body_rename_callback(tmp_path):
    """不同 body 同名 + rename_callback -> 用 callback 返回的名(用户自决)。"""
    s1 = _mk_agent_skill(tmp_path, "sk1", "dup", ["name: dup", "description: x"],
                         body=b"## A\n")
    s2 = _mk_agent_skill(tmp_path, "sk2", "dup", ["name: dup", "description: x"],
                         body=b"## B\n")
    repo = tmp_path / "repo"; repo.mkdir()
    import_skill(s1, repo, auto_rename=False)
    # callback 决定改名 office-dup
    cb = lambda orig, suggested, native: "office-dup"   # noqa: E731
    d2, _ = import_skill(s2, repo, auto_rename=False, rename_callback=cb, agent="Hermes")
    assert d2.name == "office-dup"
    # 建议名应是 dup-hermes
    from skillbank.importer import suggest_variant_name
    assert suggest_variant_name("dup", "Hermes") == "dup-hermes"


def test_short_agent_code_and_suggest():
    from skillbank.importer import short_agent_code, suggest_variant_name
    assert short_agent_code("QwenWorkCN") == "qwen"
    assert short_agent_code("TeleAgent") == "tele"
    assert short_agent_code("ClaudeCode") == "claude"
    assert short_agent_code(None) == "src"
    assert suggest_variant_name("docx", "QwenWorkCN") == "docx-qwen"
    assert suggest_variant_name("humanizer", "Hermes") == "humanizer-hermes"


def test_import_no_frontmatter_raises(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    (d / "SKILL.md").write_bytes(b"just body\n")
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="frontmatter"):
        import_skill(d, repo)


def test_detect_source_agent_unknown(tmp_path):
    m = _machines(tmp_path)
    assert detect_source_agent(tmp_path / "elsewhere" / "skill", m, "m1") is None
    assert detect_source_agent(tmp_path / "teleagent-skills" / "s", m, "m1") == "TeleAgent"


def test_import_explicit_agent_flag_beats_detection(tmp_path):
    src = _mk_agent_skill(tmp_path, "teleagent-skills", "x1",
                          ["name: x1", "description: x"])
    repo = tmp_path / "repo"
    repo.mkdir()
    dst, _warns = import_skill(src, repo, agent="ClaudeCode",
                       machines=_machines(tmp_path), machine="m1")
    ir = parse_canonical(dst / "SKILL.md")
    assert ir.native_agent == "ClaudeCode"   # 显式优先


# --- P0 #1: scan_body_paths 路径警告 ---

def test_scan_body_paths_absolute_warns():
    from skillbank.importer import scan_body_paths
    body = b"## Step\n\nRun /Users/ss/.claude/skills/foo/run.py\n"
    ws = scan_body_paths(body)
    assert any("绝对路径" in w for w in ws)


def test_scan_body_paths_windows_drive_warns():
    from skillbank.importer import scan_body_paths
    body = b"python E:\\anaconda\\python.exe C:\\Users\\x\\r.py\n"
    ws = scan_body_paths(body)
    assert any("绝对路径" in w for w in ws)


def test_scan_body_paths_cross_dir_warns():
    from skillbank.importer import scan_body_paths
    body = "## Step\n\n参考 ../shared/templates.md 的模板\n".encode("utf-8")
    ws = scan_body_paths(body)
    assert any("跨 skill 目录" in w for w in ws)


def test_scan_body_paths_clean_returns_empty():
    from skillbank.importer import scan_body_paths
    body = "## Step\n\nRun scripts/run.py\n用 ./resources/x.png\n".encode("utf-8")
    assert scan_body_paths(body) == []


def test_import_returns_path_warnings(tmp_path):
    from skillbank.importer import import_skill
    # 源含绝对路径 body
    src = tmp_path / "sk"; src.mkdir()
    (src / "SKILL.md").write_bytes(
        b"---\nname: x\ndescription: x\n---\n## step\nrun /Users/nope.py\n"
    )
    repo = tmp_path / "repo"; repo.mkdir()
    d, ws = import_skill(src, repo)
    assert d.exists() and any("绝对路径" in w for w in ws)
