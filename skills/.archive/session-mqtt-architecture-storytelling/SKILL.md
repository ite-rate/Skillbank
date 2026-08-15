---
name: session-mqtt-architecture-storytelling
description: Build and maintain session-centric interview notes for systems that combine HTTP/Gin, MQTT, devmon, Task normalization, dispatchers, workers, and topic design. Use when the user wants a non-ambiguous architecture story that evolves from single-service MQTT handling to a split devmon/business-service design.
level: manual
native_agent: Hermes
---

# Session-centric MQTT architecture storytelling

Use this skill when the user is refining interview-prep notes or architecture explanations for a system with:
- HTTP + Gin for management/query/result endpoints
- MQTT for real-time device/control traffic
- optional devmon as the device-control plane
- a unified Task model
- dispatcher/worker async processing
- session as the main business timeline

## Core idea
Tell the story in layers:
1. **Ingress layer**: Gin HTTP handlers or MQTT callbacks
2. **Normalization layer**: convert raw input into a unified `Task`
3. **Routing layer**: dispatcher maps `Task` to concrete handlers/queues
4. **Execution layer**: workers do DB/Redis/ACK/side effects
5. **Boundary split**: devmon owns device control; business service owns session/event/result/statistics

## Canonical clarification rules
When refining the story, keep these distinctions strict:
- **Gin** is for request/response management-plane APIs, not the real-time device stream.
- **MQTT** is for device/control/event transport.
- **devmon** is the device-control plane and may transform raw telemetry into business events.
- **Task** is the common internal message shape, not the transport itself.
- **dispatcher** routes by business meaning, not by protocol identity.
- **workers** perform synchronous or asynchronous side effects.

## Topic design rules
To avoid ambiguity:
- Do **not** mix control-plane and business-plane semantics in the same topic name.
- Prefer:
  - `deviceId` for control-plane topics (heartbeat/state/ack/telemetry)
  - `sessionId` for business-plane topics (event/result/state/ack)
- Do not use a generic `.../event` topic for device-side traffic if it can be confused with business events.
- If device data needs to become a business event, let devmon translate raw telemetry into a business topic.

## Required message taxonomy
Maintain a crisp taxonomy:
- **Device/control plane**: heartbeat, state, ack, telemetry, cmd/config/control
- **Business plane**: session init, task_complete, result_submit, hint_shown, error_occurred, training state
- **Management plane**: login, create room/session, query, final result submission

## Recommended narrative structure
When rewriting docs or answering the user, use this order:
1. Why the system split happened
2. What Gin actually does
3. What MQTT/devmon actually do
4. Which messages belong to which plane
5. How raw input becomes Task
6. How dispatcher/worker consume Task
7. What guarantees are used: idempotency, ACK, timeout, retry, ordering, state layering
8. Why the design is beneficial

## Good phrasing patterns
- “Gin is the management-plane entry point.”
- “MQTT carries the device/control stream.”
- “devmon converts raw telemetry into business events.”
- “The business service subscribes to its own business topics and consumes normalized Tasks.”
- “`topic` decides where the message goes; `Task` decides what the message means.”
- “`session_id` is the business timeline; `device_id` is the control-plane identity.”

## Live interview emergency mode
When the user is in interview-prep mode and sends a short topic/question, prioritize a fast Chinese oral answer rather than long theory:
1. Give a directly speakable 20–40 second answer.
2. Add 2–3 engineering keywords only if useful.
3. Ground it in the VR/MQTT project or the target IoT/vending-machine context.
4. Offer追问兜底 only after the main answer.

When the user asks to “把这次回答也放到 10-面试回顾”, actually create/update Markdown under `/Users/ss/Documents/main_store/面试/10-面试回顾-2026-05-26/` and update that folder’s `INDEX.md`; do not only say it was saved.

Session-specific reference: `references/iot-vending-interview-followups.md` captures oral answers for reconnect storms, sessionId validation pressure, MQTT auth, service peaks/valleys, and vending-machine follow-ups.

## Common pitfalls to avoid
- Saying Gin handles the realtime stream.
- Saying device-side events and business events share one topic namespace.
- Letting `event` mean two different things in two different places.
- Making `deviceId` and `sessionId` compete as if only one can exist.
- Describing devmon ↔ business-service communication as optional when it is required by the split.
- Forgetting that query/result submission are management-plane / finalization APIs, not live MQTT events.

## Verification checklist
Before finalizing notes, check:
- Is each message clearly assigned to exactly one plane?
- Are control-plane topics separate from business-plane topics?
- Does every path end in a unified Task model?
- Is dispatch described by business meaning, not transport type?
- Are ACK, timeout, retry, idempotency, and ordering explicitly mentioned?
- Is the role of Gin limited to management-plane APIs?

## Example simplified storyline
> We first used a single business service to receive MQTT and run the end-to-end flow. As the device-control side grew, we split out devmon to own the control plane. Gin stayed as the HTTP management layer for login, session creation, final result submission, and queries. All raw inputs are normalized into a Task model, then routed by dispatcher to workers. Topic names are kept unambiguous: device/control-plane traffic uses `deviceId`, business-plane traffic uses `sessionId`, and devmon translates raw telemetry into business events when needed.
