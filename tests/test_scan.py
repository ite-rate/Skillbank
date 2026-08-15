"""scan 探测 + machines.toml 渲染回写测试。

用假 home 模拟各安装状态:
- strong : skills 目录有含 SKILL.md 的子目录
- medium : skills 目录存在但空
- weak   : agent 装了但 skills 目录没建(kimi 惰性)
- QwenWorkCN 候选序: .qwenworkcn 优先于 .qwen
- glob 变体: 只装在 ~/.qwenworkcn-skills 这种怪路径也能兜到
- render -> load 往返保值
- set_skills_dir + save 原子写
"""

from __future__ import annotations

from pathlib import Path

import tomllib

from skillhub.machines import MachinesConfig
from skillhub.scan import detect_agent, pick_best


def _fake_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


def _mk_skill(base: Path, name: str) -> None:
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_bytes(b"---\nname: x\ndescription: x\n---\nbody\n")


# --- 探测分级 ---


def test_detect_strong_with_skills(tmp_path):
    home = _fake_home(tmp_path)
    skills = home / ".claude" / "skills"
    _mk_skill(skills, "agora")
    cands = detect_agent("ClaudeCode", home)
    assert len(cands) == 1
    c = cands[0]
    assert c.confidence == "strong"
    assert c.path == skills
    assert "1 个 skill" in c.evidence


def test_detect_medium_empty_dir(tmp_path):
    home = _fake_home(tmp_path)
    (home / ".claude" / "skills").mkdir(parents=True)
    cands = detect_agent("ClaudeCode", home)
    assert cands[0].confidence == "medium"


def test_detect_weak_lazy_dir(tmp_path):
    """agent 装了(父目录在)但 skills 目录没建 — kimi 场景。"""
    home = _fake_home(tmp_path)
    (home / ".kimi-code").mkdir()
    cands = detect_agent("kimi-code", home)
    assert len(cands) == 1
    assert cands[0].confidence == "weak"
    assert cands[0].path == home / ".kimi-code" / "skills"
    assert "尚未创建" in cands[0].evidence


def test_detect_not_installed_returns_empty(tmp_path):
    home = _fake_home(tmp_path)
    assert detect_agent("Hermes", home) == []


def test_qwenworkcn_prefers_qwenworkcn(tmp_path):
    """同时有 .qwenworkcn(在用) 和 .qwen(旧), 排序优先 .qwenworkcn。"""
    home = _fake_home(tmp_path)
    _mk_skill(home / ".qwenworkcn" / "skills", "dws")
    _mk_skill(home / ".qwen" / "skills", "old")
    cands = detect_agent("QwenWorkCN", home)
    assert cands[0].path == home / ".qwenworkcn" / "skills"


def test_qwenworkcn_weird_path_got_by_glob(tmp_path):
    """怪路径(~/.qwenworkcn-skills)也能被 glob 兜住 — 用户说'qwen 路径就很怪'。"""
    home = _fake_home(tmp_path)
    _mk_skill(home / ".qwenworkcn-skills" / "skills", "dws")
    cands = detect_agent("QwenWorkCN", home)
    assert any(c.path == home / ".qwenworkcn-skills" / "skills" for c in cands)


def test_pick_best_prefers_strong(tmp_path):
    home = _fake_home(tmp_path)
    _mk_skill(home / ".qwenworkcn" / "skills", "dws")   # strong
    (home / ".qwen").mkdir()                            # weak(.qwen/skills 未建)
    best = pick_best(detect_agent("QwenWorkCN", home))
    assert best.confidence == "strong"
    assert best.path == home / ".qwenworkcn" / "skills"


# --- 渲染回写往返 ---


def test_render_load_roundtrip(tmp_path):
    home = _fake_home(tmp_path)
    _mk_skill(home / ".claude" / "skills", "agora")

    m = MachinesConfig()
    m.set_skills_dir("mac-main", "ClaudeCode", str(home / ".claude" / "skills"))
    m.set_skills_dir("mac-main", "kimi-code", str(home / ".kimi-code" / "skills"))
    m.machines["mac-main"].display_name = "Mac 主力机"

    out = tmp_path / "machines.toml"
    m.save(out)
    # 产物是合法 TOML
    with open(out, "rb") as fh:
        d = tomllib.load(fh)
    assert d["machines"]["mac-main"]["agents"]["ClaudeCode"]["skills_dir"] == str(
        home / ".claude" / "skills"
    )
    # 再 load 回对象, 值不丢
    m2 = MachinesConfig.load(out, known_agents={"ClaudeCode", "kimi-code"})
    assert m2.get_skills_dir("mac-main", "ClaudeCode") == home / ".claude" / "skills"
    assert m2.get_skills_dir("mac-main", "kimi-code") == home / ".kimi-code" / "skills"
    assert m2.machines["mac-main"].display_name == "Mac 主力机"


def test_save_atomic_no_tmp(tmp_path):
    m = MachinesConfig()
    m.set_skills_dir("m", "ClaudeCode", "/x")
    m.save(tmp_path / "machines.toml")
    assert not list(tmp_path.glob("*.tmp"))
