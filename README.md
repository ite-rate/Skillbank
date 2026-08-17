# Skillbank

> Central canonical SKILL.md repository → 7 desktop AI agents.
> **body byte-identical, no loss** — frontmatter 经手 Skillbank 后字段级透传, 引号/顺序不漂移。
> Cross-machine sync via git (`Mac main edit → laptop periodic pull → server manual pull`).

---

## TL;DR — 5 行上手

```sh
cd ~/Documents/main_store/temp/Skillbank   # or wherever you cloned
pip install -e .                            # 一次性, 注册 `skillbank` 命令
skillbank scan --machine mac-main           # 探测本机 7 Agent 的 skills 目录 → 写 machines.toml
skillbank import ~/.qwenworkcn/skills/dws   # 反向导入:Agent skill → canonical
skillbank sync                              # 交互选 skill×Agent → 计划预览 → 确认部署
```

---

## 7 目标 Agent(实测真身, 非需求文档想象)

| Skillbank key | 真实产品 | skills_dir (实测 mac-main) | frontmatter 方言 |
|---|---|---|---|
| `ClaudeCode`  | Anthropic Claude Code  | `~/.claude/skills` | name + description (+ `disable-model-invocation: true`) |
| `ZCode`       | 智谱 ZCode (GLM-5.2) | `~/.zcode/skills` | 同 ClaudeCode |
| `QwenWorkCN`  | 阿里 QwenWorkCN 千问办公(**非** Qwen Code CLI) | `~/.qwenworkcn/skills` | + `description_zh`/`name_zh` (+ `enabled_at: false`) |
| `TeleAgent`   | TeleAgent (OpenCode 内核) | `~/.config/TeleAgent/skills` | + `description_cn`/`name_cn` (从 canonical `_zh` 镜像) (+ `enabled_at: false`) |
| `Hermes`      | NousResearch Hermes | `~/.hermes/skills/<category>/` | + `metadata.hermes.disable-model-invocation` (default category `imported/`) |
| `Codex`       | OpenAI Codex | `~/.codex/skills` | + `disable-model-invocation`, description ≤1024 截断 |
| `kimi-code`   | moonshot kimi-code(**非** Claude 跟随) | `~/.kimi-code/skills` | name + description (无 frontmatter 禁触发字段) |

**全部 7 个 Agent 一律 cp 部署**(emitter 硬编码, 无 `method` 配置)。

**需求文档的 3 个身份错误已被实测推翻**:
- Qwen 一律写成 Qwen Code CLI 开发者版(实际装的是办公版)
- kimi 当成 Claude/OpenClaw 跟随体(实际是 moonshot 独立 kimi-code)
- ZCode 是混合体(真实副本 + 软链都存在)

---

## Canonical SKILL.md(frontmatter 正文)

```yaml
---
name: canvas-design
description: Create visual art. When the user asks for a poster, ...
level: auto                            # auto | manual | experimental | disable
native_agent: TeleAgent                # 可选;skillbank list/doctor 展示用(不注入 deployed body)
requires: [image_generation, file_write]   # 可选;仅作文档标注(emitter 不做能力过滤)
description_zh: 创意海报设计...           # 可选;TeleAgent/QwenWork 双语镜像位
name_zh: 创意海报设计                    # 可选
version: 1.0.0                          # 可选
license: Complete terms in LICENSE.txt   # 可选
---
<body — bytes, 字段级透传保证不漂移>
```

canonical 只用 `description_zh` 一个中文 key(中性, 更准):
- TeleAgent 用 `name_cn`/`description_cn`, QwenWork 用 `name_zh`/`description_zh`
- emitter 对 TeleAgent 自动镜像 `_zh → _cn`, 对 QwenWork 直传 `_zh`
- import 时反向:TeleAgent `_cn` → canonical `_zh`(透明转换)

Agent 专有字段(市场装来的 `install_source`/`skill_id`/`metadata.hermes.tags` 等)不进 canonical,
存 `.agent_overrides/<agent>.toml`(skill 目录下)。
sync 部署到原生 Agent 时从 overrides 递归合并回 deployed frontmatter
(dict 嵌套合并, emitter 已写值优先, 不丢 override 元数据)。

---

## Skill 分级(level)— 触发方式控制

