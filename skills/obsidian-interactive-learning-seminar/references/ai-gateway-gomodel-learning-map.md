# GoModel AI Gateway — 学习主线

用 GoModel 源码做锚点的 9 模块深度学习路径（含认证体系 + 可观测性）。

## 模块地图

0. 认证体系总览（AuthMiddleware 三态 + AuthKey Service snapshot + user_path 双路径注入）
1. 请求生命周期与核心翻译层
2. 模型发现、user_path 与信任边界
3. 两层缓存（精确 + 语义 + 流式录播回放）
4. Guardrail（system_prompt + LLM-based altering + Pipeline 并行/串行）
5. Fallback + 断路器（三态机 + 重试 + 回退链）
6. Workflow 策略引擎（Scope 匹配 → 编译 → Policy+Pipeline → GuardrailsHash）
7. 完整链路函数级标注
8. 可观测性三线分离（Audit async + Usage async + Budget sync + Live SSE）

## 核心问题库

每题都锚定具体源码文件。

**模块 1：**
- 为什么 Anthropic /v1/messages 必须先翻译成 core.ChatRequest 再派发？（internal/anthropicapi/）
- 入门前 5 步为什么缓存必须在最后？（guardrail 改写请求 → 缓存 key 必须等价于最终 prompt）
- 流式翻译 finish_reason 的时序陷阱（提前填入 → SDK break → 后续 chunk 全部丢失）

**模块 2：**
- 模型清单三层 merge 冲突怎么解决？（pricing override 优先级最高）
- user_path 信任边界：为什么 GoModel 不验证 user_path？（Auth Proxy 负责注入）
- 同 model name 多 provider 的注册顺序陷阱（先注册抢走）

**模块 3：**
- 精确缓存 key 不含 guardrailsHash → 靠 workflow hash 间接隔离
- 语义缓存只看最后 user message → 长对话误匹配 → MaxConversationMessages 跳过
- 换 embedding model 旧向量变孤儿 → embedderIdentity 打入 hash 隔离
- 流式录播回放：首次实流异步记录 → 后续 Redis 整段 SSE 推送
- 降级链：精确 → 语义 → 直连。启动时 Redis/向量库连不上直接 crash

**模块 4：**
- system_prompt 零延迟无注入风险 / LLM altering 强但有注入悖论
- Pipeline 同 order 并联互斥覆盖 / 不同 order 串联组合
- LLM guardrail 成本陷阱：每条约 4000 token × N 条 = O(n) 延迟

**模块 5：**
- 断路器三态：Closed → Open（5 次失败）→ Half-Open（30s）→ Closed（2 次成功）
- 重试和断路器独立：retry 处理临时抖，breaker 处理 provider 挂
- 429 在 closed 不计 breaker / half-open 计入 → 限流不跳闸
- fallback 三种模式：off / manual / auto（benchmark top 5）
- 走过 fallback 的响应不写缓存

**模块 6：**
- Scope 三维匹配：user_path 祖先链 → provider_model → provider → global
- 编译：Payload → Policy(Features+GuardrailsHash) + Pipeline
- Feature caps：系统级上限强制关子级功能
- GuardrailsHash 打入语义缓存 key 隔离 / WorkflowHash 仅版本追踪

**模块 7：完整链路函数级标引**
- 1. Auth：master key → 托管 API Key → user_path 注入（覆盖客户端 header）
- 2. Server Handler：prepareTranslatedRequest() 一条链完成 Model Resolution + Authorization + Workflow Match + Guardrail Patch
- 3. Cache Lookup：handleWithCache() → TryHit（精确）→ semantic.Handle()（语义）→ dispatch
- 4. Provider 调用：dispatchChatCompletion() → enforceBudget() → ExecuteChatCompletion()
- 5. llmclient：beginRequest 查断路器 → HTTP + 重试 → recordCircuitBreakerCompletion
- 6. Fallback：executeWithFallbackResponse() → ShouldAttemptFallback(422 不触发) → 逐个试
- 7. 返回：audit 记录 + usage 记录 + 异步写缓存（走过 fallback 不写缓存）

**模块 0：认证体系总览**
- Middleware 顺序不可变：RequestSnapshotCapture → AuthMiddleware（先捕获再覆盖）
- AuthMiddleware 三态：无 key（全放）→ master key（constantTimeCompare）→ 托管 API Key（内存查表）
- AuthKey Service 也是 snapshot 模式（DB → 内存），和 Workflow 同构
- 区别：AuthKey 用 mutex+RWLock（有增量 Create/Deactivate），Workflow 用 atomic.Value
- 两条 user_path 注入路径：外部 Auth Proxy（header）vs 托管 API Key（UserPath 字段覆盖 header）
- Token 结构：sk_gom_ + base64(32 bytes) → 只存 sha256 hash
- Admin API：GET/POST /admin/auth-keys、POST /admin/auth-keys/:id/deactivate

**模块 8：可观测性三线分离**
- Audit（异步）：middleware 创建 LogEntry → handler 跑完补全 metadata → channel → 批量写 DB
- Usage（异步）：非流式从 response JSON 提取 token 计数 → 查 pricing 算成本 → channel → 批量写 DB
- Budget（同步）：当场拦截（Check → SumUsageCost → 超了 429 + Retry-After），匹配走祖先链
- SSE 观察不阻塞流：ObservedSSEStream 字节原样转发，侧路解析 JSON fan out 给 observer
- StreamUsageObserver：累积最后一个含 usage 的 SSE chunk → 流关闭时 Write
- StreamLogObserver：从 SSE 事件重建 response body 和元数据
- Live Events：audit/usage 各自推事件到 dashboard（started/updated/completed/failed/flushed/removed）
- 三条线通过 Workflow.Features.{Audit,Usage,Budget} 独立开关，系统级 cap 可强制关

**关键纠偏记录（历次 session）：**
- Workflow 编译是后台 Refresh 做的，不是请求时做的。请求时 matchCompiled() 从内存 snapshot 读现货
- 精确缓存不含 GuardrailsHash（key 是 workflow 结构字段 Mode/ProviderType/QualifiedModel）
- 语义缓存含 GuardrailsHash（paramsHash 显式写入）
- WorkflowHash 仅用于版本追踪和 admin 展示，不直接参与缓存 key
- user_path 来源：托管 API Key 的 UserPath 字段 → auth 中间件注入 header → 覆盖客户端自报值
- 或外部 Auth Proxy（Kong/Nginx）解析 JWT → 设 X-GoModel-User-Path header

## 用户校正记录

- "太浅了 直接进入核心" → 跳过热身，直接问架构设计问题
- "格式不对 重新返回 看着很难受" → Feishu 不用表格/代码块，平文本 + 短段落
- "你刚才可没说...在对比源码确定一下" → 所有声称必须读源码验证
- "我没法看啊" → 长内容写 vault，Feishu 只留精短互动
- write_file 不可靠 → terminal cat heredoc 写文件
- 确认用户看的哪个 vault 再写文件（多 vault 环境）
