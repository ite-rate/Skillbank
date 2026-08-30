---
name: skillbank
description: 管理跨 AI agent 的 skill 资产:同步中心 skill 仓库到本机各 agent、反向导入既有 skill、部署体检。当用户提到 skill 同步/备份/迁移/整理/skill 仓库/部署 skill 到 agent 时使用。
level: auto
---

# Skillbank — 中心 skill 仓库管家

你有一个二进制工具 `skillbank`(在本 skill 的 bin/ 里),它把一个中心 git 仓库里的
canonical skill **字节零损耗地**同步到本机的各个 AI agent 目录(Claude Code、ZCode、
QwenWorkCN、TeleAgent、Hermes、Codex、kimi-code),也能把散落在 agent 目录里的既有
skill 反向收编进中心仓。

## 第一步:环境感知(每次会话开始先做)

1. **找二进制**:优先系统 PATH 里的 `skillbank`;没有则用本 skill 目录下的
   `bin/skillbank-<平台>`(darwin/linux × amd64/arm64,按 `uname -sm` 选),建议先
   `chmod +x` 并建议用户把它放进 PATH。
2. **读用户配置**:`~/.config/skillbank/config.toml`(记 repo_path / repo_url)。
   `repo_path` 没配 → 问用户中心仓库地址(git URL 或本地路径),不要自己猜。
3. `skillbank doctor` 一次,把 errors/warnings 人话汇报给用户。

## 意图分类 → 操作

| 用户意图 | 命令 |
|---|---|
| 新机器/云服务器装环境 | `skillbank bootstrap --repo-url <url> --machine <别名> --yes`(clone→探测→绑定→sync 一条龙) |
| 把改动推到本机各 agent | `skillbank sync`(会展示计划;确认后执行) |
| 收编某 agent 里的既有 skill | `skillbank import <skill 目录>` |
| 从 git/本地路径加新 skill | `skillbank add <路径或 URL>` |
| 不想再同步某 skill | `skillbank set-level <name> disable` |
| 彻底删部署副本(canonical 留 git) | `skillbank rm <name>` |
| 长期不用先收起 | `skillbank archive <name>` / `unarchive <name>` / `archive-list` |
| 看状态 | `skillbank list` / `skillbank doctor` / `doctor --skill <name>` |
| 从零建中心仓 | 空目录 `skillbank init` |

命令的权威参考(参数、语义、边界)在 `reference/` 下,执行前先查:
- `reference/commands.md` — 全子命令参考(**权威**,本文件只是路由)
- `reference/bootstrap.md` — 新机器 runbook
- `reference/conventions.md` — 中心仓库组织约定(frontmatter/level/入库三通道)
- `reference/safety.md` — 硬边界,动盘前必读

## 操作纪律

- **所有会改盘的命令先跑 `--dry-run`**,把计划念给用户,确认后再真执行。
  (`sync`/`rm`/`archive`/`zcode-cleanup`/`scan` 都有 `--dry-run`。)
- **`--machine` 不要乱填**:它是「本机在 machines.toml 里的别名」。不确定时先
  `skillbank use` 查看绑定,或让用户说清楚。跨机器的删除由 pending 机制在
  各机下次 sync 时自动执行,**绝不要在 A 机器上按 B 机器的名义操作**。
- **不动用户手放的 skill**:只管理 manifest 记录过的部署;同目录用户自装的
  原封不动。
- 交互场景(用户在场)不加 `--yes`,让工具自己问;无人值守(脚本/CI)加 `--yes`。
- canonical 仓库本身是 git:提醒用户改动(commit)以后要 push,skill 的跨机
  分享靠 git 而不是本工具直接传文件。

## 汇报口径

- 每次操作后给一句人话结论:做了什么、成功几个/失败几个、下一步建议。
- `doctor --skill <name>` 报"引用文件缺失"时,如实告诉用户:是 import 时漏了
  资源镜像,建议 `import --force` 重导;不要试图替用户修 agent 端的文件。

## 首跑引导(用户没给仓库地址时)

问一句:「你的 skill 中心仓库地址是?(git URL,或本地已有目录路径)」
- git URL → `bootstrap --repo-url <url> --machine <别名>`
- 本地路径 → 写进 `~/.config/skillbank/config.toml`:
  `repo_path = "<绝对路径>"`(该文件是用户资产,在 skill 目录外,更新 skill 不会丢)
- 用户说"还没有仓库" → 建议在空目录跑 `skillbank init`,之后把它推到自己的 git。