| `level` | 同步? | 模型自动触发? | 手动调用? | emitter 写什么 |
|---|---|---|---|---|
| `auto`          | ✅ | ✅ 允许 | ✅ | 干净 frontmatter |
| `manual`        | ✅ | ❌ 禁止 | ✅ | Claude/ZCode/Codex → `disable-model-invocation: true`; TeleAgent/Qwen → `enabled_at: false`; Hermes → `metadata.hermes.disable-model-invocation: true` |
| `experimental`  | ✅ | ❌ 禁止(同 manual) | ✅ | 同 manual(语义标记区别) |
| `disable`       | ❌ 不同步 | — | — | 下次 sync 清掉所有已部署副本(canonical 保留) |

**已知限制:** `kimi-code` 不支持 frontmatter 禁止触发字段,`manual`/`experimental` 部署到 kimi 时
sync 输出 ⚠ 提示模型仍可能自动触发,需靠 description 话术或下级工具显式控制。

---

## CLI 全命令(10 个)

```sh
# 路径配置(每机器一次)
skillbank scan                              # 探测 + 交互确认 + 写 machines.toml
skillbank scan --yes                        # 非交互自动选最优候选
skillbank doctor [--machine mac-main]       # 配置/路径/manifest/canonical/git 体检
skillbank doctor --skill <name>            # 专项:body 引用 vs 资源镜像一致性(防 silent failure)

# 导入既有 skill 进 canonical
skillbank import <agent_skill_dir>          # 反向导入(自动探测 native_agent;双语 _cn→_zh)
skillbank import <dir> --agent ClaudeCode --level manual
skillbank add <local_path>                  # 同 import 的快捷变种(无 --agent 自动探测)
skillbank add <git_url>                     # git clone --depth 1 + 批量导入

# 同步
skillbank sync                              # 交互选 skill×Agent → 计划 → 确认
skillbank sync -s <name> -a <agent> --yes   # 非交互单 skill 单 Agent
skillbank sync -s <name>                    # 单 skill 到该机器全部 Agent
skillbank sync --dry-run                    # 只看计划不动盘
skillbank sync --to <machine>               # 不同机器(默认 mac-main)

# 删除 / 状态 / level
skillbank rm <name>                         # 本机删副本 + 其它机器标 pending(下次 sync 执行)
skillbank rm <name> --dry-run
skillbank list                              # 状态表(c=cp p=pending ·=未部署 ~=deferred)
skillbank list --agent ClaudeCode --level auto
skillbank set-level <name> <auto|manual|experimental|disable>   # 改触发策略

# ZCode 治理(可选, 谨慎 — zcode 真实副本迁入中央)
skillbank zcode-cleanup                     # 逐个交互确认 + mv 备份到 ~/.zcode/skills.bak/<ts>/ → 软链 canonical
skillbank zcode-cleanup --dry-run
```

---

## 跨机器接入(新机器 3 步)

```sh
# 一次性
git clone <Skillbank_repo_remote> ~/Documents/Skillbank
cd ~/Documents/Skillbank
pip install -e .

# 第二台机器:
skillbank scan --machine laptop             # 探测这台装的 agent → 写 machines.toml
#   - 没装的 agent 会被探测标 ✗ 不留下配置 → sync 时跳过不报错
#   - 各机器的 agent 路径独立手填/确认(QwenWorkCN 在 Mac 与笔记本路径不一致也无所谓)
skillbank sync --to laptop                  # 拉到该机本装的 agent 子集
```

跨机机制 = **git 仓库本身当跨机消息总线**:
- Mac 改 canonical + sync → manifest 写记录(谁部署到哪) → git commit/push
- 笔记本 git pull → `skillbank sync --to laptop` 自动执行 pending_deletion(其它机器标来的删)→ plan 各 Agent 的 deploy
- body hash 比对 manifest 的 `ir_hash` 字段可证各机器收到的 body 一字不差

---

## Pipeline(parser→IR→emitter, 零损耗如何保证)

