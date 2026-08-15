# Skillbank 后续迭代 TODO

> M0-M7 已完成(14 commit, 102/102 测试全绿)。本文是 M7 之后用户实际使用中预演出来的、需要迭代的项。
> 排序按优先级(P0 已完, P1 待用户实战暴露后再定, P2 是已知 polish)。

## P0 已修(M6 修 commit `61d2761`)

- [x] #1 import 时 warn body 绝对/跨目录路径 (`importer.scan_body_paths`)
- [x] #2 unknown 能力提示措辞改柔和(不怂恿模型中止,`prompt_inject._unknown_hint` ❓ vs ⚠️ 分开)
- [x] #3 kimi `manual` 级显式 warn(kimi 无 frontmatter 禁触发字段, 该端仍自动触发)
- [x] #4 Codex 截断优先保留触发关键词(`use when ...` 末句, 中间 ` ... ` 分界计入总长)

## P1 (待用户真机首次 sync 后看实际是否暴露)

- [ ] 真机首次实战: 用户亲手 import+sync 到 mac-main(需用户批准 — 会真写 `~/.claude/skills` 等)
- [ ] git remote 接入(GitHub 私库 / 自托管) — 由用户决定后配置

## P2 后续 polish

- [ ] #6 Hermes skipped 在 `list` 里区分原因(存 skipped meta 入 manifest, screen 区分 `·`/`~`)
- [ ] #8 sync 加 `--all-skills` 默认全选(避免大量 skill 交互菜单长)
- [ ] #9 canonical `_zh` vs TeleAgent `_cn` 差异在 README 继续补例(当前仅说明逻辑)
- [ ] #10 manifest 大量 skill 后分片(`manifests/<skill>.json` 或按 machine 切)
- [ ] #11 import 跨 skill 相对引用(`../shared/x`)跨机深 warn(当前浅 warn)
- [ ] #12 import 后 doctor 报告未识别 frontmatter 字段(已透传到 overrides, 但用户应知情)
- [ ] #13 交叉 symlink 去重(claude<->zcode<->codex 指同一处时,list 应折叠展示而非 3 行重复)
- [ ] #14 Hermes `.usage.json` 作为真实使用频率源入 Skillbank `list`(本扫描调研后定方案)

## 长期 consideration(不计入迭代, 留碍)

- 多人协作场景下 manifest 加 file lock(当前单人编辑流够用)
- 中央仓 WEB UI?(过度工程, CLI 够用)
- 主动从 skillMarket 拉取更新(import 已支持 git URL, 自动定时未做)