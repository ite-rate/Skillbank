# Cron Job max_iterations_reached Error Pattern

## Symptom

Cron job fails with `RuntimeError: <agent output content>` where the error message IS the agent's generated content (e.g., a daily briefing, report, or analysis).

Example from logs:
```
2026-06-19 07:48:54,923 ERROR cron.scheduler: Job 'daily-0740-news-weather-trending' failed: 
RuntimeError: 2026年6月19日 Agent 早报

**今日最值得关注的 1-2 句话：** ...
```

## Root Cause

The agent generated content successfully but hit the **iteration limit** before marking the task as complete.

From `cron/scheduler.py`:
```python
if result.get("failed") is True or result.get("completed") is False:
    _err_text = (
        result.get("error")
        or (result.get("final_response") or "").strip()
        or "agent reported failure"
    )
    raise RuntimeError(_err_text)
```

The `final_response` (the complete generated content) is treated as error text because `completed=False` due to `max_iterations_reached`.

Log evidence:
```
agent.conversation_loop: Turn ended: reason=max_iterations_reached(90/90) 
model=kimi-k2.6 api_calls=90/90 budget=90/90 tool_turns=90 
last_msg_role=assistant response_len=5712
```

## Diagnostic Steps

1. Check cron job logs in `~/.hermes/logs/agent.log`:
   ```bash
   grep -n "max_iterations_reached\|RuntimeError.*cron" ~/.hermes/logs/agent.log
   ```

2. Look for the `Turn ended` line to confirm iteration exhaustion:
   ```bash
   grep "Turn ended: reason=max_iterations_reached" ~/.hermes/logs/agent.log
   ```

3. Check if tool calls are consuming iterations:
   ```bash
   grep "api_calls=" ~/.hermes/logs/agent.log | tail -20
   ```

## Solutions

### Option 1: Reduce Tool Usage in the Skill/Prompt

The agent is making too many tool calls (browser_navigate, terminal, web_search, etc.) within the iteration budget. Optimize the skill to:
- Batch web requests
- Reduce redundant browser snapshots
- Use fewer terminal commands
- Cache results between calls

### Option 2: Increase Iteration Limit (if configurable)

Check if Hermes config allows increasing `max_iterations` for cron jobs. As of current version, this may require source modification.

### Option 3: Simplify the Task

Break the cron job into multiple smaller jobs:
- One job for weather
- One job for news
- One job for GitHub trending

Each with simpler prompts that complete within 90 iterations.

### Option 4: Use a More Efficient Model

Some models (especially reasoning models) use more iterations per tool call. Switching to a faster, non-reasoning model may help.

## Prevention

When writing cron job skills/prompts:
1. Count expected tool calls (each tool call + LLM response = 2 iterations minimum)
2. Keep total expected iterations under 80 (leave 10 buffer)
3. Use `no_agent=True` for script-only cron jobs (no LLM iterations consumed)
4. Test the prompt manually first: run it in a regular session and count iterations

## Related

- `cron/scheduler.py` line ~1866: `raise RuntimeError(_err_text)`
- `agent/conversation_loop.py`: iteration budget enforcement
- Hermes default cron iteration budget: 90
