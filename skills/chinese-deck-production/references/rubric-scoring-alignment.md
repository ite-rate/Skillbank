# Scoring-rubric alignment + 方正极简 layout (worked example)

Source session: 2026-08-10, 数据要素大赛答辩 (火眼AI智慧消防), pages P13 市场空间 + P14 推广可行性.
User corrections that shaped this design: "字体调大点 / 换一个模板 / 太丑了 / 要那种方方正正 / 花里胡哨的颜色少点的".

## The rubric (OCR'd from the judge-screenshot, 中国信息协会数据要素应用创新大赛)

- **市场潜力 (0-10 分)**: 考察项目的目标市场定位、市场空间和规模、推广前景等情况
  - 市场空间巨大且需求明确 → 8-10 分
  - 潜在市场较大 → 5-7 分
  - 市场有限 → 0-4 分
- **示范推广性 (25 分)**, 子项 **推广可行性 (0-15 分)**: 考察项目是否形成具有可复制、可推广的系统解决方案以及项目的团队、资金等基础保障情况
  - 已形成行业标准且组织稳定、团队能力强 → 12-15 分
  - 方案有复制潜力且形成团标地标，团队有可持续发展能力 → 8-11 分
  - 方案难以形成标准，团队能力较弱 → 0-7 分

## Page → rubric mapping (both pages hit the TOP band)

**P13 市场空间** (tag: 市场空间 MARKET SPACE)
- 深蓝定位条 (14pt): 目标市场定位一句话 → 坐实"目标市场定位清晰"
- 三级市场大数字卡（本地→全省→全国）:
  - 安阳本地·已落地: 147 家 / 重点消防单位 + 10 大行业场景 + 九小场所全域
  - 河南全省·复制中: 18 地市 / 电信属地体系联动，驻马店已同步推进
  - 全国市场·可推广: 百万家级 / 全国消防重点单位存量改造
  → 证明"市场空间巨大"且有落地支撑（空间不是画饼）
- 需求三证据卡（政策强制 / 事故教训 / 合规刚需）→ 证明"需求明确":
  - 政策: 「十五五」事前预防转型 + 省厅 2026 通知 + 市「十四五」规划
  - 事故: 具体数字才有冲击力 — 2022.11 安阳火灾 42 死·损失 1.23 亿；北京长峰医院 29 死
  - 合规: 唯一通过消防合格检测 + 人保承保 2000 万 → 减责免责刚需
- 底部总结句: 存量改造 × 政策强制 × 全域覆盖：本地已落地、全省在复制、全国可推广

**P14 推广可行性** (tag: 推广可行性 FEASIBILITY)
- 左大卡「标准化·可复制的系统解决方案」: 产品包四要素(算力+AI+网络+保险) / 利旧零改造秒级预警 / 10 大行业部署标准+7 类建议书模板 / 双标杆落地(宾馆+市政府大楼) / 方法论(试点→复盘→标准化→批量) → 回答"能不能复制"
- 右上「已形成的行业标准与资质」: 唯一通过消防电子质检合格检测 / CECS 448:2016 / 发明专利+软著 → 坐实"已形成行业标准"这一句
- 右下「组织与资金保障」: 央企 18 地市联动 / 与应急管理部天津消防研究所联合研发 / 政企专班+本地 7×24 运维 / 人保承保(财产险 2000 万·人身险 20 万/人) → 回答"团队强不强、钱稳不稳"
- 底部推广路径: 政策牵引 → 试点先行 → 分类推进(2026.9 / 2026.12 / 2027) → 行业渗透

## 方正极简 style recipe (user-approved)

- Shapes: RECTANGLE only — no ROUNDED_RECTANGLE, no shadow, no gradient
- Palette: bg F2F3F5 / white blocks / border D9DDE2 1pt / ink 1A2530 / gray 6B7280 / accent red C93A32 / navy 0F1B2D (bars only)
- header(): red square 0.16 at (M, 0.34) + gray tag (charSpacing 3) + title 28pt bold at y 0.66 + line rule h 0.014 at y 1.42
- Hero number: two runs — `[{text: v, options:{fontSize:30,color:red,bold:true}}, {text:' '+u, options:{fontSize:15,color:gray,bold:true}}]`
- blockTitle(): red square 0.14 + 13-17pt bold ink
- bullets(): `bullet:{code:"2013", indent:14}`, paraSpaceAfter 5, lineSpacingMultiple 1.12, fit:"shrink"
- Bottom close: summary 14pt bold centered at y 6.5 (h 0.42) + red strip (w CW, h 0.045) at y 6.95
- Footer: navy bar h 0.45 at y 7.05, text 9pt color 8FA0B5, page "13 / 16" right-aligned

## Footer-overlap pitfall (hit and fixed this session)

First version: red bar at y 6.68 (h 0.26) + summary text at y 7.0 (h 0.5) → text bottom edge 7.5 sat ON TOP of the navy footer (starts 7.05).
Fix: summary text at y 6.5 h 0.42; red underline strip at y 6.95 h 0.045; everything stays above 7.0.
QA assertion (python-pptx): flag non-footer content bleeding into the footer band —
`shape.top < 7.0 and shape.top + shape.height > 7.02 and shape.height > 0.4`.

## OCR fallback for rubric screenshots (no vision tool available)

```bash
sips -Z 2880 img.jpg --out img_big.png          # 2x upscale — big accuracy win for small text
tesseract img_big.png stdout -l chi_sim --psm 6  # iterate psm 3/4/6/11; tables respond best to psm 6
```
tesseract chi_sim was at /opt/homebrew/bin/tesseract. Garbled table cells are normal — cross-check multiple psm variants, crop regions (`sips -c H W --cropOffset`) for rows that stay unreadable, and reconstruct the rubric structure by hand from the fragments.

## Standalone N-page delivery

Copy helpers into a standalone script (build_p13_14.js), emit a separate N-slide pptx, keep the MASTER footer numbers ("13 / 16") so pages re-slot unchanged. Patch the same IIFE blocks into the master build script to keep the full deck in sync. Verify the standalone file with the same python-pptx dump (slide count, boundary check, footer-overlap assertion).