```
canonical SKILL.md (skills/<name>/SKILL.md)
  └─ parsers/canonical.parse_canonical()
        ├─ bytes 读全文, byte-level 正则切 frontmatter 边界(允许 \r\n)
        ├─ body 取边界后的全部原字节 → SkillIR.body: bytes (不 decode 不 normalize)
        └─ frontmatter 原字节 + 原 dict 也存入 IR(fm_raw / fm_orig)
              └─ emitters/<agent>.emit()
                    ├─ frontmatter 字段级透传:未变更字段保原字节(引号/顺序不漂),
                    │   仅重写翻译字段(level→disable-model-invocation/双语镜像/Codex截断/...)
                    ├─ Agent 专有字段从 .agent_overrides/<agent>.toml 递归合并回 frontmatter
                    ├─ body 直接跟 frontmatter(无前言, 不注入任何元信息)
                    ├─ resources/ 全目录镜像(相对路径继续有效)
                    └─ 部署产物 SKILL.md 写盘
                          └─ manifest 记录 (deploy_path + ir_hash=body sha256)
```

**零损耗验证手段**: `pytest tests/test_roundtrip.py tests/test_deploy_semantics.py` —
- parse(canonical) → emit_canonical → parse → body 等值
- frontmatter 无变更时字节完全一致(引号/顺序都保留)
- 部署产物文件末尾完整出现 canonical body 原字节

字段级透传规则(`emitters/base.py: edit_frontmatter_fields`):
- 无任何语义变更 → 原样返回(完美字节稳定)
- 未变更字段 → 保留原始行(含引号/缩进/顺序)
- 变更/新增字段 → 用 safe_dump 重写该字段
- 删除字段(在 orig 不在 new) → 丢弃

---

## 删除链(安全边界)

**Skillbank 只动 manifest 记录过的路径**。机制保证:
- Agent 内置 skill / 用户手放 skill → 从未入 manifest → 永不被删
- 用户 import 进 canonical 的 skill → 之后由 Skillbank 全权管
- Agent 自建 skill(Hermes curator 自产 / 你 import 之外的)→ 不碰;想纳入跑 `import`

实例: Mac rm → 本机副本删;其它机器记录标 `pending_deletion=true`;
那台机器下次 `skillbank sync` 时执行删除并清记录。ln 类型只 unlink 软链,
canonical 目标绝不动。

---

## 能力矩阵(capabilities.toml)

⚠ **代码不再加载**(2026-08-17 清理)。`capabilities.py` 已删, sync/cli 不读它。
`capabilities.toml` 保留作"各 Agent 能力实测对照"的人工查阅文档。
canonical 的 `requires: [cap]` 当前仅作文档标注:emitter 不做能力过滤、不注入前言。

如需能力驱动的部署过滤/提示, 待将来在 emitter 层重新实现。

---

## 已知限制 / 后续 TODO

- **kimi 端 manual 级失效**:无 frontmatter 禁止触发字段;sync 输出 ⚠ 提示
- **Hermes 超 100k 字符 skill**:emitter 跳过 Hermes(`method=skipped`),
  body 零损耗不破(Hermes 缺席此 skill, 其他 Agent 正常同步)
- **archive 模块已实现但未接 CLI**:`archive.py` 有 `archive_skill`/`unarchive_skill`,
  但 CLI 无对应子命令。需要时在 cli.py 加 wiring
- **manifest 一个 JSON 增长无界** — 上百 skill 后考虑分片
- **import 跨 skill 相对路径引用**(`../shared/x`)— 已 warn 但不阻止
- **包形态 skill**(如 dws 含 `multi/` 20 个子 skill):整包 cp 即可, 各 Agent 只扫顶层
  `SKILL.md`, 不递归; 子 SKILL.md 当包内资源, 不被独立发现。外部依赖(如 dws 二进制)
  需目标机器自行安装, Skillbank 不校验

---

## 未实现(需求文档错误条目, 实测后作废)

- ❌ Qwen 硬编码 Python 路径替换(`E:\anaconda\...`)— QwenWorkCN 实测不存在,属 Qwen Code CLI 另一产品
- ❌ Qwen `priority`/`paths`/`user-invocable`/`source` frontmatter — 同上,不属 QwenWorkCN
- ❌ kimi 跟随 `~/.claude/skills` / 100% OpenClaw 兼容 — kimi 是 moonshot kimi-code 独立 Agent

---

## 测试 / 状态

118/118 tests green:
- `test_roundtrip.py` 14 — IR parser/emitter 回环零损耗 + frontmatter 字节稳定(引号保留)
- `test_emitter_*.py` — 7 Agent emitter 各自边界 + overrides 递归合并
- `test_manifest.py` — 删除链跨机语义
- `test_sync.py` — keep 真跳过(不重写盘/不刷 manifest) + 计划/执行
- `test_scan.py` — 路径自动探测 + 回写