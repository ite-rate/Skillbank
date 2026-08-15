# Deleting Tasks

## Command Syntax

**Note**: Avoid using `--offline` or `--force-offline` options as they bypass the daemon service and can cause data inconsistency. Only use standard command options as shown in this document.

**Daemon Failure Handling**: If command fails with daemon errors (e.g., "Invalid bearer token", "Connection refused", "daemon not running"):
- Stop immediately and report the error
- DO NOT attempt to use `--offline` or `--force-offline` as a workaround

```bash
teleai-agent-schedule delete <task-id>
```

**Parameters**:
- `task-id`: The ID of the task to delete

## Workflow

**Why stop on errors**: When a scheduler command fails, continuing can cause confusion or show incorrect data to the user. Stop immediately and report the error clearly.

1. **Get Task List**
   ```bash
   teleai-agent-schedule list --json
   ```
   **⚠️ Check Result**: Success → continue, Failure → STOP

2. **Identify Target Task**
   - Match from list using: task ID, name, time, content, or combination
   - **Multiple matches**: Use question tool for disambiguation
   - **No matches**: Show task not found error message, STOP
     ```
     ❌ 未找到您要删除的任务

     请尝试：
     1. 使用"查看任务列表"查看所有任务
     2. 使用更具体的关键词
     3. 使用任务的确切名称或ID
     ```

3. **Show Task Card**

   ```markdown
   ✅ 为您找到了您要删除的任务：

   | 📋 定时任务详情 |
   |:---|
   | **任务名称**：<task name> |
   | **任务要求**：<task prompt> |
   | **执行时间**：<time> |
   | **启用状态**：<status> |
   ```

4. **Confirm with User** ⚠️ **REQUIRED STEP**

   **⚠️ IMPORTANT**: Always use question tool with deletion warning BEFORE deleting to prevent accidental data loss.

   **Confirmation Pattern**
   ```
   确定要永久删除任务'<task-name>'吗？此操作不可恢复。
   ```
   - **Do not execute delete until user confirms**

5. **Execute Delete**

   **Only AFTER user confirmation**, execute:
   ```bash
   teleai-agent-schedule delete <task-id>
   ```

   **⚠️ Check Result**: Success → show success, Failure → STOP and show error

6. **Display Result**
   - **Success**: Show "✅ 任务已删除"

## Examples

### Example 1: Delete by Name

**User**: "删除日报任务"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "日报任务" → task_001 "daily-news"

# Step 3: Show task card
✅ 为您找到了您要删除的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：日报汇总 |
| **任务要求**：收集今天科技行业的热点新闻并整理... |
| **执行频率**：每天09:00 |
| **启用状态**：✅ 开启 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要永久删除任务'日报汇总'吗？此操作不可恢复。"
User: "确定删除"

# Step 5: Execute
teleai-agent-schedule delete task_001

# Step 6: Display result
✅ 任务已删除
```

### Example 2: Delete by Time

**User**: "把9点的那个提醒删了"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "9点" → task_002 "mail-reminder"

# Step 3: Show task card
✅ 为您找到了您要删除的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：邮件提醒 |
| **任务要求**：邮件查看提醒 |
| **执行时间**：每天09:00 |
| **启用状态**：❌ 停用 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要永久删除任务'邮件提醒'吗？此操作不可恢复。"
User: "确定删除"

# Step 5: Execute
teleai-agent-schedule delete task_002

# Step 6: Display result
✅ 任务已删除
```

### Example 3: User Cancels Deletion

**User**: "这个任务不要了"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "这个任务" → task_003 "backup-check"

# Step 3: Show task card
✅ 为您找到了您要删除的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：备份检查 |
| **任务要求**：检查最近一次备份是否成功 |
| **执行时间**：每隔6小时 |
| **启用状态**：✅ 开启 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要永久删除任务'备份检查'吗？此操作不可恢复。"
User: "取消"

# Step 5: User cancelled, do NOT execute
⚠️ 用户取消删除，操作已中止
```

### Example 4: Task Not Found

**User**: "删除测试任务"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "测试" → No matches found

# Step 3: Show error message
❌ 未找到您要删除的任务

请尝试：
1. 使用"查看任务列表"查看所有任务
2. 使用更具体的关键词
3. 使用任务的确切名称或ID

⚠️ 操作已中止
```

## Error Handling

### teleai-agent-schedule list Fails

```
❌ 无法获取任务列表

请检查teleai-agent-schedule是否正常运行。

错误详情：[error output]
```

### Task Not Found

```
❌ 未找到您要删除的任务

请尝试：
1. 使用"查看任务列表"查看所有任务
2. 使用更具体的关键词
3. 使用任务的确切名称或ID
```

### Delete Command Fails

```
❌ 删除失败

任务ID：<task-id>

可能原因：
• 任务不存在
• 任务已被删除
• 权限不足

错误详情：[error output]
```