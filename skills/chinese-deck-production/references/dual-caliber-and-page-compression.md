# 双口径补短板 + 22页大纲→14页压缩 (worked example: 安阳宾馆智慧消防 答辩PPT)

Session: 16页 deck existed → user provided 22-page outline → asked "压缩到14页" with
"跟上次比 优化了一些内容". Result: 答辩PPT_14页.pptx (build_deck_14.js pattern).

## 1. 双口径 (dual-caliber) strategy — 补申报书客观短板, 不虚构

申报书 v3.0 had 4 objective weaknesses. Fix = run two labeled calibers on the SAME
slides instead of merging/inflating. Every page/card that uses product-line assets
carries a caliber label; a neutral 口径说明 line sits at page bottom.

| 短板 | 产品体系口径 (mature product line) | 项目口径 (this project) |
|---|---|---|
| 客户仅1家 | 火眼 2012 起千余家落地案例(文博/酒店/医院/化工/变电站) = "5个以上成熟案例" | 安阳宾馆 = 最新标杆; 在谈/意向复制客户清单(酒店/商超/写字楼/医院/学校) |
| 参赛单位 0专利0软著 | 火眼发明专利/软著/CECS 448:2016 主编 = 核心技术底座 (chip: "技术底座口径") | 参赛单位自身软著/专利 (待补充 placeholder) |
| 收入规模小 | — | 不拼总量拼结构: 三层收入(硬件/算法授权/持续服务), 服务占比 20%→50%+, 单点经济账+回收期 |
| 未形成标准 | CECS 448:2016 主编资历 | 本项目沉淀 "人员密集场所视频数据治理四规范" + 团标/地标申报计划 |

Rules:
- Label chips/cards explicitly: "产品体系口径" / "项目口径" — never let product-line
  claims read as project facts.
- 口径说明 footer line, audience-facing neutral wording, e.g.
  "口径说明：产品体系口径 = 火眼整体能力沉淀；项目口径 = 本项目实际落地 —— 两类信息并列呈现、真实可查".
- Outline's own strategy notes (冲「2项以上专利」档 / 注明口径 / 双口径并列页页标注清楚)
  are WORKING NOTES → rewrite neutral before generating, or QA will flag them.

## 2. 22页 → 14页 compression mapping (merge along rubric, never across)

| # | 14页 deck | 来源(22页大纲) | 评分对应 |
|---|---|---|---|
| 1 | 封面 (新主标题, 赛道口径待确认标注) | 封面 | — |
| 2 | 一页速览: 6数字 + 一句话定位 | P1 | 整体印象 |
| 3 | 痛点 + 数据归因 + 政策契合 | P2+P3 | 应用实效性·解决行业痛点 |
| 4 | 四层一体两翼架构 | P4 | 创新及先进性 |
| 5 | 数据要素价值主线 (核心页, 单独成页) | P5 | 创新及先进性·全篇核心 |
| 6 | 三大关键能力: 利旧/AI预警/网业协同 | P6+P7+P8 | 创新及先进性 |
| 7 | 模式创新 + 知识产权背书 | P9+P10 | 创新及先进性·业务模式创新 |
| 8 | 数据集 + 数据飞轮 + 治理四规范 | P11+P12 | 应用实效性·数据质量 |
| 9 | 标杆案例成效账本 + 前后对比 | P13 | 应用实效性·落地成熟度 |
| 10 | 产品成熟度 + 复制管道 (双口径) | P14+P15 | 应用实效性·覆盖 + 示范推广 |
| 11 | 商业价值: 三层收入/定价/经济账/社会效益 | P16+P17+P18 | 商业价值 |
| 12 | 市场潜力 + 三路径 + 标准计划 | P19+P20 | 示范推广性 |
| 13 | 团队保障 + 三年路线图 + 结语 | P21+P22 | 示范推广·组织稳定 |
| 14 | 致谢 | — | — |

Compression rules:
- 数据要素主线 stays its own page (灵魂主线); cover/thanks always stay.
- Every content page carries top-right score tag: "对应：创新及先进性 · 25分" (评分规则即目录).
- One memory point per page: merged page title = single conclusion.
- 结语句 kept on P13 (让每一路沉睡的摄像头，都成为守护安全的数据哨兵).

## 3. QA findings worth pre-empting (all hit this deck)

1. **叠字**: "5–10 秒秒级预警" (from merging 秒级 + 秒级预警) — grep `([一-龥])\1`.
2. **Internal notes on slides**: 冲「...」档 / 注明口径 / 页页标注 — rewrite neutral.
3. **Grid right-margin overflow**: 3×3.94 + 2×0.26 = 12.34 > content width 12.333.
   Check `x0 + (n-1)*(w+g) + w ≤ 12.333` with slack; keep x0 = M+0.05 for row alignment.
4. **Contrast**: amber E8A13C on white = 2.19:1 → darken to C7781D; teal 0E8A7A → 0C7769.
5. **Style consistency**: same logical row must use same accent-bar orientation (left bar vs
   top bar) — QA flagged mixed bars on the pricing row.
6. **Footer page numbers**: verify "NN / 14" present on all content slides via markitdown
   or PyMuPDF text blocks at y>505pt.

## 4. Reuse path

- Prior deck's build script (build_deck.js) = palette/helpers source; copy C palette,
  header/footer/card/chip/bullets/statCard into build_deck_14.js.
- Rendering: `NODE_PATH=$(npm root -g) node build_deck_14.js` → soffice → pdftoppm -r 110.
- Vision-free geometry QA: subagent + PyMuPDF (see deck-visual-qa-without-vision.md).
