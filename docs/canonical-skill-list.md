# Skillbank canonical 全量 skill 分类表（166 个）

> Hermes 频率列来自 `.usage.json` 的 `use_count`/`last_used_at`（仅 Hermes 有此数据，其他 Agent 无频率记录）


## 学术研究（15 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `ai-coding-agent-research` | Hermes | manual | 4次/07-22 | 评估/对比 AI coding agent 能力与选型 |
| `autoresearchclaw-run-and-monitor` | Hermes | manual | — | 跑 AutoResearchClaw 自动研究流程, 验证配置和监控 |
| `deep-research` | TeleAgent | manual | — | 中文深度研究: 调研/全面调查/行业分析/生成研究报告 |
| `deli-autoresearch` | ClaudeCode | manual | — | 长周期自主研究框架, 跑多步骤开放式调研 |
| `job-market-research` | Hermes | manual | 5次/07-27 | 对比职业方向/岗位市场需求 |
| `live-job-market-research` | Hermes | manual | 3次/07-27 | 从公开招聘源实时研究招聘趋势 |
| `llm-model-release-research` | Hermes | manual | 2次/08-14 | 追踪 AI 模型发布动态, 查哪个厂商出了什么模型 |
| `paper-experiment-design` | ClaudeCode | manual | — | 为论文设计实验验证方案 |
| `paper-guardrails` | ClaudeCode | manual | — | 多步骤论文写作的轻量编排层(防跑偏) |
| `paper-literature-survey` | ClaudeCode | manual | — | 加强论文的文献基础/综述 |
| `paper-peer-review` | ClaudeCode | manual | — | 模拟同行评审, 多角色审稿给修改意见 |
| `paper-structure-logic` | ClaudeCode | manual | — | 起草/重组/修复论文结构逻辑 |
| `pre-submission-reviewer` | ClaudeCode | manual | — | 论文提交前五维审查(逻辑/写作/语法/LaTeX/图表) |
| `research-kickoff` | ClaudeCode | manual | — | 启动开放式研究论文项目 |
| `research-paper-writing` | ClaudeCode | manual | — | 端到端论文写作与修订流水线 |


## 文档生成（14 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `data-report` | QwenWorkCN | manual | — | 从 Excel/CSV 表格生成自包含 HTML 数据分析报告 |
| `docx` | QwenWorkCN | manual | — | QwenWorkCN 版 Word 文档创建/读取/编辑 |
| `docx-tele` | TeleAgent | manual | — | TeleAgent 版文档创建/编辑/分析 |
| `paddleocr-doc-parsing` | TeleAgent | manual | — | 复杂版式 PDF 的 OCR 兜底解析 |
| `pdf` | Hermes | manual | 1次/08-13 | Hermes 版 PDF 创建/读取/合并/填表/加密 |
| `pdf-qwen` | QwenWorkCN | manual | — | QwenWorkCN 版 PDF 全功能处理 |
| `pdf-tele` | TeleAgent | manual | — | TeleAgent 版 PDF 生成(视觉精修版) |
| `powerpoint` | Hermes | manual | 7次/08-12 | Hermes 版 PPT 创建/读取/编辑/模板 |
| `pptx` | QwenWorkCN | manual | — | QwenWorkCN 版 PPT 全功能 |
| `pptx-tele` | TeleAgent | manual | — | TeleAgent 版中文 PPT(汇报/提案/课件/路演) |
| `print` | TeleAgent | manual | — | 通用文档打印(PDF/Word/Excel/PPT/图片→真打印机) |
| `scanned-pdf-ocr` | Hermes | manual | 1次/08-03 | 扫描件/图片型 PDF 的 OCR 文字提取 |
| `xlsx` | QwenWorkCN | manual | — | QwenWorkCN 版 Excel 全功能 |
| `xlsx-tele` | TeleAgent | manual | — | TeleAgent 版电子表格创建/编辑/分析 |


