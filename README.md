# Skillbank

> Central canonical SKILL.md repository → 7 desktop AI agents.
> **body byte-identical, no loss** — frontmatter 经手 Skillbank 后字段级透传, 引号/顺序不漂移。
> Cross-machine sync via git (`Mac main edit → laptop periodic pull → server manual pull`)。

**单文件 Go 二进制**(静态编译, 无 Python/CGO 依赖, 一台 Mac 交叉编译全平台),
外加一个 skill 分发包(装进 agent, 用自然语言操作)。

---

## TL;DR — 新机器一条龙

```sh
skillbank bootstrap --repo-url <你的中心仓 git URL> --machine <本机别名> --yes
# = git clone → 探测本机 Agent → 写 machines.toml → 绑定身份 → sync → doctor
```

没有中心仓(第一台机器):

```sh
mkdir my-skillbank && cd my-skillbank
skillbank init          # 脚手架 skills/ manifests/ agents.toml machines.toml + git init
skillbank scan --machine main
skillbank import ~/.claude/skills/<某 skill>
git add -A && git commit -m "init skillbank"
```

二进制来源:`make build`(darwin/linux × amd64/arm64)或直接用 skill 包里的 `bin/`。
repo 根解析:`--repo` > `SKILLBANK_REPO` env > `~/.config/skillbank/config.toml` 的
`repo_path` > cwd 向上找 `agents.toml`。config.toml 模板见 `skill/config.toml.example`。

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

---

## Skill 分发包(装进 agent 自然语言操作)

`skill/` 是组装产物(`make skill`):

```
skill/
├── SKILL.md            # 意图路由(6 类) + 环境感知 + 操作纪律
├── reference/
│   ├── commands.md     # 权威命令参考(参数/语义/exit code 以此为准)
│   ├── bootstrap.md   # 新机器 runbook(3 场景)
│   ├── conventions.md  # 中心仓库组织约定
│   └── safety.md      # 硬边界(dry-run 先行 / 不碰用户 skill)
├── bin/                # 4 平台静态二进制(按 uname -sm 选)
└── config.toml.example
```

把 `skill/` 整个目录拷进任一 agent 的 skills 目录(如 `~/.claude/skills/skillbank`),
在会话里说「体检一下 skill 仓库」即可 — agent 读 SKILL.md 找到二进制、跑
doctor/list,变更操作先 dry-run 再确认。

---

## Canonical SKILL.md(frontmatter 正文)

```yaml
---
name: canvas-design
description: Create visual art. When the user asks for a poster, ...
level: auto                            # auto | manual | experimental | disable
native_agent: TeleAgent                # 可选;list/doctor 展示用(不注入 deployed body)
requires: [image_generation, file_write]   # 可选;仅文档标注(emitter 不做能力过滤)
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
存 `.agent_overrides/<agent>.toml`(skill 目录下)。sync 部署时从 overrides 递归合并回
deployed frontmatter(dict 深并, emitter 已写值优先)。

---

## Skill 分级(level)— 触发方式控制

| `level` | 同步? | 模型自动触发? | emitter 写什么 |
|---|---|---|---|
| `auto`          | ✅ | ✅ 允许 | 干净 frontmatter |
| `manual`        | ✅ | ❌ 禁止 | Claude/ZCode/Codex → `disable-model-invocation: true`; TeleAgent/Qwen → `enabled_at: false`; Hermes → `metadata.hermes.disable-model-invocation: true` |
| `experimental`  | ✅ | ❌ 禁止(同 manual) | 同 manual(语义标记区别) |
| `disable`       | ❌ 不同步 | — | 下次 sync 清掉所有已部署副本(canonical 保留) |

**已知限制:** `kimi-code` 无 frontmatter 禁止触发字段,`manual`/`experimental` 部署到
kimi 时 sync 输出 ⚠,需靠 description 话术或下级工具控制。

---

## CLI 全命令

```sh
# 建仓 / 装机
skillbank init                                  # 当前目录脚手架成新中心仓
skillbank bootstrap [--repo-url <url>] [--machine <别名>] [--yes]
                                                # clone → scan → 绑定 → sync → doctor 一条龙

# 路径配置(每机器一次)
skillbank scan [--machine <别名>] [--yes]       # 探测 + 写 machines.toml + 绑定身份
skillbank use [<别名>]                           # 绑定/查看本机身份

# 导入既有 skill 进 canonical
skillbank import <agent_skill_dir>              # 反向导入(自动探测 native_agent;_cn→_zh)
skillbank add <local_path | git_url>            # 本地目录 / git 仓库批量
skillbank import <dir> --agent ClaudeCode --level manual

# 同步
skillbank sync                                  # 交互选 skill×Agent → 计划 → 确认
skillbank sync -s <name> -a <agent> --yes       # 非交互单 skill 单 Agent
skillbank sync --dry-run                        # 只看计划不动盘
skillbank sync --force                           # keep 项强制重写(资源自愈/frontmatter 级变更)

# 删除 / 状态 / level / 归档
skillbank rm <name>                              # 本机删副本 + 其它机器标 pending
skillbank set-level <name> <auto|manual|experimental|disable>
skillbank list [--agent <名>] [--level <级>]     # skill × agent 状态表
skillbank archive <name>                         # canonical 移入 skills/.archive/
skillbank unarchive <name>
skillbank archive-list

