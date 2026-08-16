# Skillbank 后续迭代实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Skillbank 剩余的 7 个 TODO 项做完，让产品从"能用"到"好用"

**Architecture:** 在现有 M0-M7 代码基础上迭代，每个 TODO 独立可测，不破坏已有 112/112 测试

**Tech Stack:** Python 3.12, pytest, tomllib, PyYAML, 无第三方依赖

## Global Constraints

- Python 3.12+，不引入新第三方依赖
- body 零损耗硬约束不被破坏
- 已有 112/112 测试不回归
- canonical 真源唯一性不破坏

---

## Task 1: list 区分 Hermes skipped 原因 (#6)

**Files:**
- Modify: `src/skillbank/manifest.py` — `DeployRecord` 加 `skip_reason: Optional[str]` 字段
- Modify: `src/skillbank/sync.py` — Hermes skip 时写 `skip_reason` 到 manifest
- Modify: `src/skillbank/cli.py` — `list` 命令读 `skip_reason` 显示 `~` 而非 `·`
- Test: `tests/test_manifest.py` — 加 skip_reason 序列化/读取测试

**Interfaces:**
- Consumes: `sync.execute()` 里 Hermes skip 时已有的 `result.note`
- Produces: `DeployRecord.skip_reason` 字段，`list` CLI 展示用

- [ ] **Step 1: DeployRecord 加 skip_reason 字段**

```python
@dataclass
class DeployRecord:
    skill: str
    machine: str
    agent: str
    deploy_path: str
    deployed_at: str = ""
    method: str = "cp"
    ir_hash: str = ""
    note: str = ""
    pending_deletion: bool = False
    skip_reason: Optional[str] = None    # #6: Hermes skip 原因(file_size_max 等)
```

- [ ] **Step 2: sync.py Hermes skip 时写 skip_reason**

在 `sync.execute()` 的 `result.method == "skipped"` 分支里，不直接删 manifest 记录，而是更新记录标 `skip_reason`:

```python
if result.method == "skipped":
    recs = manifest.find(name, machine=machine, agent=agent)
    if recs:
        recs[0].skip_reason = result.note
        recs[0].method = "skipped"
        manifest_dirty = True
    else:
        # 没有旧记录，新建一条 skipped 记录
        manifest.upsert(DeployRecord(
            skill=name, machine=machine, agent=agent,
            deploy_path=str(deploy_root / name), method="skipped",
            skip_reason=result.note,
        ))
        manifest_dirty = True
```

- [ ] **Step 3: cli.py list 命令读 skip_reason 显示 ~**

```python
# 在 list 命令的 cells 构建里：
if not recs:
    cells.append("·")
elif recs[0].method == "skipped" or recs[0].skip_reason:
    cells.append("~")
elif recs[0].pending_deletion:
    cells.append("p")
elif recs[0].method == "ln":
    cells.append("l")
else:
    cells.append("c")
```

- [ ] **Step 4: 测试**

```python
def test_skip_reason_stored_and_read(tmp_path):
    manifest = DeploymentsManifest(path=tmp_path / "d.json")
    manifest.upsert(DeployRecord(
        skill="big", machine="m", agent="Hermes",
        deploy_path="/tmp/big", method="skipped",
        skip_reason="file_size_max exceeded: 100540 > 100000",
    ))
    manifest.save()
    m2 = DeploymentsManifest.load(tmp_path / "d.json")
    rec = m2.find("big", machine="m", agent="Hermes")[0]
    assert rec.method == "skipped"
    assert rec.skip_reason == "file_size_max exceeded: 100540 > 100000"
```

---

## Task 2: sync 加 --all-skills 默认全选 (#8)

**Files:**
- Modify: `src/skillbank/cli.py` — `_cmd_sync` 加 `--all-skills` flag
- Modify: `src/skillbank/interactive.py` — `select_many` 加 `all` 快捷
- Test: `tests/test_cli.py`（新建，测 --all-skills 行为）

- [ ] **Step 1: argparse 加 --all-skills**

```python
sp.add_argument("--all-skills", action="store_true",
                help="全选所有 canonical skill(不交互)")
```

- [ ] **Step 2: _cmd_sync 里 --all-skills 跳过交互选 skill**

