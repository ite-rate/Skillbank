# Skillbank

> 把一份 canonical `SKILL.md` 资产库,字节零损耗地同步到本机全部 7 个桌面 AI Agent。
> **body byte-identical, no loss** — frontmatter 字段级透传, 引号/顺序/空行不漂移。
> 跨机同步 = git 本身(`A 机改 → push → B 机 pull → sync`)。

单文件 Go 二进制(静态编译, 无 Python、无 CGO,一台 Mac 交叉编译全平台),
外加一个 skill 分发包 — 装进 agent 后用户说自然语言,agent 照 `SKILL.md` 操作二进制。

---

## 两仓库架构

| 仓库 | 内容 | 举例 |
|---|---|---|
| **工具仓**(本仓) | Go 源码 + `skill/` 分发包 + Makefile | 你现在看的这个 |
| **中心仓**(你自己的私有 repo) | `skills/` + `manifests/` + `agents.toml` + `machines.toml` + 本机绑定 | `git@github.com:you/my-skills.git` |

skill **资产**归你的中心仓,private git 托管,可换机器可协作;工具仓只管代码,
不掺任何用户数据。中心仓目录结构约定见
[`skill/reference/conventions.md`](skill/reference/conventions.md)。

工具不用安装到中心仓目录:repo 根按
`--repo > SKILLBANK_REPO 环境变量 > ~/.config/skillbank/config.toml 的 repo_path > cwd 向上找 agents.toml`
解析,在任意目录都能跑。

---

## 上手三选一

**A. 已有中心仓 → 一条龙装机**(新机器/云服务器):

```sh
skillbank bootstrap --repo-url <中心仓 git URL> --machine <本机别名> --yes
# = git clone → 自动探测 7 Agent 目录 → 写 machines.toml → 绑定身份 → sync → doctor
```

**B. 第一台机器,从零建中心仓:**

```sh
mkdir my-skills && cd my-skills
skillbank init                                    # 脚手架 + git init(幂等)
skillbank import ~/.claude/skills/<某 skill>      # 收编散落在 agent 里的既有 skill
skillbank scan --machine main                     # 探测本机 agent → machines.toml
skillbank sync                                    # 计划预览 → 确认 → 部署
git add -A && git commit -m "init" && git push    # 推到你自己的私有 git
```

**C. 装成 skill,让 agent 来操作**(kimi-slides 形态):

本仓 clone 下来后 `skill/` 目录即是分发包(`skill/bin/` 里带 4 平台静态二进制):

```sh
cp -R skill ~/.claude/skills/skillbank
# 会话里说:「体检一下我的 skill 仓库」「把 xx 收进中心仓」——agent 读 SKILL.md 自己跑
```

首次使用需让工具知道中心仓在哪:写 `~/.config/skillbank/config.toml`
(模板见 [`skill/config.toml.example`](skill/config.toml.example)),或让
bootstrap 自动写,或跑命令时用 `--repo` / `SKILLBANK_REPO`。

---

## 7 目标 Agent(实测真身)

| Skillbank key | 真实产品 | skills_dir (实测示例) | frontmatter 方言 |
|---|---|---|---|
| `ClaudeCode`  | Anthropic Claude Code  | `~/.claude/skills` | name + description (+ `disable-model-invocation: true`) |
| `ZCode`       | 智谱 ZCode (GLM) | `~/.zcode/skills` | 同 ClaudeCode |
| `QwenWorkCN`  | 阿里 QwenWorkCN 千问办公(**非** Qwen Code CLI) | `~/.qwenworkcn/skills` | + `description_zh`/`name_zh` (+ `enabled_at: false`) |
| `TeleAgent`   | TeleAgent (OpenCode 内核) | `~/.config/TeleAgent/skills` | + `description_cn`/`name_cn` (从 canonical `_zh` 镜像) (+ `enabled_at: false`) |
| `Hermes`      | NousResearch Hermes | `~/.hermes/skills/<category>/` | + `metadata.hermes.disable-model-invocation` (category 默认 `imported/`) |
| `Codex`       | OpenAI Codex | `~/.codex/skills` | + `disable-model-invocation`, description ≤1024 字符截断 |
| `kimi-code`   | moonshot kimi-code | `~/.kimi-code/skills` | name + description(无 frontmatter 禁触发字段) |

**全部 7 个 Agent 一律 cp 部署**(emitter 硬编码)。没装的 agent 探测/手填后跳过,不报错;
单机只装其中两三个是常态。

识别为哪套方言、`level` 如何映射成各家的禁触发字段,细则见
[`skill/reference/commands.md`](skill/reference/commands.md) 与
[`skill/reference/conventions.md`](skill/reference/conventions.md)。

