# Feishu DM reply should still deliver to main chat

## Trigger

Use this reference when a user reports that Hermes “replied, but under an old Feishu/Lark message” or that a Feishu private-chat reply appears to have no answer in the main conversation.

## Observed behavior

In Feishu P2P/DM, user messages created with the Feishu “reply” UI can carry fields such as `parent_id`, `root_id`, or `reply_to_message_id`. Hermes may correctly receive and process the message, but if those fields are promoted to `source.thread_id` or used as outbound `reply_to`, the bot response is sent via Feishu reply/thread semantics and renders beneath the quoted message.

This can also split session history: a session key may include the parent message id, causing `history=0` even though the user thinks they are continuing the same DM.

## Fix pattern

For Feishu DM/P2P only:

1. Keep `reply_to_message_id` and fetched `reply_to_text` for model context.
2. Do **not** promote DM `root_id` / `parent_id` to `source.thread_id`.
3. Make `_reply_anchor_for_event()` return `None` for Feishu `chat_type == "dm"`, so outbound sends are top-level in the DM.
4. Preserve real group/thread behavior: only suppress this for Feishu DM/P2P, not Telegram DM topics or Feishu group threads.
5. Add adapter tests asserting both:
   - quoted parent text is still injected (`reply_to_text` preserved), and
   - Feishu DM event source has no thread id / outbound reply anchor.

## Verification used

A targeted Feishu adapter test can cover inbound reply parsing and outbound threaded send behavior. Then run the whole Feishu gateway test file. In the session that produced this reference, the relevant full file check passed with `201 passed`.

## User-experience note

If code is fixed but the live gateway is already running, tell the user the behavior requires a gateway restart to take effect. Do not restart automatically when the user has a preference against service restarts without explicit permission.