```python
if args.all_skills or args.yes or not _is_tty():
    skills_filter = None  # None = 全部
else:
    # 原有交互选 skill 逻辑
    ...
```

- [ ] **Step 3: interactive.select_many 加 all 快捷**

```python
def select_many(title: str, options: list[str], none_ok: bool = True) -> list[int]:
    ans = input(f"选择(逗号分隔编号, 回车=全选, all=全选, none=不选): ").strip()
    if ans in ("", "all"):
        return list(range(len(options)))
    ...
```

- [ ] **Step 4: 测试**

```python
def test_all_skills_flag_bypasses_interaction():
    # --all-skills 时 skills_filter=None, 不弹交互
    ...
```

---

## Task 3: import 后 doctor 报告未识别 frontmatter 字段 (#12)

**Files:**
- Modify: `src/skillbank/cli.py` — `_cmd_import` / `_cmd_add` 后自动调 `doctor --skill`
- Modify: `src/skillbank/refs.py` — 新增 `scan_unknown_frontmatter_fields(fm) -> list[str]`
- Test: `tests/test_refs.py` — 加未知字段检测测试

- [ ] **Step 1: refs.py 加 scan_unknown_frontmatter_fields**

```python
_CANONICAL_FM_FIELDS = {"name", "description", "level", "native_agent",
                         "requires", "description_zh", "name_zh",
                         "version", "license", "name_cn", "description_cn"}

def scan_unknown_frontmatter_fields(fm: dict) -> list[str]:
    """检测 import 时 frontmatter 里不在 canonical 认识范围里的字段。"""
    return [k for k in fm if k not in _CANONICAL_FM_FIELDS]
```

- [ ] **Step 2: cli.py import 后打印未知字段警告**

```python
unknown = scan_unknown_frontmatter_fields(src_fm)
if unknown:
    print(f"  ⚠ frontmatter 含未识别字段: {', '.join(unknown)}")
    print(f"    这些已透传到 .agent_overrides/<agent>.toml, 部署时还原")
```

- [ ] **Step 3: 测试**

```python
def test_scan_unknown_fields():
    fm = {"name": "x", "description": "d", "install_source": "market", "priority": 1}
    unknown = scan_unknown_frontmatter_fields(fm)
    assert set(unknown) == {"install_source", "priority"}
```

---

## Task 4: import 跨 skill 相对路径深 warn (#11)

**Files:**
- Modify: `src/skillbank/importer.py` — `scan_body_paths` 对 `../` 引用加跨 skill 深度检测
- Test: `tests/test_importer.py` — 加跨 skill 引用 warn 测试

- [ ] **Step 1: scan_body_paths 里 `../` warn 加深**

当前 `../` 只浅 warn "可能失效"，改成检测目标是否在其他 skill 目录里：

```python
cross = _CROSS_DIR_RE.findall(text)
if cross:
    for ref in cross:
        target = src_dir.parent / ref
        if target.exists():
            warns.append(f"body 引用 `../{ref}` 指向相邻 skill 目录 — "
                        f"跨 Agent 同步后路径断裂(各 Agent 目录结构不同)")
        else:
            warns.append(f"body 引用 `../{ref}` — 目标不存在, 可能是模板占位")
```

- [ ] **Step 2: 测试**

```python
def test_cross_skill_ref_warn(tmp_path):
    # 建 sibling skill 目录
    other = tmp_path / "other-skill"
    other.mkdir()
    (other / "shared.md").write_text("x")
    # body 里引 ../other-skill/shared.md
    body = b"See ../other-skill/shared.md for details\n"
    warns = scan_body_paths(body)
    assert any("相邻 skill" in w for w in warns)
```

---

## Task 5: manifest 分片支持 (#10)

**Files:**
- Modify: `src/skillbank/manifest.py` — `DeploymentsManifest` 支持按 machine 分文件
- Test: `tests/test_manifest.py` — 加分片读写测试

- [ ] **Step 1: DeploymentsManifest 加 per-machine 文件支持**

```python
class DeploymentsManifest:
    def __init__(self, records=None, path=None, per_machine=False):
        ...
        if per_machine:
            # manifests/<machine>.json 而非 deployments.json
            self.path = self.path.parent / f"machine-{machine}.json"
```