## 创意/视觉（26 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `baoyu-article-illustrator` | Hermes | manual | — | 为文章配插图(类型×风格×配色一致) |
| `baoyu-comic` | Hermes | manual | — | 知识漫画: 教育/传记/教程类漫画生成 |
| `batch-video-generation-workflows` | Hermes | manual | 5次/07-30 | 批量 AI 视频生成工作流调研 |
| `brandkit` |  | manual | — | 高端品牌套件图片生成 |
| `canvas-design` | TeleAgent | manual | — | 设计哲学驱动 + AI 生图的高品质海报/视觉创作 |
| `design-taste-frontend` |  | manual | — | 反 slop 前端设计 skill(落地页/作品集/品牌站) |
| `design-taste-frontend-v1` |  | manual | — | v1 版审美 skill, 旧项目依赖保留 |
| `diagram-drawing` | TeleAgent | manual | — | 自然语言生成专业图表(流程图/架构图/时序图等) |
| `figure-designer` | ClaudeCode | manual | — | 技术论文三张核心图表设计指导 |
| `frontend-design` | TeleAgent | manual | — | 前端视觉设计指导(差异化/有意图) |
| `frontend-review` | ZCode | manual | — | 前端代码审查: 可访问性/安全/性能 |
| `go-interview-rapid-project-design` | Hermes | manual | — | 面试速成: 共设计一个最小 Go 项目 |
| `gpt-taste` |  | manual | — | GPT 审美 UX/UI + GSAP 动效工程 |
| `hearth` | ZCode | manual | — | 火炉边房间 — 关系与家庭议题讨论 |
| `high-end-visual-design` |  | manual | — | 高端代理商级视觉设计教学 |
| `image-to-code` |  | manual | — | 网站截图转代码(视觉精准还原) |
| `imagegen` | Codex | manual | — | AI 光栅图片生成/编辑(Codex 内置) |
| `imagegen-frontend-mobile` |  | manual | — | 移动端 App 高品质配图生成 |
| `imagegen-frontend-web` |  | manual | — | 前端网页高品质配图生成 |
| `industrial-brutalist-ui` |  | manual | — | 工业粗野主义 UI(瑞士印刷+机械感) |
| `infographic` | TeleAgent | manual | — | 21 种版式的专业信息图生成 |
| `minimalist-ui` |  | manual | — | 极简编辑风格 UI(暖色单色) |
| `pixel-art` | Hermes | manual | — | 像素画(NES/Game Boy/PICO-8 调色板) |
| `redesign-existing-projects` |  | manual | — | 升级现有网站/App 到高端品质 |
| `stitch-design-taste` |  | manual | — | Google Stitch 语义设计系统生成 |
| `web-artifacts-builder` | TeleAgent | manual | — | 复杂多组件 Claude web artifact 构建 |


