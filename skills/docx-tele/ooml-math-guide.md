# OMML 数学公式指南

当 Markdown 围栏代码块中的 LaTeX 公式需要真正的数学排版（下标、上标、分数、根号）时，用 OMML 注入。

> 此文件按需加载，不常驻 context。SKILL.md 第3层表格中的"数学公式"行指向此处。

## 结构概览

```
<m:oMath>          ← 行内公式（放在 <w:p> 内）
<m:oMathPara>      ← 块级公式（独立段落级，可含多个 <m:oMath>）
  <m:oMath>...</m:oMath>
  <m:oMath>...</m:oMath>
</m:oMathPara>
```

一个 `<m:oMath>` 内是一系列 OMML 元素的序列，按数学排版规则自动布局。

## 常用元素速查

### 基础：数学文本 `m:r` / `m:t`

```xml
<m:r>
  <m:t>θ</m:t>
</m:r>
```

### 下标 `m:sSub`

```xml
<m:sSub>
  <m:e><m:r><m:t>θ</m:t></m:r></m:e>     <!-- 基 -->
  <m:sub><m:r><m:t>t</m:t></m:r></m:sub>  <!-- 下标 -->
</m:sSub>
```

### 上标 `m:sSup`

```xml
<m:sSup>
  <m:e><m:r><m:t>x</m:t></m:r></m:e>
  <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
</m:sSup>
```

### 上下标 `m:sSubSup`

```xml
<m:sSubSup>
  <m:e><m:r><m:t>x</m:t></m:r></m:e>
  <m:sub><m:r><m:t>i</m:t></m:r></m:sub>
  <m:sup><m:r><m:t>2</m:t></m:r></m:sup>
</m:sSubSup>
```

### 分数 `m:f`

```xml
<m:f>
  <m:num><m:r><m:t>1</m:t></m:r></m:num>  <!-- 分子 -->
  <m:den><m:r><m:t>2</m:t></m:r></m:den>  <!-- 分母 -->
</m:f>
```

### 根号 `m:rad`

```xml
<m:rad>
  <m:deg><m:r><m:t>3</m:t></m:r></m:deg>  <!-- 根指数（平方根可省略） -->
  <m:e><m:r><m:t>x+1</m:t></m:r></m:e>    <!-- 被开方数 -->
</m:rad>
```

### 上下标记（帽子、横线等） `m:acc`

```xml
<m:acc>
  <m:accPr>
    <m:chr m:val="&#x0302;"/>   <!-- ^ 帽 -->
  </m:accPr>
  <m:e><m:r><m:t>y</m:t></m:r></m:e>
</m:acc>
```

常用 accent 字符：`&#x0302;`(帽^) `&#x0304;`(横线¯) `&#x0303;`(波浪线~) `&#x0307;`(点˙) `&#x20D7;`(矢量→)

### 括号 `m:d`

```xml
<m:d>
  <m:dPr>
    <m:begChr m:val="("/>
    <m:endChr m:val=")"/>
  </m:dPr>
  <m:e><!-- 括号内容 --></m:e>
</m:d>
```

### 大型运算符 `m:nary`（求和、积分、乘积）

```xml
<m:nary>
  <m:naryPr>
    <m:chr m:val="∑"/>          <!-- 求和符号 -->
    <m:limLoc m:val="undOvr"/>  <!-- 上下限位置 undOvr / subSup -->
  </m:naryPr>
  <m:sub><m:r><m:t>i=1</m:t></m:r></m:sub>
  <m:sup><m:r><m:t>n</m:t></m:r></m:sup>
  <m:e><m:r><m:t>x_i</m:t></m:r></m:e>
</m:nary>
```

nary 符号：`∑` 求和, `∏` 乘积, `∫` 积分, `∬` 二重积分

### 矩阵 / 多行对齐 `m:eqArr`

```xml
<m:eqArr>
  <m:e><m:r><m:t>m_t = β₁·m_{t-1} + (1-β₁)·∇L</m:t></m:r></m:e>
  <m:e><m:r><m:t>v_t = β₂·v_{t-1} + (1-β₂)·(∇L)²</m:t></m:r></m:e>
</m:eqArr>
```

注意：`m:eqArr` 内每个 `<m:e>` 是一行，用最简单的内容即可。真正数学下标仍需嵌套 `m:sSub` 等。

