# Skillbank 后续迭代 TODO

> v2.0.0: Go 移植完成(单文件静态二进制 + skill 分发包), Python 实现已退役删除。
> 139 个 Go 测试全绿, 真机 dry-run 与 Python 版逐字节一致, sync keep 幂等 manifest 零 diff,
> bootstrap 冒烟(clone→scan→绑定→sync→doctor)通过。

## v2.1(2026-08-31)

- [x] canonical 加 `source` 字段(import git URL 时写 provenance;nil-omitted, 既有资产零 diff)
  - 未来若做 `update <name>`,需再议是否持久化 commit(`source_commit`):本地一编辑 commit 就失真,宁可先不写
- [x] `install <git-url>` 命令(导入 + 只同步新 skill 一条龙)
- [x] `pull` 命令(git pull --ff-only → sync → doctor;脏树中止,分叉提示手动解决)
- [x] 修 v2.0 老bug: `sync -s <名>` / `-a` 短旗标只注册未绑定指针, 调用即 SIGSEGV
  (长形 `--skill` 一直正常;现别名指同一槽位 + 回归测试)
- [x] **覆盖语义反转(行为变更)**: 同名非托管目标一律 `■ unmanaged` 阻断,
  不再静默 clobber;软链目标 `--force` 也不放行(写穿会污染链目标);普通文件/非目录
  `--force` 收编(先移除再部署)。老用户靠 cp 覆盖"修复"的路径现在必须 `--force`
- [x] 二进制出库 → GitHub Releases(release.yml 打 tag 自动传 + SHA256SUMS;
  `scripts/install.sh` 下载并校验): tradeoff = 离线 fresh clone 需先 `make build`
- [ ] 遗留: Hermes `DefaultCategory` 变更后,旧类目的部署目录会成孤儿
  (manifest Upsert 按 (skill, machine, agent) 记录换了 deploy_path, 旧目录无记录,
  得手动删;既有问题非 v2.1 引入)

## v2.0.0 已完成(2026-08-30)

- [x] Go 全量移植(parser/IR/7 emitter 字节稳定合同/sync/manifest/删除链/身份绑定)
- [x] bootstrap 子命令(clone → scan → 绑定 → sync → doctor 一条龙)
- [x] init 子命令(脚手架新中心仓)
- [x] repo 根解析链(--repo > SKILLBANK_REPO > config.toml > cwd 向上)
- [x] Makefile 四平台交叉编译 + `make skill` 组装分发包
- [x] skill/ 分发包(SKILL.md + reference 4 篇 + bin/ + config 模板)
- [x] manifest JSON 跨实现字节兼容(git diff 零噪音)
- [x] 真机验证:Go sync --dry-run 与 Python 输出逐字节一致;真执行全 keep、manifest 零 diff

## P1 待用户实战暴露

- [ ] skill 分发包真装进 ~/.claude/skills/skillbank, 会话内自然语言操练一轮
- [ ] bootstrap 冒烟在第二台机器(或云服务器)实走一次

## P2 后续 polish

- [ ] #6 Hermes skipped 在 `list` 里区分原因(存 skipped meta 入 manifest, 区分 `·`/`~`)
- [ ] #8 sync 加 `--all-skills` 默认全选(避免大量 skill 交互菜单长)
- [ ] #9 canonical `_zh` vs TeleAgent `_cn` 差异在 README 补例
- [ ] #10 manifest 大量 skill 后分片
- [ ] #11 import 跨 skill 相对引用(`../shared/x`)跨机深 warn
- [ ] #12 import 后 doctor 报告未识别 frontmatter 字段
- [ ] #13 交叉 symlink 去重(list 折叠展示)
- [ ] #14 Hermes `.usage.json` 作为使用频率源入 `list`
- [ ] #15 本机身份 hostname 交叉校验(绑定文件格式已留扩展位)

## 长期 consideration(不计入迭代, 留碍)

- 多人协作场景下 manifest 加 file lock(当前单人编辑流够用)
- 中央仓 WEB UI?(过度工程, CLI 够用)
- 主动从 skillMarket 拉取更新(import 已支持 git URL, 自动定时未做)