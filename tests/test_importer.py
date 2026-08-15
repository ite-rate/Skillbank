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

from skillhub.importer import detect_source_agent, import_skill
from skillhub.machines import MachinesConfig
from skillhub.parsers.canonical import parse_canonical

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


def test_import_existing_canonical_raises_unless_force(tmp_path):
    src = _mk_agent_skill(tmp_path, "some-skills", "dup", ["name: dup", "description: x"])
    repo = tmp_path / "repo"
    repo.mkdir()
    import_skill(src, repo)
    with pytest.raises(ValueError, match="已存在"):
        import_skill(src, repo)
    import_skill(src, repo, force=True)   # force 覆盖 ok


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
    from skillhub.importer import scan_body_paths
    body = b"## Step\n\nRun /Users/ss/.claude/skills/foo/run.py\n"
    ws = scan_body_paths(body)
    assert any("绝对路径" in w for w in ws)


def test_scan_body_paths_windows_drive_warns():
    from skillhub.importer import scan_body_paths
    body = b"python E:\\anaconda\\python.exe C:\\Users\\x\\r.py\n"
    ws = scan_body_paths(body)
    assert any("绝对路径" in w for w in ws)


def test_scan_body_paths_cross_dir_warns():
    from skillhub.importer import scan_body_paths
    body = "## Step\n\n参考 ../shared/templates.md 的模板\n".encode("utf-8")
    ws = scan_body_paths(body)
    assert any("跨 skill 目录" in w for w in ws)


def test_scan_body_paths_clean_returns_empty():
    from skillhub.importer import scan_body_paths
    body = "## Step\n\nRun scripts/run.py\n用 ./resources/x.png\n".encode("utf-8")
    assert scan_body_paths(body) == []


def test_import_returns_path_warnings(tmp_path):
    from skillhub.importer import import_skill
    # 源含绝对路径 body
    src = tmp_path / "sk"; src.mkdir()
    (src / "SKILL.md").write_bytes(
        b"---\nname: x\ndescription: x\n---\n## step\nrun /Users/nope.py\n"
    )
    repo = tmp_path / "repo"; repo.mkdir()
    d, ws = import_skill(src, repo)
    assert d.exists() and any("绝对路径" in w for w in ws)
