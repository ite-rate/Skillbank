
from pathlib import Path


# --- SKILL_DIR 变量引用(真实 data-report 场景) ---


def test_check_body_refs_skill_dir_var(tmp_path):
    """${SKILL_DIR}/scripts/foo.py 这种变量引用都应识(data-report 真实形式)。"""
    from skillbank.refs import check_body_refs
    d = tmp_path / "s"
    d.mkdir()
    (d / "scripts").mkdir()
    (d / "scripts" / "run.py").write_text("x")
    # 形式 1: ${SKILL_DIR}/scripts/run.py (花括号形式)
    body = b"Run ${SKILL_DIR}/scripts/run.py to start\n"
    issues = check_body_refs(body, d)
    assert any(i.ref == "scripts/run.py" for i in issues), \
        f"应识 ${{SKILL_DIR}}/scripts 引用, got {[i.ref for i in issues]}"
    # 形式 2: "$SKILL_DIR/scripts/run.py" (双引号里裸变量)
    body2 = b'python "$SKILL_DIR/scripts/run.py" --opt\n'
    issues2 = check_body_refs(body2, d)
    assert any(i.ref == "scripts/run.py" for i in issues2), \
        f"应识 \"$SKILL_DIR/scripts/run.py\", got {[i.ref for i in issues2]}"
    # 形式 3: $SKILL_DIR 不带花括号也不带引号
    body3 = b"exec $SKILL_DIR/scripts/run.py arg\n"
    issues3 = check_body_refs(body3, d)
    assert any(i.ref == "scripts/run.py" for i in issues3), \
        "应识 $SKILL_DIR/scripts/run.py 无花括号形式"


def test_check_body_refs_data_report_real_body(tmp_path):
    """端到端: 真实 data-report body 含 SKILL_DIR/scripts/* 与 references/* 引,
    check_body_refs 应能全识(全部在镜像目录中存在)。"""
    import re
    from skillbank.refs import check_body_refs

    src = Path.home() / ".qwenworkcn/skills/data-report"
    if not src.exists():
        import pytest
        pytest.skip("data-report 未装")
    raw = (src / "SKILL.md").read_bytes()
    m = re.match(rb"\A---\r?\n(.*?)\r?\n---\r?\n(.*)", raw, re.S)
    issues = check_body_refs(m.group(2), src)
    # data-report body 里 references/scripts 引用全存在
    missing = [i for i in issues if i.severity == "missing"]
    assert not missing, f"data-report body 引用未在源目录全部存在: {missing}"
    # scripts/xlsx_reader.py 等(body 里写 ${SKILL_DIR}/scripts/xlsx_reader.py)
    refs = {i.ref for i in issues}
    assert any("xlsx_reader" in r for r in refs), \
        f"scripts/xlsx_reader 引用应识, got {refs}"
    assert any("references/" in r for r in refs), \
        f"references/ 引用应识, got {refs}"
    # html_report.py 也是 ${SKILL_DIR}/scripts/html_report.py 形式
    assert any("html_report" in r for r in refs), \
        f"scripts/html_report 引用应识(SKILL_DIR 形式), got {refs}"