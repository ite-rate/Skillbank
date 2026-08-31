# skillbank 命令参考(权威)

本文件是 `skillbank` 二进制全子命令的权威参考。SKILL.md 只做意图路由;
参数、语义、输出口径以本文件为准。

## 通用

- repo 根解析:`--repo <path>` > `SKILLBANK_REPO` 环境变量 >
  `~/.config/skillbank/config.toml` 的 `repo_path` > 当前目录向上找 `agents.toml`。
- `--machine` 默认取本机绑定(`skillbank use` 写的 `.skillbank-machine`,gitignored);
  未绑定且未显式指定时,命令拒绝执行并给指引(防在别的机器上按它机名义动盘)。
- 会改盘的命令都有 `--dry-run`(只展示,不写)。无人值守加 `--yes`。

## sync — canonical → 本机各 Agent

```
skillbank sync [-s <skill>...] [-a <agent>...] [--to <machine>] [--dry-run] [--yes] [--force]
```

- 三段式:collect(计划)→ show(人话展示)→ confirm → execute。
- 计划项:`+ deploy`(将部署)/ `= keep`(hash 相同跳过)/ `- skip`(未装/超限/被过滤)/
  `x delete`(本机清理)/ `p pending`(其它机器待删)/ `! warn` /
  `■ unmanaged`(目标被阻断, 用户资产未动)。
- **unmanaged 阻断**:部署目标已存在但本仓从未部署过它(用户手放的同名目录/
  软链/普通文件)→ 拒绝覆盖并给原因。软链**连 `--force` 也不放行**(cp 会写穿
  软链污染链目标; 逃生 = 手动摘链后重跑);普通文件/非目录、其它机器部署过的
  目录 `--force` 收编(先移除后部署);空目录直接放行。
- `keep` 是真幂等:不重写文件、不刷 manifest。资源自愈或 frontmatter 级变更
  (overrides/字段透传)落地需 `--force`。
- disable 级 skill 不部署;既有副本在下次 sync 被清(canonical 保留)。

## add / import — 反向收编

```
skillbank add <本地目录 | git URL> [--level auto|manual|experimental|disable] [--force] [--yes]
skillbank import <agent 的 skill 目录> [--agent <名>] [--level ...] [--force] [--yes]
```

- 产物:`skills/<name>/SKILL.md`(canonical frontmatter + body 原字节)+
  其余文件保真镜像 + `.agent_overrides/<agent>.toml`(agent 专有字段)。
- 缺 description 报错;无 frontmatter 边界报错。
- **source(p provenance)**:`add <git-url>` / `install` 会把来源 URL 写进
  canonical frontmatter 的 `source` 字段;源 SKILL.md 已有 `source` 则保留原值并
  警告。本地路径导入**不写** source(绝对路径跨机必断)。
- 重名策略:同 body → 静默去重;不同 body → 交互改名(建议名 `原名-agent短码`)。
- `import` 会探测 `native_agent`(源路径在 machines.toml 的哪个 skills_dir 下)。
- body 含绝对路径 / `../` 跨目录引用时给警告(跨机必断)。

## rm / set-level / archive — 生命周期

```
skillbank rm <name> [--dry-run]        # 删各机部署副本, canonical 留在 skills/(git 可恢复)
skillbank set-level <name> <level>     # 改触发策略; disable → 下次 sync 清所有副本
skillbank archive <name> [--dry-run]   # canonical 也移到 skills/.archive/(暂存)
skillbank unarchive <name>             # 移回 skills/ 且 level 强制 manual(审过再 auto)
skillbank archive-list                 # 归档清单
```

跨机删除链:本机 `rm`/`archive`/`set-level disable` 会给其它机器的记录标
`pending_deletion`,那些机器**各自下次 sync 时**删自己的副本。不需要也不会
远程登录别的机器。

## list / doctor — 状态

```
skillbank list [--agent <名>] [--level <级>]   # skill × agent 部署状态表
skillbank doctor [--skill <name>]              # 环境体检; --skill 深查 body 引用 vs 资源镜像
```

- `list` 单元格:`c`=cp `l`=ln `p`=pending `·`=未部署;`(孤儿)` = manifest 有
  记录但 canonical 已删。
- `doctor` 检查:配置加载 / 本机绑定 / 路径存在性 / manifest 一致性 / canonical
  可解析 / git 干净度。errors>0 返回非 0。
- `doctor --skill` 是防"静默失败"的关键:body 引用的 scripts/references 文件
  若没镜像进 canonical,这里能查出来(答案通常是 import 时漏了资源,`--force` 重导)。

## use / scan / zcode-cleanup — 本机身份与探测

```
skillbank use [<别名>]     # 不带参数 = 查看当前绑定
skillbank scan [--machine <别名>] [--yes] [--dry-run]
  # 探测本机 7 个 Agent 的 skills 目录 → 确认写入 machines.toml + 绑定身份
  # 首次在本机使用必须给 --machine(顺带注册新别名)
skillbank zcode-cleanup [--yes] [--dry-run]
  # ZCode skills 目录里的真实副本 → mv 备份 + 软链 canonical(逐个交互确认)
```

## init / bootstrap — 建仓与装机

```
skillbank init                        # 当前目录脚手架成新中心仓(skills/ + manifests/
                                      # + agents.toml + machines.toml + .gitignore + git init)
skillbank bootstrap [--repo-url <url>] [--machine <别名>] [--yes] [--dry-run]
  # 1. 本地无 repo → git clone <url> ~/Skillbank 并写 config.repo_path
  # 2. scan 探测 + machines.toml + 绑定身份
  # 3. sync(展示计划; --yes 免确认)
  # 4. doctor 汇总
```

bootstrap 依赖目标机有 git(clone 本身同前提,不算新增依赖)。

## install / pull — 一条龙动线

```
skillbank install <git-url> [--level L] [--force] [--machine <别名>] [--agent <名>] [--yes] [--dry-run]
  # 导入 git 仓里的 skill(SKILL.md 单文件或整仓) → 只把**本次新导入**的 skill
  # sync 到本机(不带 --agent/--to 时全 agent 默认机)。结束时打印
  # 「改动记得 commit + push 中心仓」。
  # 注意: install 的 --dry-run 会真实导入 skills/(只预览部署段) —— dry-run ≠ 零副作用。
  # 中心仓 machines.toml 未配置 → 导入照做, 提示先 skillbank scan, exit 0。
  # 非 git URL → 拒绝(exit 2), 本地目录用 add。

skillbank pull [--to <machine>] [--agent <名>] [-s <skill>...] [--yes] [--dry-run] [--no-doctor]
  # 日常动线一键: git pull → sync → doctor。
  # 1. 中心仓有未提交改动 → 中止(pull 可能半合并), --yes 不豁免;
  # 2. 有 remote 才拉(git pull --ff-only);分叉/冲突 → 提示手动解决, 绝不 reset;
  #    无 remote(本地-only 仓)→ 跳过 pull 继续 sync;
  # 3. sync(同 bootstrap 链式);
  # 4. doctor 默认跑且非致命(--no-doctor 给脚本)。
  # 注意: pull 的 --dry-run 跳过部署执行但不跳过 git pull —— dry-run ≠ 零副作用。
```

## 输出语义速查

- `[xxx]` 前缀 = 子命令名;`✓/⚠/✗` = 正常/警告/错误。
- exit code:0 成功(含"无动作");1 有失败;2 用法/身份错误。
- manifest(`manifests/deployments.json`)是部署状态的唯一真相源,字节级
  跨机兼容(indent=2, 非 ASCII 直出, 单尾换行),git diff 零噪音。