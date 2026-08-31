# 新机器 runbook(云服务器 / 二手机 / 重装)

目标:在一台新机器上,从"什么都没有"到"本机所有 agent 的 skill 与中心仓一致"。

## 场景 A:已有中心仓(最常见)

```bash
# 1. 装二进制(首选 install 脚本: 下载 + SHA256 校验 + 放 PATH)
curl -fsSL https://raw.githubusercontent.com/ite-rate/Skillbank/main/scripts/install.sh | sh
# 或手动: 到 https://github.com/ite-rate/Skillbank/releases 下载
# skillbank-<os>-<arch>(按 uname -sm 选), chmod +x 后 mv 进 PATH。

# 2. 一条龙(需要 git)
skillbank bootstrap --repo-url <中心仓 git URL> --machine <本机别名> --yes
```

bootstrap 自动做了:
1. `git clone --depth 1` 中心仓 → `~/Skillbank`,并把路径写进
   `~/.config/skillbank/config.toml`(以后在任意目录运行都能找到 repo);
2. 探测本机 7 个 Agent 的 skills 目录 → 写 `machines.toml`;
3. 绑定本机身份(`.skillbank-machine`,gitignored);
4. 同步 + 体检汇总。

想先看会做什么:`skillbank bootstrap --repo-url <...> --machine <...> --dry-run`。

## 场景 B:机器装了 agent 但想先确认探测结果

```bash
skillbank scan --machine <别名>          # 逐个确认候选目录
skillbank use <别名>                     # 绑定身份(不带参数 = 查看)
skillbank sync                           # 展示计划, 确认后执行
```

## 场景 C:还没有中心仓(第一台机器)

```bash
mkdir my-skillbank && cd my-skillbank
skillbank init                  # 脚手架: skills/ + manifests/ + agents.toml + machines.toml + git init
skillbank scan --machine main   # 注册本机
skillbank import ~/.claude/skills/<某 skill>   # 把既有 skill 收编进中心仓
git add -A && git commit -m "init skillbank"
git remote add origin <你的私有 git> && git push -u origin main
```

## 装完后验证

```bash
skillbank doctor        # 应 OK(0 errors)
skillbank list          # skill × agent 状态表
```

## 注意

- `--machine <别名>` 是**本机**在 machines.toml 里的名字,一台机器一个别名,
  别复用别的机器的别名(删除链按机器名路由,别名混用会误删)。
- 绑定文件 `.skillbank-machine` 不进 git;重 clone 的机器要重新 `skillbank use`。
- bootstrap 之后日常只有一件事:`git pull` + `skillbank sync`。