"""P0 #15: 资源统计 + body 引用与资源一致性 check 测试。

防 "skill 调 py 因资源没 sync 过去 → 静默失败 → 你只觉得 LLM 质量差" 的盲区。
SkillBank 责任:文件搬齐是 emit 镜像;引用文件缺失由本层识别告知给用户。
"""

from __future__ import annotations

from pathlib import Path

from skillbank.refs import BodyRefIssue, check_body_refs, resource_stats


# --- resource_stats ---


def test_resource_stats_empty_dir_returns_empty(tmp_path):
    assert resource_stats(tmp_path / "no") == ""


def test_resource_stats_classification(tmp_path):
    """混合目录:scripts/N references/M + 散文件(N 文件入 files/N)。"""
    d = tmp_path / "skill"
    d.mkdir()
    (d / "SKILL.md").write_bytes(b"x")  # 应排除
    (d / "scripts").mkdir()
    (d / "scripts" / "a.py").write_text("x")
    (d / "scripts" / "b.py").write_text("x")
    (d / "references").mkdir()
    (d / "references" / "ref.md").write_text("y")
    (d / "LICENSE.txt").write_text("L")  # 散文件
    (d / ".agent_overrides").mkdir()    # 应排除

    s = resource_stats(d)
    assert "scripts/2" in s
    assert "references/1" in s
    assert "files/1" in s  # LICENSE.txt
    # SKILL.md 和 .agent_overrides 不计
    assert "SKILL.md" not in s and "agent_overrides" not in s


def test_resource_stats_nested_subdirs(tmp_path):
    d = tmp_path / "s"; d.mkdir()
    (d / "scripts").mkdir()
    (d / "scripts" / "sub").mkdir()
    (d / "scripts" / "a.py").write_text("x")
    (d / "scripts" / "sub" / "b.py").write_text("x")
    s = resource_stats(d)
    assert "scripts/2" in s


# --- check_body_refs ---


def test_check_body_refs_ok(tmp_path):
    """body 引用 scripts/run.py 且文件在 → ok。"""
    d = tmp_path / "s"; d.mkdir()
    (d / "scripts").mkdir()
    (d / "scripts" / "run.py").write_text("print(1)")
    body = b"## Step\n\nRun `scripts/run.py`\n"
    issues = check_body_refs(body, d)
    assert len(issues) == 1
    assert issues[0].severity == "ok" and issues[0].ref == "scripts/run.py"


def test_check_body_refs_missing(tmp_path):
    """body 引用 scripts/missing.py 但镜像目录没 → missing(silent failure 可感)。"""
    d = tmp_path / "s"; d.mkdir()
    # 注意不在创建 scripts/missing.py
    body = b"## Step\n\ncall `scripts/missing.py` --opt\n"
    issues = check_body_refs(body, d)
    assert len(issues) == 1
    assert issues[0].severity == "missing" and "missing.py" in issues[0].detail


def test_check_body_refs_excludes_absolute_and_parent(tmp_path):
    """绝对路径 / https URL / ../ 引用都不查(scan_body_paths 管)。"""
    d = tmp_path / "s"; d.mkdir()
    body = (b"## Step\n\nRun /Users/x/run.py ; "
            b"see <https://example.com/data.json> ; "
            b"ref `../shared/templates/foo.json`\n")
    issues = check_body_refs(body, d)
    assert issues == [], "绝对/URL/.. 跨目录引用应不归本层 check"


def test_check_body_refs_multiple_extensions(tmp_path):
    """覆盖常见扩展名: py sh json md yaml png ttf ..."""
    d = tmp_path / "s"; d.mkdir()
    (d / "templates").mkdir()
    for ext in ("py", "sh", "json", "md", "yaml", "png", "ttf"):
        (d / "templates" / f"x.{ext}").write_text("x")
    body = b"## Step\n\nRefer to `templates/x.py`, `templates/x.sh`, `templates/x.json`, `templates/x.md`, `templates/x.yaml`, `templates/x.png`, `templates/x.ttf`\n"
    issues = check_body_refs(body, d)
    assert len(issues) == 7
    assert all(i.severity == "ok" for i in issues)


def test_check_body_refs_dedup(tmp_path):
    """同一引用在 body 多次出现, 只报一次。"""
    d = tmp_path / "s"; d.mkdir()
    (d / "scripts").mkdir()
    (d / "scripts" / "a.py").write_text("x")
    body = b"Run `scripts/a.py` then `scripts/a.py` again\n"
    issues = check_body_refs(body, d)
    assert len(issues) == 1


def test_check_body_refs_known_subdirs_collected(tmp_path):
    """scripts/references/resources/templates/prompts/fonts/rooms 都被检。"""
    d = tmp_path / "s"; d.mkdir()
    for sd in ("scripts", "references", "resources", "templates",
               "prompts", "fonts", "rooms", "agents", "protocol"):
        (d / sd).mkdir()
        (d / sd / "f.json").write_text("{}")
    body_text = "    ".join(f"`{sd}/f.json`" for sd in
                            ["scripts", "references", "resources", "templates",
                             "prompts", "fonts", "rooms", "agents", "protocol"])
    body = ("## Step\n\n" + body_text + "\n").encode("utf-8")
    issues = check_body_refs(body, d)
    assert len(issues) == 9
    assert all(i.severity == "ok" for i in issues)

