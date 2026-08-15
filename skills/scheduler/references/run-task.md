# Running Tasks

## Command Syntax

**Note**: Avoid using `--offline` or `--force-offline` options as they bypass the daemon service and can cause data inconsistency. Only use standard command options as shown in this document.

**Daemon Failure Handling**: If command fails with daemon errors (e.g., "Invalid bearer token", "Connection refused", "daemon not running"):
- Stop immediately and report the error
- DO NOT attempt to use `--offline` or `--force-offline` as a workaround

```bash
teleai-agent-schedule run <task-id>
```

**Parameters**:
- `task-id`: The ID of the task to run

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
     ❌ 未找到您要运行的任务

     请尝试：
     1. 使用"查看任务列表"查看所有任务
     2. 使用更具体的关键词
     3. 使用任务的确切名称或ID
     ```

3. **Show Task Card**

   ```markdown
   ✅ 为您找到了您要运行的任务：

   | 📋 定时任务详情 |
   |:---|
   | **任务名称**：<task name> |
   | **任务要求**：<task prompt> |
   | **执行时间**：<time> |
   | **启用状态**：<status> |
   ```

4. **Confirm with User** ⚠️ **REQUIRED STEP**

   **⚠️ IMPORTANT**: Always use question tool to get user confirmation BEFORE running to ensure user intends to execute the task.

   **Confirmation Pattern**
   ```
   确定要立即运行任务'<task-name>'吗？
   ```
   - **Do not execute run until user confirms**

5. **Execute Run**

   **Only AFTER user confirmation**, execute:
   ```bash
   teleai-agent-schedule run <task-id>
   ```

   **⚠️ Check Result**: Success → show success, Failure → STOP and show error

6. **Display Result**
   - **Success**: Show "✅ 任务执行完成" and task output

## Examples

### Example 1: Run by Name

**User**: "运行日报任务"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "日报任务" → task_001 "daily-news"

# Step 3: Show task card
✅ 为您找到了您要运行的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：日报汇总 |
| **任务要求**：收集今天科技行业的热点新闻并整理... |
| **执行频率**：每天09:00 |
| **启用状态**：✅ 开启 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要立即运行任务'日报汇总'吗？"
User: "确定运行"

# Step 5: Execute
teleai-agent-schedule run task_001

# Step 6: Display result
✅ 任务执行完成
[Task output]
```

### Example 2: Run by Time

**User**: "立即运行9点的那个提醒"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "9点" → task_002 "mail-reminder"

# Step 3: Show task card
✅ 为您找到了您要运行的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：邮件提醒 |
| **任务要求**：邮件查看提醒 |
| **执行时间**：每天09:00 |
| **启用状态**：❌ 停用 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要立即运行任务'邮件提醒'吗？"
User: "确定运行"

# Step 5: Execute
teleai-agent-schedule run task_002

# Step 6: Display result
✅ 任务执行完成
[Task output]
```

### Example 3: User Cancels Run

**User**: "手动触发那个备份检查"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "备份检查" → task_003 "backup-check"

# Step 3: Show task card
✅ 为您找到了您要运行的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：备份检查 |
| **任务要求**：检查最近一次备份是否成功 |
| **执行时间**：每隔6小时 |
| **启用状态**：✅ 开启 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要立即运行任务'备份检查'吗？"
User: "取消"

# Step 5: User cancelled, do NOT execute
⚠️ 用户取消运行，操作已中止
```

### Example 4: Task Not Found

**User**: "运行测试任务"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "测试" → No matches found

# Step 3: Show error message
❌ 未找到您要运行的任务

请尝试：
1. 使用"查看任务列表"查看所有任务
2. 使用更具体的关键词
3. 使用任务的确切名称或ID

⚠️ 操作已中止
```

### Example 5: Run Command Fails

**User**: "执行数据同步任务"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "数据同步" → task_004 "data-sync"

# Step 3: Show task card
✅ 为您找到了您要运行的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：数据同步 |
| **任务要求**：同步数据到远程服务器 |
| **执行时间**：每天08:00 |
| **启用状态**：✅ 开启 |

# Step 4: Confirm with user (使用 question tool)
Question: "确定要立即运行任务'数据同步'吗？"
User: "确定运行"

# Step 5: Execute
teleai-agent-schedule run task_004

# Step 6: Command failed
❌ 任务执行失败

任务ID：task_004

可能原因：
• 任务不存在
• 任务已被删除
• 权限不足
• 服务异常

错误详情：[error output]
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
❌ 未找到您要运行的任务

请尝试：
1. 使用"查看任务列表"查看所有任务
2. 使用更具体的关键词
3. 使用任务的确切名称或ID
```

### Run Command Fails

```
❌ 任务执行失败

任务ID：<task-id>

可能原因：
• 任务不存在
• 任务已被删除
• 权限不足
• 服务异常

错误详情：[error output]
```
