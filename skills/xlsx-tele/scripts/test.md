# XLSX fallback_formula_check 测试

目标：验证 `scripts/fallback_formula_check.py` 在 LibreOffice 不可用时仍能输出稳定 JSON 报告。

## 1. 生成一个用于测试的 `sample.xlsx`

在 `packages/skills/xlsx/` 目录下运行：

```bash
python - <<'PY'
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "Sheet1"

# 1) 用字符串模拟“缓存的公式错误值”
ws["A1"] = "#REF!"

# 2) 静态检查：引用不存在的 sheet
ws["A2"] = "=MissingSheet!A1"

# 3) 静态检查：超出 Excel 绝对边界的列（XFE = 16385，超过 XFD=16384）
ws["A3"] = "=XFE1"

# 4) 正常引用（用于确认不会被误判）
ws["A4"] = "=A1"

wb.save("sample.xlsx")
print("Wrote sample.xlsx")
PY
```

## 2. 运行 fallback

```bash
python scripts/fallback_formula_check.py sample.xlsx --out report.json
```

## 3. 检查输出

- 观察 `report.json` 中的：
  - `degraded_mode == true`
  - `cached_error_summary` 里包含 `#REF!`
  - `static_checks.static_reference_issues.missing_sheets` 包含 `MissingSheet`
  - `static_checks.static_reference_issues.out_of_bound_references` 包含 `XFE1` 的条目

## 4. 真实性说明

该测试不依赖 LibreOffice；因此：
- `cached_value_errors_found` 只能反映“Excel 缓存值里已有错误字符串”的情况
- 如果你生成的是“仅有公式、没有缓存值”的文件，fallback 可能检测不到真实的错误结果

要获得权威结果，请安装 LibreOffice/soffice 并运行 `python recalc.py ...`。

