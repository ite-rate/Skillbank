# IoT / vending-machine interview follow-ups

Session learning: user needed rapid oral interview answers around MQTT/IoT edge cases and wanted the answer added under the `10-面试回顾` Obsidian review set.

## Persistent workflow rule
When the user says “把这次回答也放到 10-面试回顾”, actually write a new Markdown note under:

`/Users/ss/Documents/main_store/面试/10-面试回顾-2026-05-26/`

Then update:

`/Users/ss/Documents/main_store/面试/10-面试回顾-2026-05-26/INDEX.md`

Do not merely claim it was saved.

## Oral-answer style required
For live interview emergencies, answer in Chinese as a 20–40 second spoken answer:

1. Direct answer first
2. 2–3 keywords / engineering levers
3. Project or IoT grounding
4. Optional one-sentence追问兜底

Avoid long theory unless asked.

## Follow-up topics that emerged

### 1. Massive device reconnect storm pressure on MQTT
Core answer:
- Yes, reconnect storms can pressure broker, auth service, and subscribers.
- Mitigate with exponential backoff, jitter, connection-rate limits, broker clustering, message priority, heartbeat degradation/merge.
- Distinguish business peak from reconnect peak.

Oral version:
> 会有这个风险，尤其是网络恢复或设备批量重启时。我的思路是设备端不要固定频率同时重连，而是做指数退避加随机抖动；broker 侧限制连接速率和最大连接数；后端侧对心跳、状态类消息做降级和合并，result、支付、出货这类关键事件优先处理。这样系统是逐步恢复，而不是所有设备一起打进来。

### 2. Reconnect sessionId validation pressure on DB
Core answer:
- DB is the source of truth, but should not be the first hop for every reconnect.
- Hot path: Redis runtime state (`device:current_session:{deviceId}`, `session:runtime:{sessionId}`), recovery window, last heartbeat.
- Fallback to DB only on cache miss, conflict, suspicious sessionId, ownership validation, or critical state.

Oral version:
> 不应该每次重连都直接查 DB。DB 是 session 事实源，但热路径先看 Redis 里的设备当前 session、最后心跳和恢复窗口。只有 Redis 缺失、状态冲突、sessionId 可疑，或者需要确认 deviceId 和 session 归属时，才回源查 DB。这样 Redis 扛重连热路径，DB 做兜底校验。

### 3. MQTT authentication for IoT devices
Core answer:
- Per-device `deviceId` + per-device secret/token/cert.
- Provisioned at factory/install time, transmitted over TLS.
- Server/broker validates credential binding and enforces topic ACL.
- Support revocation and rotation.

Oral version:
> 设备连接 MQTT 时一般会有唯一 deviceId，再配一个装机或出厂时写入的独立密钥、token 或证书。连接 broker 时通过 username/password、token 或 TLS 双向证书认证。服务端不会只相信设备传的 deviceId，而是校验 deviceId 和凭证是否匹配，并限制它只能发布订阅自己权限范围内的 topic。密钥还要支持吊销和轮换。

### 4. Service peak/valley answer
For VR project:
- Not e-commerce-level spikes, but daytime institution usage and batch reconnects create local peaks.
- Night/off-work periods are lower traffic.
- Separate business peaks from technical reconnect peaks.

For vending-machine company:
- Peaks around commute/lunch/evening商圈; low at night except heartbeat/reconciliation/remote config.
- Critical events: payment, dispense result, inventory deduction; low-value high-frequency events: heartbeat/status.

Oral version:
> 我会把波峰分成业务波峰和技术波峰。业务上，比如无人售货机会在早高峰、午饭、下班、商圈夜间有交易和库存变更峰值；技术上，网络恢复、设备批量启动会带来 MQTT 重连和心跳峰值。心跳、状态这类高频低价值消息可以合并降级；支付、出货、库存扣减这类关键事件必须优先处理、可靠落库和幂等。

## Additional likely IoT/vending questions
- 支付成功但出货失败：订单状态机 `created -> paid -> dispensing -> success/failed/refunding`；支付成功不等于交易完成；失败触发退款/人工补偿；orderId/eventId 幂等。
- 消息重复上报：MQTT QoS 1 至少一次，业务侧幂等；messageId 或 `orderId + eventType`；Redis 短期去重 + DB 唯一索引兜底。
- 在线状态：heartbeat + Redis TTL + last_heartbeat + LWT；TTL 为心跳间隔 2–3 倍并加防抖。
- 库存准确性：DB 库存流水是事实源；设备上报用于校验/修正；不应无脑覆盖 DB。
- 远程控制：commandId + command 状态机 pending/received/success/failed；设备端命令幂等，避免重复执行危险动作。