# 体检
skillbank doctor                                 # 配置/绑定/路径/manifest/canonical/git
skillbank doctor --skill <name>                  # body 引用 vs 资源镜像一致性
skillbank zcode-cleanup                          # ZCode 真实副本迁中央 + 软链(逐个确认)
```

全部动盘命令支持 `--dry-run`;`--yes` 免交互。exit code:0 成功、1 有失败、2 用法/身份错误。

---

## 本机身份绑定

所有命令的 `--machine`/`--to` 默认取绑定值(不硬编码):
- 绑定:`skillbank use <别名>` 或 `skillbank scan --machine <别名>`(存 repo 内
  `.skillbank-machine`, gitignored;重 clone 需重新绑定)
- 未绑定时,依赖默认值的命令**拒绝执行**并给指引(防在别的机器上按它机名义误动本机文件)
- 已绑定后显式传不同 `--machine`(会动本机磁盘的命令)会打 ⚠ 提示

跨机机制 = **git 仓库本身当跨机消息总线**:
- A 机改 canonical + sync → manifest 写记录(谁部署到哪)→ git commit/push
- B 机 git pull → `skillbank sync` 自动执行 pending_deletion + 计划部署
- body hash 比对 manifest 的 `ir_hash` 可证各机器收到的 body 一字不差

---

## Pipeline(parser→IR→emitter, 零损耗如何保证)

```
canonical SKILL.md (skills/<name>/SKILL.md)
  └─ parser.ParseCanonical()
        ├─ bytes 读全文, byte-level 切 frontmatter 边界(允许 \r\n)
        ├─ body 取边界后全部原字节 → ir.SkillIR.Body []byte (不 decode 不 normalize)
        └─ frontmatter 原字节 + 解析 dict 都存入 IR(fm_raw / fm_orig)
              └─ emit/<agent>.emit()
                    ├─ 字段级透传:未变更字段保原字节(引号/顺序不漂),
                    │   仅重写翻译字段(level→禁触发/双语镜像/Codex截断/...)
                    ├─ overrides 递归合并回 frontmatter
                    ├─ body 直接跟 frontmatter(无前言, 不注入任何元信息)
                    ├─ resources/ 全目录镜像(相对路径继续有效)
                    └─ 部署产物写盘(原子 tmp+rename)
                          └─ manifest 记录 (deploy_path + ir_hash=body sha256)
```

零损耗验证:`go test ./...` — roundtrip(body 回环等值)、frontmatter 无变更字节完全一致、
部署产物文件末尾完整出现 canonical body 原字节、sync keep 幂等(mtime 不动、manifest 零 diff)、
manifest JSON 跨实现字节兼容(indent=2, 非 ASCII 直出, 字段序固定, 单尾换行)。

---

## 删除链(安全边界)

**Skillbank 只动 manifest 记录过的路径**。机制保证:
- Agent 内置 skill / 用户手放 skill → 从未入 manifest → 永不被删
- 用户 import 进 canonical 的 skill → 之后由 Skillbank 全权管
- Agent 自建 skill(Hermes curator 自产 / import 之外的)→ 不碰;想纳入跑 `import`

实例: A 机 rm → 本机副本删;其它机器记录标 `pending_deletion=true`;
那台机器下次 `skillbank sync` 时执行删除并清记录。ln 类型只 unlink 软链,
canonical 目标绝不动。

**归档 vs 删除**:`rm` 只删部署副本、canonical 仍留在 `skills/`;`archive` 连 canonical
也移到 `skills/.archive/`(list 默认不显示);`unarchive` 移回 + 置 level=manual。
`.archive/` 在 git 里追踪, canonical 跨机随仓库走, 不丢。

---

## 开发

```sh
make test      # go test ./...
make build     # 4 平台二进制 → dist/
make skill     # 组装 skill/ 分发包(拷入 dist/ 二进制)
```

结构:`cmd/skillbank`(入口)+ `internal/{ir,parser,emit,config,identity,manifest,
sync,scan,importer,archive,refs,interactive,cli,bootstrap}`。依赖仅
yaml.v3 + BurntSushi/toml,CGO_ENABLED=0。139 个 Go 测试全绿(语义与原 Python
132 条等价 + bootstrap/init/skill 包新增)。

---

## 已知限制 / 后续 TODO

见 `TODO.md`。要点:kimi 端 manual 级失效(无禁触发字段)、Hermes 超 100k 跳过、
manifest 单 JSON 无界增长、import 跨目录相对路径 warn 不阻止。

---

## 未实现(需求文档错误条目, 实测后作废)

- ❌ Qwen 硬编码 Python 路径替换(`E:\anaconda\...`)— QwenWorkCN 实测不存在,属 Qwen Code CLI 另一产品
- ❌ Qwen `priority`/`paths`/`user-invocable`/`source` frontmatter — 同上
- ❌ kimi 跟随 `~/.claude/skills` / 100% OpenClaw 兼容 — kimi 是 moonshot kimi-code 独立 Agent