# Listing Tasks (scheduler list)

## Command Syntax

**Note**: Avoid using `--offline` or `--force-offline` options as they bypass the daemon service and can cause data inconsistency.

**Daemon Failure Handling**: If command fails with daemon errors (e.g., "Invalid bearer token", "Connection refused", "daemon not running"):
- Stop immediately and report the error
- DO NOT attempt to use `--offline` or `--force-offline` as a workaround

**Usage**:
```bash
teleai-agent-schedule list --json
```

**Output Format**: JSON with structure: `{"jobs": [...], "total": <number>, "limit": 100, "offset": 0}`

## Workflow

**Why stop on errors**: When a scheduler command fails, continuing can cause confusion or show incorrect data to the user. Stop immediately and report the error clearly.

1. **Execute Command** - Run `teleai-agent-schedule list --json`
   - **Success**: Proceed to step 2
   - **Failure**: Stop and show error: `❌ 无法获取定时任务列表\n\n请检查teleai-agent-schedule是否正常运行。\n\n错误详情：[error output]`

2. **Parse JSON** - Extract `jobs` array and `total` count
   - ⚠️ **Important**: `total` is the actual task count, `limit` is query page size (usually 100)

3. **Identify Filters** (Optional) - Analyze user input for filter conditions
   - **Status**: "启用/开启" → `enabled === true`, "禁用/关闭" → `enabled === false`
   - **Type**: "周期/cron" → `type === 'cron'`, "一次性/once" → `type === 'once'`
   - **Name**: "包含xxx" → `name.includes(keyword)`
   - **Content**: "内容包含xxx" → `prompt.includes(keyword)`
   - Use AND logic for multiple conditions

4. **Apply Filters** - Filter `jobs` array based on identified conditions

5. **Format & Display** - Convert to user-friendly table format

   **Field Mapping Rules**:
   - `name` → `名称` (task identifier)
   - `expr`/`run-at` → `执行时间`
     - Cron: Convert expr "0 9 * * *" → "每天 09:00", "0 14 * * 1" → "每周一 14:00"
     - Once: Convert run-at "2026-03-20T00:00:00Z" → "2026-03-20 08:00" (UTC to local time)
   - `prompt` → `内容` (truncate to 16 chars + "...")
   - `enabled` → `状态` (✅ 已启用 / ❌ 已禁用)

   **Display Format (With Tasks)**:
   ```markdown
   ✅ 定时任务查询完成！共查询到 N 个定时任务

   🔍 过滤条件：[条件名称] [if applicable]

   | 名称 | 执行时间 | 内容 | 状态 |
   |:-----|:---------|:-----|:-----|
   | 每日AI进展 | 每天 09:00 | 简单总结一下大模型领域最新动向和... | ✅ 已启用 |
   | 房价走势 | 2026-03-20 15:00 | 北京今年房价走势 | ❌ 已禁用 |
   ```

   **Display Format (No Tasks)**:
   ```markdown
   ✅ 定时任务查询完成！未找到符合条件的定时任务
   ```


## JSON Response Format

**Response Structure**:
```json
{
  "jobs": [...],     // Array of task objects
  "total": 1,        // Total number of tasks (actual count)
  "limit": 100,      // Query page size (NOT max task limit)
  "offset": 0        // Pagination offset
}
```

**Task Object Example**:
```json
{
  "id": "job_id",
  "name": "定时测试任务",
  "type": "cron",           // "cron" or "once"
  "expr": "0 9 * * *",      // Cron expression (for cron type)
  "run_at": null,           // ISO timestamp (for once type)
  "timezone": "Asia/Shanghai",
  "prompt": "测试任务",
  "enabled": false,         // true = enabled, false = disabled
  "last_run_at": "2026-03-11T07:38:00.033Z",
  "last_status": "failed"   // "success" or "error"
}
```

## Example

**User Input**: "查看已启用的任务"

**Workflow**:
1. Execute `teleai-agent-schedule list --json`
2. Parse JSON
3. Identify filter: "已启用" → `enabled === true`
4. Apply filter
5. Display result

**Output**:
```markdown
✅ 定时任务查询完成！共查询到1个已启用的定时任务

🔍 过滤条件：已启用

| 名称 | 执行时间 | 内容 | 状态 |
|------|----------|------|------|
| 每日新闻收集 | 每天 09:00 | 收集昨天AI行业热点新闻 | ✅ 已启用 |
```


