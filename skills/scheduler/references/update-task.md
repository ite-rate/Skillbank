# Updating Tasks

## Command Syntax

**Note**: Avoid using `--offline` or `--force-offline` options as they bypass the daemon service and can cause data inconsistency. Only use standard command options as shown in this document.

**Daemon Failure Handling**: If command fails with daemon errors (e.g., "Invalid bearer token", "Connection refused", "daemon not running"):
- Stop immediately and report the error
- DO NOT attempt to use `--offline` or `--force-offline` as a workaround

### Enable/Disable Tasks

```bash
# Enable task
teleai-agent-schedule enable <task-id>

# Disable task
teleai-agent-schedule disable <task-id>
```

### Modify Task Properties

```bash
teleai-agent-schedule update <task-id> [options]
```

**Options**:
- `--name <name>` - Update task name
- `--prompt <description>` - Update task description/content（遵循 SKILL.md「任务要求」规则：有明确表述则原样复制，否则尽可能准确、全面描述意图）
- `--expr <cron-expression>` - Update schedule (cron tasks)
- `--run-at <ISO-8601-timestamp>` - Update execution time (once tasks)
- `--project-path <path>` - Update workspace path

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
   - **No matches**: Show message, STOP

3. **Parse Modification Type**
   - **Enable/Disable**: Keywords "启用", "开启", "停用", "禁用", "关闭"
   - **Property update**: Keywords "改成", "修改", "添加", "移除"
   - **任务要求变更**：用户给出新的明确表述时原样写入 `--prompt`；仅笼统说明时按意图尽可能准确、全面描述（同 SKILL.md「任务要求」规则）

4. **Show Task Card Preview**

   ```markdown
   | 📋 定时任务详情（更新预览） |
   |:---|
   | **任务名称**：<task name> |
   | **任务要求**：<task prompt> |
   | **执行频率**：<frequency> |
   | **执行时间**：<time> |
   | **工作空间**：<project-path> |
   | **使用技能**：<skill> |
   | **使用MCP**：<mcp> |
   | **启用状态**：<status> |

   **变更说明**：
   • <field>：<old> → <new>
   ```

5. **Confirm with User** ⚠️ **REQUIRED STEP**

   **⚠️ IMPORTANT**: Always use question tool to get user confirmation BEFORE executing any command to prevent unintended changes.
   - **Do not execute command until user confirms**

6. **Execute Command**

   **Only AFTER user confirmation**, execute the appropriate command:

   **For Property Updates**:
   ```bash
   teleai-agent-schedule update <task-id> [options]
   ```

   **For Enable/Disable**:
   ```bash
   teleai-agent-schedule enable <task-id>
   teleai-agent-schedule disable <task-id>
   ```

   **⚠️ Check Result**: Success → show success, Failure → STOP and show error

## Examples

### Example 1: Modify Execution Time

**User**: "把每天早上9点的日报任务改成9点半"

```bash
# Step 1: Get task list
teleai-agent-schedule list --json

# Step 2: Identify task
Match: "每天早上9点的日报" → task_001

# Step 3: Parse modification
Type: Property update (time)

# Step 4: Show preview
```
| 📋 定时任务详情（更新预览） |
|:---|
| **任务名称**：日报汇总 |
| **任务要求**：查看所有人员的日报并进行汇总 |
| **执行频率**：每天 |
| **执行时间**：9:30 |
| **工作空间**：C:/Users/Administrator/Downloads |
| **使用技能**：无 |
| **使用MCP**：无 |
| **启用状态**：✅ 开启 |

**变更说明**：• 执行时间：09:00 → 09:30
```

# Step 5: Confirm with user (使用 question tool)
Question: "确认要修改吗？"
User: "确认"

# Step 6: Execute
teleai-agent-schedule update task_001 --expr "30 9 * * *"
✅ 任务已更新成功
```

### Example 2: Disable Task

**User**: "把周五的日报汇总先停用一下"

```bash
# Step 1-2: Get list and identify
teleai-agent-schedule list --json
Match: "周五的日报" → task_002

# Step 3: Parse modification
Type: Disable operation

# Step 4: Show preview
| 📋 定时任务详情（更新预览） |
|:---|
| **任务名称**：日报汇总 |
| **任务要求**：查看所有人员的日报并进行汇总 |
| **执行频率**：仅一次 |
| **执行时间**：2026-03-20 09:30:00 |
| **工作空间**：C:/Users/Administrator/Downloads |
| **使用技能**：无 |
| **使用MCP**：无 |
| **启用状态**：❌ 停用 |

**变更说明**：• 启用状态：✅ 开启 → ❌ 停用

# Step 5: Confirm with user (使用 question tool)
Question: "确认要修改吗？"
User: "确认"

# Step 6: Execute
teleai-agent-schedule disable task_002
✅ 任务已更新成功
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
❌ 未找到匹配的任务

请尝试：
1. 使用"查看任务列表"查看所有任务
2. 使用更具体的关键词
```

### Update/Enable/Disable Fails

```
❌ 操作失败

任务ID：<task-id>

可能原因：
• 任务不存在
• 无效的cron表达式
• 权限不足

错误详情：[error output]
```