# 中心仓库组织约定

## 目录

```
<repo>/
├── agents.toml        # 7 个 Agent 的集成方式(emitter 读它; 一般不动)
├── machines.toml      # 机器档案: 每台机器装了哪些 agent、skills 目录在哪
├── skills/            # canonical skill 平铺目录
│   ├── <skill-name>/
│   │   ├── SKILL.md          # 唯一权威源(frontmatter + body)
│   │   ├── scripts/ references/ ...   # 资源镜像(body 里相对路径引用)
│   │   └── .agent_overrides/<agent>.toml  # agent 专有字段(不污染 canonical)
│   └── .archive/<name>/      # 归档区(sync 不扫, list 不显示)
├── manifests/
│   └── deployments.json      # 部署状态唯一真相源(跨机 git 同步)
└── .skillbank-machine        # 本机身份绑定(gitignored)
```

skill 一律平铺在 `skills/<name>/`,不搞分类子目录 — 找 skill 靠名字,
分类信息放 frontmatter。

## canonical SKILL.md frontmatter

| 字段 | 说明 |
|---|---|
| `name` | 必须等于目录名(不一致时以目录名为准 + doctor 警告) |
| `description` | 必填;触发话术, 写清"什么时候用" |
| `level` | 触发策略, 见下 |
| `native_agent` | 这个 skill 从哪个 agent 收编来(溯源) |
| `requires` | 能力依赖清单(如 image_generation) |
| `description_zh` / `name_zh` | 中文案(QwenWorkCN 直传, TeleAgent 由 _cn 映射) |
| `version` / `license` | 元数据 |
| `source` | 来源 provenance(git URL);本地导入不写;字段顺序在 license 之后 |

其它字段(如市场来源的 `install_source`/`skill_id`)不进 canonical,由 import
自动落到 `.agent_overrides/`。

## level 触发策略

| level | 语义 |
|---|---|
| `auto` | 各 agent 正常自动触发 |
| `manual` | 用户显式点名才触发(写 agent 的禁触发字段) |
| `experimental` | 同 manual 语义, 标记未验证 |
| `disable` | 不同步;已有副本下次 sync 清掉(canonical 留 git) |

新 import 的 skill 默认 `manual` — 审过再 `set-level auto`。

## 入库三通道

1. `skillbank import <agent 的 skill 目录>` — 从本机 agent 目录收编(最常用);
2. `skillbank add <本地路径>` — 从任意本地目录;
3. `skillbank add <git URL>` — 从一个 git 仓库批量收编(浅 clone 后逐个导)。

共同契约:body 字节原样进 canonical(CRLF/空行/tabs 保留),资源文件保真镜像,
缺 description 拒绝,重名同 body 去重、不同 body 改名。

## 同步语义

- body hash 相同 → `keep`(不重写不刷 manifest,真幂等);
- body 变 → 重新部署 + 刷新 hash;
- canonical 删了(git rm)→ 孤儿记录自动清理;
- manifest JSON 格式跨实现字节兼容,git diff 里只有真实变更。