# Creating Tasks

## Command Syntax

**Note**: Avoid using `--offline` or `--force-offline` options as they bypass the daemon service and can cause data inconsistency. Only use standard command options as shown in this document.

**Daemon Failure Handling**: If command fails with daemon errors (e.g., "Invalid bearer token", "Connection refused", "daemon not running"):
- Stop immediately and report the error
- DO NOT attempt to use `--offline` or `--force-offline` as a workaround

### Recurring Tasks (cron)

```bash
teleai-agent-schedule add \
  --name "<task-name>" \        # Required: Task name (2-8 characters)
  --type cron \                 # Required: Schedule type
  --expr "<expression>" \       # Required for cron: Cron expression (e.g., "0 9 * * *" for daily 9 AM)
  --prompt "<description>" \    # Required: Natural language task description
  --project-path "<path>"      # Required: Project directory path
```

### One-Time Tasks (once)

```bash
teleai-agent-schedule add \
  --name "<task-name>" \               # Required: Task name (2-8 characters)
  --type once \                       # Required: Schedule type
  --run-at "<ISO-8601-timestamp>" \    # Required for once: Execution time in UTC (e.g., "2026-03-10T15:00:00Z")
  --prompt "<description>" \           # Required: Natural language task description
  --project-path "<path>" \           # Required: Project directory path
```

## Task Card Format

```Markdown
| 📋 定时任务详情 |
|:---|
| **任务名称**：<LLM总结的任务名称> |
| **任务要求**：见下方「任务要求」规则；若使用技能须在内容中体现 |
| **执行频率**：<cron/once> |
| **执行时间**：<具体时间> |
| **工作空间**：默认为当前工作目录路径，用户可指定 |
| **使用技能**：无（可选） |
| **引用文件**：无（可选） |
| **使用MCP**：无（可选） |
| **启用状态**：默认为"✅ 开启"，用户可指定 |
```

## 任务要求（`--prompt`）

1. **用户有明确表述**：用户已给出可识别的任务要求原文时，**原样复制**到 `--prompt` 与任务卡片的「任务要求」，勿改写或省略。
2. **用户无明确表述**：未单独说明或过于笼统时，根据理解**尽可能准确、全面**地写出可执行的任务要求；引用技能、文件或 MCP 时须写入任务要求。

## Workflow

**Why validate first**: Running all validations before presenting the task card prevents wasting user time on confirming tasks that cannot be created. It also ensures a cleaner user experience by catching issues early.

**Why stop on errors**: When a command fails, continuing can cause data inconsistency or confusion. Stop immediately and report the error clearly to the user.

1. **Parse & Extract** - Extract task name, prompt, frequency, and time from user input
   - **任务要求**：按上文「任务要求（`--prompt`）」规则填写 `prompt`
   - Ask for missing information using question tool (frequency first, then time)

2. **Validate All** - Run all validations in one step before showing the card
   - **Resources**: Check if skills, files, and MCP servers exist
     - Error if not found: `❌ 资源验证失败\n\n资源'<name>'不存在，请检查后重试。\n\n可能原因：\n• 技能名称错误或技能未安装\n• 文件路径错误或文件不存在\n• MCP服务器名称错误或未配置`
   - **Time** (once tasks only): Check if `--run-at` is in the past
     - Error if past: `❌ 指定的执行时间已过\n\n任务执行时间：[time]\n当前时间：[now]\n\n一次性任务必须在未来的时间执行。`
   - **If any validation fails**: Stop and show the error

3. **Present Card** - Display the task card following the format defined in the "Task Card Format" section
   - Only reached if all validations pass

4. **Confirm** - Get user confirmation using question tool
   - Options: "确认创建" / "取消" / "修改"
   - If "修改": Ask for updated details and go back to step 1

5. **Execute** - Run `teleai-agent-schedule add [options]` based on confirmed card
   - **Success**: Proceed to step 6
   - **Failure**: Stop and show error: `❌ 任务创建失败\n\n错误详情：[command output]`

6. **Report** - Show success message with next run time

## Examples

```bash
# Daily task at 9 AM (recurring)
teleai-agent-schedule add --name "daily-news" --type cron --expr "0 9 * * *" --prompt "收集热点新闻" --project-path "/Users/xxx/projects/app"

# Interval task: Every 2 hours
teleai-agent-schedule add --name "drink-water" --type cron --expr "0 */2 * * *" --prompt "提醒我喝水" --project-path "/Users/xxx/projects/app"

# Weekly task: Every Sunday at 2 AM
teleai-agent-schedule add --name "weekly-backup" --type cron --expr "0 2 * * 0" --prompt "刷新网页" --project-path "/Users/xxx/projects/app"

# One-time task at specific time (UTC)
teleai-agent-schedule add --name "project-report" --type once --run-at "2026-03-10T15:00:00Z" --prompt "生成项目日报" --project-path "/Users/xxx/projects/app"

# With custom --project-path
teleai-agent-schedule add --name "daily-sync" --type cron --expr "0 8 * * *" --prompt "数据同步" --project-path "/custom/path/to/project"
```

## Time Expression Patterns

### Daily Patterns
```
"每天早上9点" → "0 9 * * *"
"每天下午2点" → "0 14 * * *"
```

### Weekly Patterns
```
"每周一早上9点" → "0 9 * * 1"
"每周五下午5点" → "0 17 * * 5"
```

### Interval Patterns
```
"每隔1小时" → "0 */1 * * *"
"每隔30分钟" → "*/30 * * * *"
```

## Example Flow

### Complete Information Flow (Success)

```
User: "每天早上9点查看黄金一周趋势"

[步骤1: Parse & Extract]
✓ 提取完成：name=daily-gold-trend, type=cron, expr=0 9 * * *, prompt=查看黄金一周趋势

[步骤2: Validate All - 资源、时间、数量检查]
✓ 验证通过（无技能/文件/MCP引用，时间为未来，任务数<10）

[步骤3: Present Card]
```
这是一个需要自动执行的任务吗？我的理解，您想要建立以下的任务：

| 📋 定时任务详情 |
|:---|
| **任务名称**：每日黄金趋势查看 |
| **任务要求**：查看黄金一周趋势 |
| **执行频率**：每天 |
| **执行时间**：09:00 |
| **工作空间**：/Users/xxx/projects/app |
| **使用技能**：无 |
| **引用文件**：无 |
| **使用MCP**：无 |
| **启用状态**：✅ 开启 |
```

[步骤4: Confirm - 使用 question tool]

选项：
1. 确认创建
2. 取消
3. 修改

User: 选择 "确认创建"

[步骤5: Execute]
teleai-agent-schedule add --name "每日黄金趋势查看" --type cron --expr "0 9 * * *" --prompt "查看黄金一周趋势" --project-path "/Users/xxx/projects/app"

[步骤6: Report]
✅ 任务创建成功！下次执行时间：明天 09:00
```


### Resource Validation Failure Flow (Validation Failure)

```
User: "每天9点检查代码，使用code-analyzer技能"

[步骤1: Parse & Extract]
✓ 提取完成，包含 skill=code-analyzer

[步骤2: Validate All - 检查 skill "code-analyzer"]

❌ 资源验证失败

资源'code-analyzer'不存在，请检查后重试。

可能原因：
• 技能名称错误或技能未安装
• 文件路径错误或文件不存在
• MCP服务器名称错误或未配置
```