## 开发工程（31 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `archify` | ZCode | manual | — | 架构图/工作流图/时序图生成(精修版) |
| `debugging-hermes-tui-commands` | Hermes | manual | — | 调试 Hermes TUI 斜杠命令 |
| `dispatching-parallel-agents` |  | manual | — | 2+ 独立任务时分派并行 agent |
| `executing-plans` |  | manual | — | 按已写好的实施计划执行 |
| `finishing-a-development-branch` |  | manual | — | 开发分支完工后收尾(测试/合并/清理) |
| `github-issue-to-pr` | Hermes | manual | — | GitHub issue 转 verified PR |
| `github-repo-management` | Hermes | manual | 1次/06-22 | Git 仓库 clone/create/fork/release 管理 |
| `kanban-codex-lane` | Hermes | manual | — | Hermes Kanban worker 调 Codex CLI 跑任务 |
| `merge-reconciler` | Hermes | manual | — | agent 合并冲突的中立第三方裁决 |
| `plan` | Hermes | manual | — | 写 markdown 计划到 .hermes/plans/(不执行) |
| `plugin-creator` | Codex | manual | — | Codex 插件目录脚手架创建 |
| `plugin-creator-qwen` | QwenWorkCN | manual | — | QwenWorkCN 插件创建/定制/修改 |
| `receiving-code-review-hermes` | Hermes | manual | — | 收到 code review 反馈后的处理流程 |
| `release-orchestrator` | ZCode | manual | — | 软件发布编排(准备/灰度/就绪检查) |
| `requesting-code-review-hermes` | Hermes | manual | — | 提交前 review: 安全扫描/质量门/自动修 |
| `sdlc-review` | Hermes | manual | — | 审查 Kanban 交接和路由验证产出 |
| `session-action` | TeleAgent | manual | — | 查询其他会话运行状态, 疏通阻塞的待处理任务/权限确认 |
| `session-librarian` | Hermes | manual | — | 按 prompt 组织会话: 查找/重命名/归档/清理 |
| `session-mqtt-architecture-storytelling` | Hermes | manual | 2次/05-28 | HTTP+MQTT 系统的会话级面试笔记构建(主题设计/dispatcher/worker) |
| `skill-creator` | Codex | manual | — | Codex skill 创建指南 |
| `skill-creator-tele` | TeleAgent | manual | — | TeleAgent skill 创建指南 |
| `skill-installer` | Codex | manual | — | 从 curated 列表安装 Codex skill |
| `subagent-driven-development` |  | manual | — | 用独立子 agent 执行实施计划 |
| `systematic-debugging-hermes` | Hermes | manual | — | 4 阶段根因调试: 先理解再修 |
| `test-driven-development` |  | manual | — | TDD: 先写测试再实现功能/修 bug |
| `using-git-worktrees` |  | manual | — | 用 git worktree 隔离 feature 开发 |
| `using-superpowers` |  | manual | 4次/06-29 | 对话开始时建立 skill 发现与调用机制 |
| `verification-before-completion` |  | manual | 1次/06-11 | 声称完工前必须跑验证命令确认输出(防假报完成) |
| `weekly-review-planning` | Hermes | manual | — | 周复盘: 承诺/停滞项/下周计划 |
| `writing-plans` |  | manual | — | 有 spec/需求时写多步骤实施计划 |
| `writing-skills` |  | manual | 8次/08-10 | 创建/编辑/验证 skill 的指南 |


## 办公/集成（25 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `bilibili-summary` | QwenWorkCN | manual | — | B 站视频链接总结内容/课程 |
| `blocked-page-recovery` | Hermes | manual | — | 被墙/付费墙/WAF 拦截页面兜底恢复 |
| `box` | Hermes | manual | — | Box 云文件管理(分享/搜索/元数据) |
| `competitor-news-monitor` | Hermes | manual | — | 监控指定公司重大新闻(带引用) |
| `contract-review` | TeleAgent | manual | — | 合同审查, 注释式标注问题 |
| `doc-coauthoring` | TeleAgent | manual | — | 结构化文档协作撰写工作流 |
| `document-to-action-items` | Hermes | manual | — | 文档提取义务/截止日/任务 |
| `dws` | QwenWorkCN | manual | — | 钉钉全产品操作(表格/日历/通讯录/群聊/待办/审批/考勤/日志/文档/云盘等) |
| `email-inbox-triage` | Hermes | manual | — | 收件箱分类: 优先级排序+草拟回复 |
| `feishu-sheets-api` | Hermes | manual | 2次/06-20 | 飞书表格 API 直接创建/填充数据 |
| `find-nearby` | Hermes | manual | — | 找附近地点(餐厅/咖啡/药店等) |
| `grounded-citations` | Hermes | manual | — | 答案/文档加可验证引用来源 |
| `linear` | Hermes | manual | — | Linear 项目管理 via GraphQL |
| `meeting-action-items` | Hermes | manual | — | 会议纪要转决策/负责人/工单 |
| `memory-manager` | TeleAgent | manual | — | 长期记忆管理: 记住事实/查询过往记录 |
| `news-aggregator-skill` | TeleAgent | manual | — | 新闻聚合: 抓取/过滤/深度摘要 |
| `obsidian-interactive-learning-seminar` | Hermes | manual | 21次/06-06 | Obsidian 交互式学习研讨引导 |
| `onboarding` | TeleAgent | manual | — | 新用户初次认识引导 |
| `product-price-monitor` | Hermes | manual | — | 监控商品/机票/列表价格, 达目标价提醒 |
| `qwenwork-guidance` | QwenWorkCN | manual | — | QwenWork Connector 内置工具路由指南 |
| `scheduler` | TeleAgent | manual | — | 定时任务管理: 创建/查看/修改/删除/运行(cron+一次性) |
| `spotify` | Hermes | manual | — | Spotify 播放/搜索/队列/歌单/设备管理 |
| `webhook-subscriptions` | Hermes | manual | 1次/08-13 | Webhook 事件驱动 agent 运行 |
| `xitter` | Hermes | manual | — | X/Twitter 终端客户端交互 |
| `yuanbao` | Hermes | manual | — | 元宝群: @提及用户, 查询信息/成员 |


