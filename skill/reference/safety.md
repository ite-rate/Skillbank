# 硬边界(动盘前必读)

这些规则同时是工具的实现语义,不要试图绕过。

## 先 dry-run,后执行

`sync` / `rm` / `archive` / `zcode-cleanup` / `scan` / `bootstrap` 全部支持
`--dry-run`。替用户操作时,第一次一律 `--dry-run`,把计划念给用户确认,
再真执行。

## 机器身份不冒名

- `--machine` = 本机别名。工具默认用 `.skillbank-machine` 绑定;
  未绑定时拒绝执行而不是猜。
- 显式 `--machine` 与本机绑定不同名时,工具会打 ⚠ — 此时停下向用户核实,
  不要继续。
- 跨机删除靠 pending 标记:本机操作 → 其它机器**各自下次 sync**删自己的副本。
  绝不存在"远程登录别的机器删文件"的路径,也不要手工构造。

## 不碰的东西

- **用户手放的 skill**:删除链只动 manifest 记录过的路径,同目录其它内容
  原封不动。
- **部署阻断**:写路径同合同 —— 部署目标既存在又不属于本仓(unmanaged)时
  拒绝覆盖(计划标 `■`);软链目标 `--force` 也不放行(写穿会污染链目标),
  解法是手动摘链后重跑;非目录/它机部署过的目录可 `--force` 收编。
- **canonical 目录**:任何"清理部署"操作都不删 `skills/<name>/`
  (archive 是 mv 到 `.archive/`,不是删)。
- **agent 自建目录**:从不写 agents.toml 之外的 agent 配置,不碰 agent 的
  状态文件(如 Hermes 的 `.hub/`)。
- **软链目标**:`ln`/软链记录删除时只 unlink 链本身,目标(canonical)不动。

## 写盘纪律

- 所有落盘原子写(tmp + rename),不留 `.tmp` 残留。
- keep 幂等:hash 相同不重写(用户手改部署端文件不会被静默覆盖;
  要自愈显式 `--force`)。
- 不修改 body 字节:canonical → 部署端,body 永远原样
  (CRLF/BOM/tabs/空行全部保留)。变更只发生在 frontmatter 字段级。

## 失败处理

- 单个 skill 部署失败不中断其它;末尾报失败数。
- 解析失败的 skill 在 sync 里是 `warn` 项,不阻塞。
- doctor errors>0 时如实报告,不要粉饰为"基本成功"。