## 工作流

### 1. 生成并解包 docx

```bash
# 正常走 Markdown→JS→docx 流程，然后：
python ooxml/scripts/unpack_workflow.py document.docx unpacked/
```

### 2. 编辑 document.xml 注入 OMML

找到公式对应的 `<w:p>` 段落（通过 Consolas 字体文本定位），替换为含 `<m:oMath>` 的段落。

替换模板 — 将整段代码文本替换为块级公式段落：

```xml
<w:p>
  <w:pPr>
    <w:jc w:val="center"/>
  </w:pPr>
  <m:oMathPara>
    <m:oMath>
      <!-- OMML 元素放这里 -->
    </m:oMath>
  </m:oMathPara>
</w:p>
```

如果公式放在正文行内（而不是独立段落），则用 `<m:oMath>` 放在 `<w:r>` 之后即可。

### 3. 打包

```bash
python ooxml/scripts/pack_workflow.py unpacked/ document.docx
```

## Python 辅助脚本模板

```python
import sys
sys.path.insert(0, "C:\\Users\\zhang\\.config\\TeleAgent\\skills\\docx")
from scripts.document_workflow import document_impl
from lxml import etree as ET

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"

doc = document_impl("unpacked/")

# 1. 找到 consolas 字体的公式段落
body = doc.get_node_impl("w:body")
for p in body.findall(".//" + doc.w("p")):
    # 检查是否包含 Consolas 文本
    for t in p.findall(".//" + doc.w("t")):
        if "θ_{" in (t.text or ""):
            # 2. 构建 OMML 替换
            omath = build_omath(t.text)  # 你的 LaTeX→OMML 转换函数
            # 替换整个段落
            parent_p = list(p.iterancestors(doc.w("p")))[0] if not p.tag.endswith("}p") else p
            # ... 执行替换
            break

doc.save_impl()
```

## LaTeX → OMML 映射速查

| LaTeX | OMML | 说明 |
|-------|------|------|
| `x_{i}` | `<m:sSub><m:e>x</m:e><m:sub>i</m:sub></m:sSub>` | 下标 |
| `x^{2}` | `<m:sSup><m:e>x</m:e><m:sup>2</m:sup></m:sSup>` | 上标 |
| `\frac{a}{b}` | `<m:f><m:num>a</m:num><m:den>b</m:den></m:f>` | 分数 |
| `\sqrt{x}` | `<m:rad><m:e>x</m:e></m:rad>` | 平方根 |
| `\sqrt[n]{x}` | `<m:rad><m:deg>n</m:deg><m:e>x</m:e></m:rad>` | n次根 |
| `\hat{y}` | `<m:acc><m:accPr><m:chr val="&#x0302;"/></m:accPr><m:e>y</m:e></m:acc>` | 帽子 |
| `\sum_{i=1}^{n}` | `<m:nary><m:naryPr><m:chr val="∑"/></m:naryPr><m:sub>i=1</m:sub><m:sup>n</m:sup></m:nary>` | 求和 |
| `\int_{a}^{b}` | `<m:nary><m:naryPr><m:chr val="∫"/></m:naryPr><m:sub>a</m:sub><m:sup>b</m:sup></m:nary>` | 积分 |
| `\nabla` | `<m:r><m:t>∇</m:t></m:r>` | 希腊字母直接用 Unicode |
| `\theta` | `<m:r><m:t>θ</m:t></m:r>` | 同上 |
| `\alpha` | `<m:r><m:t>α</m:t></m:r>` | 同上 |
| `\beta` | `<m:r><m:t>β</m:t></m:r>` | 同上 |
| `\cdot` | `<m:r><m:t>·</m:t></m:r>` | 乘点 |
| `\pm` | `<m:r><m:t>±</m:t></m:r>` | 正负号 |

## 注意事项

- OMML 不需要 `xml:space="preserve"` — 数学文本默认保留空格
- `<m:oMathPara>` 只能在 `<w:p>` 内，不能直接出现在 body 下
- 公式渲染效果依赖 Word 的数学引擎和系统字体，不同平台可能有细微差异
- docx-js 不原生支持 OMML，不要尝试用 JS 生成 — 直接走后编辑
- 修改 document.xml 后必须同步更新 `[Content_Types].xml` 确认 math 命名空间已声明（通常已由 Word 默认声明）