## 情报/职业（6 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `ai-news-digest` | Hermes | manual | 3次/08-13 | 搜索/策展最新 AI 相关新闻 |
| `career-direction-analysis` | Hermes | manual | 3次/07-27 | 职业转型方向探索分析 |
| `code-anchored-interview-coaching` | Hermes | manual | 18次/07-28 | 编程/系统设计面试辅导(代码锚定式) |
| `daily-agent-briefing` | Hermes | manual | 226次/08-14 | 中文每日简报(AI 案例+GitHub Trending+工具+天气) |
| `go-study-repo-from-codebase` | Hermes | manual | 1次/06-01 | 从现有代码库构建 Go 学习仓库 |
| `resume-tailoring` | Hermes | manual | 7次/07-28 | 按岗位定制简历 |


## 思维/讨论（14 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `agora` |  | manual | — | 讨论生态智能路由器: 分析问题→路由到合适房间 |
| `atelier` | ZCode | manual | — | 工作坊房间 — 创意突破讨论 |
| `bazaar` | ZCode | manual | — | 集市房间 — 商业与战略讨论 |
| `brainstorming` |  | manual | — | 创意工作前的必用头脑风暴 |
| `chatroom-austrian` | ClaudeCode | manual | — | 哈耶克×米塞斯×Claude 三人奥派经济学对话 |
| `clinic` | ZCode | manual | — | 诊疗室房间 — 心理韧性讨论 |
| `forge` | ZCode | manual | — | 锻造坊房间 — 工程与架构讨论 |
| `godmode` | Hermes | manual | — | LLM 越狱: Parseltongue/GODMODE/ULTRAPLINIAN |
| `grill-me` |  | manual | — | 无情拷问磨利计划/设计 |
| `grill-me-tele` | TeleAgent | manual | — | TeleAgent 版无情拷问 |
| `humanizer-hermes` | Hermes | manual | — | 文本去 AI 味, 加真实人声 |
| `ideation` | Hermes | manual | — | 用创意约束生成项目点子 |
| `oracle` | ZCode | manual | — | 神谕所房间 — 人生十字路口讨论 |
| `yao-meta-skill` | ClaudeCode | manual | — | 从工作流/提示词创建/改进/评估 skill |


