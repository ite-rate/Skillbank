# Redis engineering scenario drills

Session-derived pattern for the user's Redis learning under:
`/Users/ss/Documents/main_store/interactive-system-design-vault/Projects/redis-engineering-scenarios`

## Trigger
Use when the user wants Redis interview/system-design learning to move beyond concept notes into practical engineering recall, especially with 牛客/面经/NeetCode-style high-frequency questions.

## Core idea
Do not organize Redis as command/data-structure trivia first. Convert high-frequency interview topics into engineering scenario cards:

```text
business pressure -> Redis state role -> key/value/TTL -> read path -> write path -> failure modes -> 30s oral interview answer
```

The user should answer first. Then correct and persist.

## Required card shape
Each scenario card should force:
- Engineering problem: what breaks without Redis?
- Redis role: current state, derived cache, counter/window, set relation, sorted relation, stream/task, lock/lease, dedup record
- Key design: concrete key names, value fields, TTL, ownership
- Data structure: string/hash/set/zset/stream/bitmap/hll/lua, with why
- Read path and write path
- Failure modes: expiration, concurrent rebuild, duplicate message, DB pressure, Redis unavailable, DB/Redis inconsistency
- 30-second oral answer

## Example scenario set
Seed or maintain cards such as:
- device online state / massive reconnect
- session runtime progress
- MQTT/message deduplication
- Redis distributed lock design
- cache breakdown / penetration / avalanche
- MySQL-Redis consistency
- rate limiting window
- seckill stock pre-deduct
- leaderboard ZSet
- hot key governance
- delayed task: ZSet vs Stream
- WebSocket connection map
- payment callback idempotency

## Workflow rule
When the user says to start a scenario, do **not** provide the full answer first. Ask the scenario questions and wait for the user's closed-book attempt. Correct only after their attempt, then write the stable correction back to the scenario note.

## Interview-question integration
Do not copy external question-bank text. Instead map common themes to scenarios:
- “Redis 分布式锁怎么设计” -> cache rebuild mutex / task mutual exclusion / seckill guard
- “缓存击穿/穿透/雪崩” -> product/detail cache or activity page cache failure modes
- “Redis 和 MySQL 一致性” -> DB-as-source write path and cache invalidation
- “限流” -> protected resource window design
- “排行榜” -> ZSet score/query/update/archive design
