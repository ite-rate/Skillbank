# Print Skill - v2

## 创建时间
2025-03-06

## 目录结构
```
print/
├── SKILL.md                      # 核心 skill 定义
├── LICENSE.txt                   # 许可证
├── evals/
│   └── evals.json                # 测试用例
├── scripts/
│   ├── utils.py                  # 平台检测、命令构造
│   ├── print_file.py             # 主打印脚本
│   ├── get_printers.py           # 打印机列表
│   └── print_preview.py          # 预览和参数建议
└── references/
    ├── printing-guide.md         # 打印参数完整参考
    └── platform-differences.md   # 平台差异说明
```

## 功能特性

### 安全执行策略
- 默认先确认文件和打印机，再正式打印
- 支持 `--dry-run`，可在不出纸的情况下生成真实执行计划
- 无默认打印机时直接失败并返回可用打印机列表
- 返回 `backend`、`resolved_printer`、`error_code`、`job_id`（如可解析）

### 支持的文件格式
- PDF: 直接打印
- Word (.docx, .doc): 自动转换为 PDF 后打印
- Excel (.xlsx, .xls): 自动转换为 PDF 后打印
- PowerPoint (.pptx, .ppt): 自动转换为 PDF 后打印
- 图片 (.png, .jpg, .gif, .bmp): 直接打印

### 打印参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--copies`, `-n` | 份数 | 1 |
| `--printer` | 打印机名称 | 系统默认 |
| `--duplex` | 双面模式 (none/long-edge/short-edge) | 系统默认 |
| `--paper`, `-p` | 纸张 (Letter/A4/Legal) | 系统默认 |
| `--orientation`, `-o` | 方向 (portrait/landscape) | 系统默认 |
| `--pages`, `-P` | 页面范围 | 全部 |
| `--silent` | 静默模式 | False |
| `--dry-run` | 仅生成执行计划，不真实打印 | False |
| `--json` | JSON 输出 | False |

## 使用示例

### 基本打印
```bash
python scripts/print_file.py document.pdf
```

### 指定参数打印
```bash
python scripts/print_file.py report.docx \
  --printer "HP LaserJet" \
  --copies 2 \
  --duplex long-edge \
  --paper A4
```

### 安全预演
```bash
python scripts/print_file.py report.docx \
  --printer "HP LaserJet" \
  --copies 2 \
  --duplex long-edge \
  --dry-run \
  --json
```

### 批量打印
```bash
python scripts/print_file.py *.pdf --duplex long-edge
```

### 查看可用打印机
```bash
python scripts/get_printers.py
```

### 预览和参数建议
```bash
python scripts/print_preview.py document.pdf
```

## 跨平台支持

### macOS/Linux
- 使用 CUPS 打印系统 (`lp` 命令)
- 完整参数支持
- LibreOffice 用于 Office 文件转换

### Windows
- 主要使用 `lpr.exe` (需启用 LPR Port Monitor)
- 备选方案: `pdf-to-printer` (Node 模块，脚本可直接调用)
- 参数支持有限

## 依赖项

| 依赖 | 用途 | 是否必需 |
|------|------|----------|
| CUPS (macOS/Linux) | 打印后端 | 是 |
| LPR Port Monitor (Windows) | 打印后端 | 可选 |
| LibreOffice | Office 转 PDF | 是 (用于 Office 文件) |
| Python 3.6+ | 脚本执行 | 是 |

## Skill 触发描述

SKILL.md 中的 description 专门设计为 "pushy" 以提高触发率：

```
"Universal document printing for PDF, Word, Excel, PowerPoint, and image files.
Use whenever users need to print documents to their printer, whether they
explicitly say 'print', 'printer', 'printing' or describe the need to output
a file to paper/hard copy..."
```

触发关键词包括：
- print, printer, printing
- send to printer, output to printer
- hard copy, print out

## 测试状态

✅ 已完成基础验证：
- 平台检测: darwin (macOS)
- 依赖检查: lp ✓, lpstat ✓, LibreOffice ✓
- 打印机列表 JSON: 纯 JSON 输出
- `--dry-run`: 可生成无副作用执行计划

## 后续步骤

1. 可选: 运行完整 skill-creator 评估流程
2. 使用 skill-creator 跑基线 benchmark
3. 打包为 `.skill` 文件

## 技术实现亮点

1. **平台抽象**: 所有平台特定代码封装在 `utils.py`
2. **自动转换**: Office 文件自动使用 LibreOffice 转 PDF
3. **错误处理**: 统一 `error_code` + 可读错误信息
4. **JSON 输出**: 适合前端或 Agent 编排调用
5. **安全验证**: `--dry-run` 支持无副作用联调
6. **批量打印**: 支持部分失败汇总

## 与现有 Skill 的集成

| Skill | 集成方式 |
|-------|----------|
| docx | 复用 LibreOffice 转换命令 |
| xlsx | 可选调用 recalc 确保数据最新 |
| pdf | 可选预处理 (合并、提取页面) |
