# Diagram Type Templates

Reference for diagram generation. Each entry: Chinese name, English type, default engine, visual pattern, example prompt.

## Table of Contents

- [Flow Types](#flow-types) — flowchart, state, swimlane, dataflow
- [Hierarchy Types](#hierarchy-types) — orgchart, tree, mindmap
- [Time Types](#time-types) — sequence, gantt, timeline
- [Relationship Types](#relationship-types) — UML class, ER, concept, network
- [Analysis Types](#analysis-types) — SWOT, fishbone, matrix
- [Proportion Types](#proportion-types) — pyramid, funnel, venn
- [Other Types](#other-types) — architecture, infographic, auto

## Flow Types

**流程图 (flowchart)** — Draw.io default
Pattern: ellipse(start/end) → rectangle(steps) → diamond(decisions)
Example: "用户注册流程图"

**状态图 (state)** — Draw.io
Pattern: rounded rectangles(states) → arrows(transitions)
Example: "订单状态流转图"

**泳道图 (swimlane)** — Draw.io
Pattern: lanes per role, activities in time order
Example: "跨部门审批流程"

**数据流图 (dataflow)** — Draw.io
Pattern: processes(circles) → data stores(parallel lines) → external entities(rectangles)
Example: "系统数据流图"

## Hierarchy Types

**组织结构图 (orgchart)** — Draw.io default
Pattern: tree top-down, parent centered
Example: "公司组织架构图"

**树形图 (tree)** — Draw.io
Pattern: hierarchical tree, parent-child connections
Example: "文件目录结构图"

**思维导图 (mindmap)** — Excalidraw preferred
Pattern: root node (far left) → primary branches → sub-branches, all flowing left-to-right
Layout: root ellipse at x=50, Level 1 branches at x=450, Level 2 sub-branches at x=850
Connections: curved arrows (3-point with midpoint offset + roundness type 2), NEVER straight lines, always left→right
Colors: each primary branch a distinct color scheme, sub-branches inherit parent color
Anti-pattern: center-radial layout (use concept map instead), grid layout, straight lines, vertical tree
See excalidraw-guidelines.md "Mindmap Drawing Rules" for full details
Example: "产品规划思维导图"

## Time Types

**时序图 (sequence)** — Draw.io
Pattern: participants top, lifelines down, messages in time order
Example: "API 调用时序图"

**甘特图 (gantt)** — Draw.io
Pattern: tasks vertical, time horizontal
Example: "项目开发甘特图"

**时间线 (timeline)** — Draw.io
Pattern: main axis centered, events alternating sides
Example: "产品发展时间线"

## Relationship Types

**UML 类图 (class)** — Draw.io
Pattern: 3-section rectangles (name/attributes/methods)
Example: "电商系统类图"

**ER 图 (er)** — Draw.io
Pattern: entities(rectangles) ↔ relationships(diamonds), cardinality labels
Example: "学生选课系统 ER 图"

**概念图 (concept)** — Draw.io default
Pattern: core centered, labeled relationship arrows
Example: "机器学习概念图"

**网络拓扑图 (network)** — Draw.io
Pattern: core devices centered, grouped by function
Example: "企业网络拓扑图"

## Analysis Types

**SWOT 图 (swot)** — Draw.io
Pattern: 2×2 matrix, 4 colored quadrants
Example: "新产品 SWOT 分析"

**鱼骨图 (fishbone)** — Draw.io
Pattern: main spine → result, branches alternate up/down
Example: "质量问题鱼骨图"

**矩阵图 (matrix)** — Draw.io
Pattern: grid aligned, dark headers
Example: "技能矩阵图"

## Proportion Types

**金字塔图 (pyramid)** — Draw.io
Pattern: width increases top-down, centered
Example: "马斯洛需求金字塔"

**漏斗图 (funnel)** — Draw.io
Pattern: width decreases top-down
Example: "销售漏斗图"

**维恩图 (venn)** — Draw.io
Pattern: semi-transparent overlapping ellipses
Example: "技术栈维恩图"

## Other Types

**架构图 (architecture)** — Draw.io
Pattern: layered boxes, arrows between layers
Example: "微服务架构图"

**信息图 (infographic)** — Draw.io
Pattern: modular card layout, multi-color sections
Example: "年度报告信息图"

**自动 (auto)** — Agent determines type from description
Pattern: analyze user description to select appropriate diagram type
Example: "帮我可视化这个系统"

> AI生成