## 运维/诊断（11 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `codex-session-forensics` | Hermes | manual | — | 按主题/仓库名追溯 Codex 会话对应的项目路径 |
| `codex-usage-check` | Hermes | manual | 3次/07-16 | 查 Codex CLI 本地配额/用量 |
| `hermes-s6-container-supervision` | Hermes | manual | — | s6-overlay 监督树修改/调试 |
| `hermes-session-token-accounting` | Hermes | manual | 2次/07-16 | 估算 Hermes 会话 token 用量/成本 |
| `html-architecture-explorer` | Hermes | manual | — | 构建静态 HTML 仓库解释代码库架构 |
| `inspecting-hermes-desktop-dom` | Hermes | manual | — | 读 Hermes 桌面 DOM/CSS(CDP) |
| `maintaining-hermes-agent` | Hermes | manual | 11次/08-11 | Hermes 故障排查/配置/路由/维护 |
| `mcporter` | Hermes | manual | — | mcporter CLI 列出/配置/调用 MCP server |
| `native-mcp` | Hermes | manual | 1次/08-06 | MCP 客户端: 连接 server/注册工具 |
| `network-proxy-diagnostics` | Hermes | manual | 11次/08-15 | 网络路径/代理/SSH 跳板诊断 |
| `openclaw-operations` | Hermes | manual | 6次/06-19 | OpenClaw 安装/网关/消息通道/CLI 状态运维 |


## 设备/生活（4 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `create-skill` | QwenWorkCN | manual | — | QwenWorkCN skill 创建引导 |
| `find-skills` | QwenWorkCN | manual | — | QwenWorkCN 查找可用 skill |
| `minecraft-modpack-server` | Hermes | manual | — | 开 modded Minecraft 服务器 |
| `pokemon-player` | Hermes | manual | — | 用无头模拟器+内存读取玩宝可梦 |


## Agent 元工具（11 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `claude-code` | Hermes | manual | 1次/06-29 | 委托 Claude Code CLI 做编码 |
| `codex` | Hermes | manual | 1次/06-29 | 委托 Codex CLI 做编码 |
| `full-output-enforcement` |  | manual | — | 强制 LLM 完整输出不截断 |
| `hermes-agent` | Hermes | manual | 20次/08-15 | Hermes Agent 完整使用与扩展指南 |
| `lathe` | ClaudeCode | manual | — | 按需生成任何主题的实操技术教程 |
| `media-generation` | QwenWorkCN | manual | — | 异步生成视频/音乐(QwenWorkCN) |
| `notebooklm` | ClaudeCode | manual | — | Google NotebookLM 完整 API 编程访问 |
| `openai-docs` | Codex | manual | — | 查 OpenAI 产品/API 文档(Codex 内置) |
| `qw-pages` | QwenWorkCN | manual | — | 发布静态/动态 HTML 网站(QwenWorkCN) |
| `qw-pages-supabase` | QwenWorkCN | manual | — | 为动态网站准备 Supabase 持久化存储 |
| `thoughtcode-go` | ZCode | manual | — | Go 源码↔思路码(中文自然语言投影)双向转换 |


## 其他（9 个）

| skill | 原生 Agent | level | Hermes 频率 | 功能说明 |
|---|---|---|---|---|
| `broken-skill` | ZCode | manual | — | 测试 fixture(损坏 skill 样本, 非生产) |
| `broken-yaml-skill` | ZCode | manual | — | 测试 fixture(损坏 YAML 样本, 非生产) |
| `chinese-deck-production` | Hermes | manual | 5次/08-12 | 中文 PPT 制作: 去 AI 味 + pptxgenjs + 质检 |
| `creating-learning-audio` | Hermes | manual | 4次/06-11 | 创建/重做语音学习音频/播客片段 |
| `dbs` | ClaudeCode | manual | — | dontbesilent 商业工具箱主入口, 自动路由诊断工具 |
| `dbs-action` | ClaudeCode | manual | — | dontbesilent 执行力诊断(阿德勒心理学) |
| `dbs-deconstruct` | ClaudeCode | manual | — | dontbesilent 概念拆解(维特根斯坦+奥派) |
| `dbskill-upgrade` | ClaudeCode | manual | — | 升级 dbskill 到最新版 |
| `invalid-governance-skill` | ZCode | manual | — | 测试 fixture(governance 验证样本, 非生产) |