---

## 核心不变量(为什么敢改这一行)

```
canonical SKILL.md (skills/<name>/SKILL.md)
  └── parser.ParseCanonical
      ├─ byte 级切 frontmatter 边界(允许 \r\n), body 取其后全部原字节
      ├─ SkillIR.Body []byte — 不 decode、不 normalize(CRLF/BOM/tabs/null 全保留)
      └── fm_raw(frontmatter 原字节)+ fm_orig(解析 dict)双存
        └── emit: 字段级透传
            ├─ 未变更字段 → 保留原始行(引号/缩进/顺序一字符不动)
            ├─ 变更/新增字段 → 重写;删除字段 → 丢弃
            ├─ agent 专有字段从 .agent_overrides/<agent>.toml 递归合并
            └─ body 原字节接 frontmatter, 零注入、零前言
                └── 原子写(tmp + rename)+ manifest 记录 (deploy_path, ir_hash=sha256(body))
```

不变量由测试锁死(`go test ./...` 139 全绿):

- parse → emit canonical → parse:**body 字节等值**
- frontmatter 无语义变更 → **整文件字节一致**(引号/顺序保留)
- 部署产物文件末尾**完整出现** canonical body 原字节
- manifest JSON 跨实现字节兼容(indent=2、非 ASCII 直出、字段序固定、单尾换行)
  → git diff 里只有真实变更,零噪音
- sync keep 真幂等:hash 相同不重写、不刷 manifest(用户手改部署端不被静默覆盖)

---

## 安全边界(删除为什么不会误伤)

**只动 manifest 记录过的路径**:

- agent 自带 / 用户手放的 skill → 从未进 manifest → 永不触碰
- 跨机删除 = pending 标记:A 机 `rm` → 其它机器记录标 `pending_deletion`
  → B 机**自己下次 sync 时**删自己的副本。不存在远程替别的机器删文件的路径
- 软链部署只 unlink 链本身,canonical 目标不动
- 本机身份绑定 `.skillbank-machine`(gitignored):未绑定拒绝执行,
  显式 `--machine` 与绑定不符打 ⚠ — 防 A 机按 B 机名义误操作
- 所有动盘命令支持 `--dry-run`;`doctor --skill` 查 body 引用 vs 资源镜像(防 silent failure)

细则见 [`skill/reference/safety.md`](skill/reference/safety.md)。

---

## 命令速览

```sh
skillbank sync                        # canonical → 本机各 Agent(计划 → 确认 → 执行; keep 幂等)
skillbank import <agent skill 目录>   # 反向收编自动探测 native_agent + 双语 _cn→_zh
skillbank add <本地路径 | git URL>     # 任意目录 / git 仓库批量收编
skillbank rm <name>                   # 删部署副本, canonical 留 git; 其它机 pending
skillbank archive / unarchive / set-level <name> <auto|manual|experimental|disable>
skillbank list / doctor [--skill <name>]
skillbank scan --machine <别名>        # 首次本机: 探测 + 注册 + 绑定
skillbank use [<别名>]                 # 绑定/查看本机身份
skillbank init / bootstrap / zcode-cleanup
```

全命令参数、exit code、计划项语义的权威参考:
[`skill/reference/commands.md`](skill/reference/commands.md)。

---

## 开发

```sh
make test      # go test ./...  (139 tests)
make build     # 4 平台交叉编译 → dist/  (darwin/linux × amd64/arm64, CGO_ENABLED=0)
make skill     # 把 dist/ 二进制拷进 skill/bin/ 组装分发包
```

结构:`cmd/skillbank`(入口)+ `internal/{ir,parser,emit,config,identity,manifest,
sync,scan,importer,archive,refs,interactive,cli,bootstrap}`。
依赖只有 `gopkg.in/yaml.v3` + `github.com/BurntSushi/toml`。
`capabilities.toml` 是人工参考文档(各 Agent 能力实测矩阵),代码不加载。

---

## 已知限制

- **kimi-code 无 frontmatter 禁触发字段**:`manual`/`experimental` 部署到 kimi 时
  sync 输出 ⚠,该端模型仍可能自动触发,靠 description 话术控制
- **Hermes 超 100k 字符 skill**:跳过 Hermes 端该 skill,其它 agent 正常(body 零损耗不破)
- **manifest 单文件无界增长**:skill 上百后考虑分片
- **import 跨 skill 相对路径引用**(`../shared/x`):warn 不阻止,跨机会断
- **外部依赖不校验**(如某 skill 要 dws 二进制):目标机器自行安装

[`TODO.md`](TODO.md) 是后续迭代清单。

---

## License

MIT — 见 [LICENSE](LICENSE)。