- [ ] **Step 2: load/save 支持分片**

```python
@classmethod
def load(cls, path, machine=None):
    if machine and (path.parent / f"machine-{machine}.json").exists():
        path = path.parent / f"machine-{machine}.json"
    ...
```

- [ ] **Step 3: 测试**

```python
def test_per_machine_manifest(tmp_path):
    m1 = DeploymentsManifest(path=tmp_path / "machine-mac-main.json")
    m1.upsert(DeployRecord(skill="a", machine="mac-main", agent="ClaudeCode", ...))
    m1.save()
    assert (tmp_path / "machine-mac-main.json").exists()
```

---

## Task 6: Hermes usage 全字段入 list (#14)

**Files:**
- Modify: `src/skillbank/cli.py` — `list` 命令读 Hermes `.usage.json` 显示频率
- Modify: `src/skillbank/capabilities.py` — 加 `load_hermes_usage(path) -> dict`
- Test: `tests/test_capabilities.py` — 加 usage 加载测试

- [ ] **Step 1: capabilities.py 加 load_hermes_usage**

```python
def load_hermes_usage(path: Path) -> dict[str, dict]:
    """读 Hermes .usage.json, 返回 {skill_name: {use_count, last_used_at, ...}}"""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {name: info for name, info in data.items() if isinstance(info, dict)}
```

- [ ] **Step 2: cli.py list 显示频率列**

```python
usage = load_hermes_usage(Path.home() / ".hermes/skills/.usage.json")
# 在 list 输出里加一列:
freq = usage.get(name, {})
cnt = freq.get("use_count", 0)
last = freq.get("last_used_at", "")
if cnt:
    freq_str = f"{cnt}x"
elif last:
    freq_str = "view"
else:
    freq_str = "—"
```

- [ ] **Step 3: 测试**

```python
def test_load_hermes_usage(tmp_path):
    p = tmp_path / ".usage.json"
    p.write_text('{"daily-agent-briefing": {"use_count": 226, "last_used_at": "2026-08-14T..."}}')
    usage = load_hermes_usage(p)
    assert usage["daily-agent-briefing"]["use_count"] == 226
```

---

## Task 7: git remote 接入

**Files:**
- Modify: `README.md` — 补 git remote 配置说明
- 不改代码（纯配置 + 文档）

- [ ] **Step 1: 用户定 GitHub 私库或自托管**

```bash
# GitHub 私库
gh repo create skillbank --private --source=. --push

# 或自托管
git remote add origin git@your-server:skillbank.git
git push -u origin main
```

- [ ] **Step 2: README 补跨机 git 流程**

```markdown
## git remote 配置

```bash
# 主力机一次性
gh repo create skillbank --private --source=. --push

# 笔记本/服务器
git clone git@github.com:you/skillbank.git ~/Documents/Skillbank
cd ~/Documents/Skillbank
pip install -e .
skillbank scan --machine laptop
skillbank sync --to laptop
```
```

---

## Self-Review

### Spec coverage
- #6 list 区分 skipped → Task 1 ✓
- #8 --all-skills → Task 2 ✓
- #10 manifest 分片 → Task 5 ✓
- #11 跨 skill 深 warn → Task 4 ✓
- #12 import 后报未知字段 → Task 3 ✓
- #14 Hermes usage 入 list → Task 6 ✓
- git remote → Task 7 ✓

### Placeholder scan
- 无 TBD/TODO/fill in
- 每个 Task 都有完整代码

### Type consistency
- `DeployRecord.skip_reason: Optional[str]` — Task 1 定义，Task 5 分片时不破坏
- `load_hermes_usage(path) -> dict[str, dict]` — Task 6 定义，cli.py 消费
- `scan_unknown_frontmatter_fields(fm: dict) -> list[str]` — Task 3 定义，cli.py 消费

### 优先级
Task 1-3 是用户最常碰到的（list 看不清 / 交互烦 / import 不透明），先做。
Task 4-5 是规模扩展，44 个 skill 不急但做了更稳。
Task 6 是数据展示增强。
Task 7 纯配置，用户定后秒做。