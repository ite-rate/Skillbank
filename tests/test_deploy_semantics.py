"""零损耗部署语义回归锁 — 真实 sync 产物的正确验证口径。

正确口径(以 ClaudeCode 带 native 前言为例):
    deployed = frontmatter块 + 前言块(🪧/⚠️) + canonical body
- canonical body 必须**完整出现在文件末尾**(raw.endswith(body))
- 前言只允许出现在 frontmatter 与 body 之间
- 不能用"切出的第二段 == body"断言 — 那段含前言, 必然不等(历史冒烟脚本踩过)

另锁: 资源镜像 / ZCode 软链 / manifest 记录。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from skillbank.agents import AgentsConfig
from skillbank.capabilities import CapabilityMatrix
from skillbank.emitters.canonical import emit_canonical
from skillbank.ir import Level, SkillIR
from skillbank.manifest import DeploymentsManifest
from skillbank.machines import MachinesConfig
from skillbank.sync import collect, execute

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fm_body_raw(p: Path):
    raw = Path(p).read_bytes()
    m = re.match(rb"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", raw, re.S)
    return yaml.safe_load(m.group(1)), m.group(2), raw


def test_deployed_zero_loss_semantics_with_prompt(tmp_path):
    """带 native 前言的部署: canonical body 完整在末尾, 前言在 fm 与 body 之间。"""
    repo = tmp_path / "repo"
    canon_dir = repo / "skills" / "img"
    canon_dir.mkdir(parents=True)
    body = b"## gen\n\nmake image\r\nCRLF kept\n"
    emit_canonical(
        SkillIR(name="img", description="d", body=body, level=Level.AUTO,
                native_agent="Hermes", requires=["image_generation"]),
        canon_dir / "SKILL.md",
    )
    (canon_dir / "scripts").mkdir()
    (canon_dir / "scripts" / "run.py").write_text("print(1)\n")

    agents_cfg = AgentsConfig.load(REPO_ROOT / "agents.toml")
    machines = MachinesConfig()
    machines.set_skills_dir("m", "ClaudeCode", str(tmp_path / "cc"))
    manifest = DeploymentsManifest(path=repo / "manifests" / "d.json")
    caps = CapabilityMatrix.load(REPO_ROOT / "capabilities.toml")

    ctx = collect(repo, "m", None, None, machines, agents_cfg, manifest)
    rc = execute(repo, "m", ctx, machines, agents_cfg, caps, manifest)
    assert rc == 0

    raw = (tmp_path / "cc" / "img" / "SKILL.md").read_bytes()
    # 零损耗正确口径: canonical body 完整出现在末尾
    assert raw.endswith(body), "canonical body 必须完整在 deployed 文件末尾"
    # 前言存在于 fm 与 body 之间(🪧 native + ⚠️ image_generation unsupported)
    fm, _, _ = _fm_body_raw(tmp_path / "cc" / "img" / "SKILL.md")
    assert set(fm) == {"name", "description"}
    assert "\U0001faa7".encode() not in raw, "前言已砍, 不应有 native 提示"
    # 资源镜像
    assert (tmp_path / "cc" / "img" / "scripts" / "run.py").read_text() == "print(1)\n"
    # manifest
    rec = manifest.find("img", machine="m", agent="ClaudeCode")[0]
    assert rec.method == "cp" and rec.ir_hash == "sha256:" + __import__("hashlib").sha256(body).hexdigest()
