# Redis Engineering Scenario + Keyword Recall Drills

Use this reference when the user is preparing for Redis/backend/system-design interviews and says they can understand answers after correction but cannot quickly recall the key points in the interview.

## Core diagnosis

The problem is often not lack of Redis knowledge, but lack of a first-reaction trigger map:

```text
question -> 3-second keywords -> 30-second oral answer -> follow-up depth
```

Do not start with long explanations. Train recall first.

## Two-round training loop

1. Keyword round
   - Ask one interview question.
   - User may answer only 5 keywords, no explanation.
   - Correct missing/overfit keywords briefly.
2. Oral-answer round
   - User expands the corrected keywords into a 20-30 second answer.
   - Correct only the highest-impact gap.
   - Provide a polished version only after the user attempts.

Example prompt:

```text
题目：缓存击穿怎么解决？
只答 5 个关键词，不要展开。
```

Good corrected keywords:

```text
1. 热点 key
2. 互斥锁 / 分布式锁
3. 逻辑过期
4. 缓存预热
5. 保护 MySQL / 降级
```

## Backend universal recall frame

For any backend/system design question, silently check:

```text
状态：系统里要表达什么状态？
路径：请求/消息怎么流动？
并发：多请求同时来会发生什么？
失败：中间某一步失败怎么办？
兜底：最终靠什么保证正确？
```

## Redis-specific recall frame

For Redis questions, force the first reaction through:

```text
角色：缓存 / 当前态 / 计数器 / 去重 / 锁 / 队列 / 排行榜 / 限流？
key：具体 key 是什么？
TTL：活多久，为什么？
并发：击穿、重复消费、超卖、锁竞争？
一致性：谁是事实源，Redis 是不是派生状态？
降级：Redis 挂了/慢了怎么办？
```

## Engineering-scenario card shape

When persisting Redis drills into the user's interactive-system-design vault, prefer project:

```text
/Users/ss/Documents/main_store/interactive-system-design-vault/Projects/redis-engineering-scenarios
```

Each scenario should be a card with:

```text
工程问题
Redis 角色
key/value/TTL
读路径
写路径
并发风险
失败场景
MySQL/DB 事实源边界
30 秒口语版
追问关键词
```

The learner should answer first. Do not pre-fill polished answers unless asked.

## High-frequency Redis trigger pairs

```text
缓存击穿：热点 key、互斥锁、逻辑过期、预热、保护 DB
缓存穿透：不存在 key、参数校验、布隆过滤器、空值缓存、限流防刷
缓存雪崩：大量 key 同时失效、TTL 随机、预热、限流降级、多级缓存/高可用
分布式锁：SET NX PX、唯一 value、TTL/续期、Lua 删除、幂等优先
双写一致性：MySQL 事实源、cache-aside、更新 DB 后删缓存、失败窗口、最终一致/补偿
设备在线态：Hash/String+TTL、last_heartbeat、状态防抖、MySQL 状态事件、批量重连退避
消息去重：SET NX EX、messageId、业务唯一键、状态类覆盖、DB 唯一约束兜底
WebSocket 推送失败：业务事实已落库、通知副作用、eventId 去重、前端重连拉状态、outbox 可选
排行榜：ZSet、member=用户/设备、score=分数/次数、ZINCRBY、ZREVRANGE/ZREVRANK、定期落库/事实源
接口限流：INCR、EXPIRE、固定窗口/滑动窗口、Lua 原子化、按 userId/IP/deviceId 维度、超过阈值降级
Cluster 分片：16384 slot、CRC16(key)%16384、slot->node 映射表、MOVED 重定向、扩容只迁移部分 slot
本地缓存+Redis：二级缓存、本地最快、Redis 共享、失效通知/短 TTL/版本号、缓解热点读但增加一致性复杂度
```

## Depth calibration notes

When the user reacts with “这么简单?” after a Redis mechanism answer, do not overcomplicate the primitive. Explain that Redis operations are often simple, and the interview value is in the engineering boundary:

```text
不是命令复杂，而是要说清楚：保护谁、Key 怎么设计、TTL 怎么选、并发窗口在哪里、失败后谁兜底。
```

For distributed-lock answers, require the layered version:
- Mechanism: `SET key value NX PX ttl`
- Safety: `value=requestId/uuid` identifies lock owner
- Release: Lua check value then `DEL`, never blind delete
- Boundary: lock only narrows concurrent critical section; MySQL unique constraints / idempotency still guard correctness
- Extension: watchdog/续期 only for long business logic; cache rebuild should preferably keep critical section short

For cache breakdown/penetration/avalanche, separate primary treatment from auxiliary measures:
- 击穿 primary: mutex or logical expiration for hot key rebuild
- 穿透 primary: parameter validation + Bloom filter/empty cache for nonexistent keys
- 雪崩 primary: randomized TTL + staged preheat + degradation/rate limiting
- “预热/降级/限流” are often cross-cutting support measures; don’t present them as the only core cure for every cache problem.
- Local cache + Redis is a hotspot-read pressure optimization, not the primary solution to penetration/avalanche. If the user frames it that way, validate the pressure-relief intuition but correct the category.

For Redis Cluster slot questions, use the algorithm contrast instead of only diagrams:
- Naive route: `node = hash(key) % nodeCount`; when nodeCount changes, the formula changes and many keys move.
- Cluster route: `slot = CRC16(key) % 16384`; this stays fixed regardless of node count.
- Then `slot -> node` is a maintained mapping table; expansion changes only part of this second-layer mapping.
- Explain the value as “fixed virtual shards decouple keys from physical nodes,” not “saving hash computation.”
- If the user asks “为什么有用/对比原来和现在,” explicitly compare the two formulas side-by-side: `% nodeCount` changes with physical nodes; `% 16384` does not.
- If the user says “这里肯定有个算法/常识,” name the class: sharding/routing algorithm, similar in spirit to consistent hashing and virtual partitions.

For AOF persistence questions, keep “recording” and “fsync/flushing” separate:
- If AOF is enabled, Redis records/appends every executed write command to the AOF path/buffer.
- `appendfsync always/everysec/no` controls when those appended writes are forced to disk, not whether they are recorded.
- `always`: fsync every write; safest and slowest.
- `everysec`: fsync about once per second; production default/common tradeoff.
- `no`: Redis does not actively fsync; writes may sit in the OS page cache and flush on the OS schedule. Do not say “no means never writes/never records.”

## Style rules for this user

- Keep the drill fast. The user wants emergency oral interview answers and recall training, not long lectures.
- If the user only gives rough keywords, first validate what is right, then add missing trigger words.
- When the user says “不会/卡住”, give one compact explanation and a memorisable oral version.
- Prefer Chinese oral wording that can be spoken directly in interviews.
