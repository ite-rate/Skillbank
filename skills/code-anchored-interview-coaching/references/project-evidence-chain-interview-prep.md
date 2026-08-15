# Project Evidence Chain Interview Prep

Use this when the learner says they know the theory but freeze when the interviewer asks from a resume project, e.g. “你简历写索引优化，是怎么优化的、为什么优化？”

## Core diagnosis

The missing layer is not another theory card. It is a project evidence chain:

```text
resume claim -> concrete project scene -> original symptom -> diagnosis path -> technical cause -> exact change -> result -> follow-up anchors
```

Interviewers usually do not ask “what is an index?” first. They ask from the resume:

```text
哪个接口慢？为什么慢？原 SQL/查询形状是什么？Explain 怎么看？
你加了什么索引？为什么这个字段顺序？效果多少？副作用是什么？
```

## Required artifact shape

For each resume bullet or project highlight, create one short story card:

```text
# <Project>｜<Resume Claim>

## 简历句子
<the exact or likely resume wording>

## 业务场景
Which feature/user path/endpoint/job this happened in.

## 原始问题
What was slow, unstable, duplicated, inconsistent, or hard to maintain.

## 定位过程
How the problem was found: logs, slow SQL, EXPLAIN, metrics, traces, user report, retry records, etc.

## 技术原因
The mechanism behind the problem.

## 具体改法
What changed: SQL/index/key/TTL/queue/worker/data model/interface/config.

## 为什么这样改
Tradeoff and alternative rejected.

## 效果
Prefer real numbers. If unknown, use honest qualitative wording: “扫描行数下降 / 慢查询减少 / 响应更稳定,” not fake metrics.

## 30 秒口语版
Natural Chinese interview answer.

## 高频追问
5-8 likely follow-ups with 5-keyword answer anchors.
```

## Example: index optimization

```text
项目问题：医疗填报平台列表/统计查询变慢
定位：慢 SQL + EXPLAIN，关注 type/key/rows/Extra
原因：过滤条件、排序分页和复合索引顺序不匹配，扫描行数大，可能 filesort/回表多
改法：按查询形状设计复合索引，把等值过滤字段放前面，范围/排序字段放后面
效果：扫描行数下降，慢查询减少，接口响应更稳定
追问：最左前缀、覆盖索引、回表、filesort、深分页、写入成本
```

30 秒口语版:

> 我优化的是医疗填报平台里的列表和统计查询。这个接口会按医院、状态、时间范围筛选数据，数据量上来后响应变慢。我先看慢 SQL 和 EXPLAIN，重点看 type、key、rows、Extra，发现部分查询没有很好命中复合索引，扫描行数比较多，排序分页也不稳定。后来我按实际查询形状调整索引，把医院、状态这类等值条件放前面，时间范围或排序字段放后面，尽量减少扫描和回表。优化后慢查询减少，接口响应更稳定，同时也没有盲目加很多索引，因为索引会带来写入和存储成本。

## Coaching workflow

1. Start from the resume line, not the theory topic.
2. Ask for only the missing evidence slots first: project, endpoint/scene, query/event shape, symptom, rough change.
3. If the learner is unsure, construct a plausible but explicitly marked draft and ask them to confirm, rather than forcing a perfect recall.
4. Convert the story into:
   - 5 keywords
   - 30-second answer
   - 1-minute answer
   - likely follow-ups
5. Link supporting theory only after the story exists.

## Pitfalls

- Do not answer with a generic theory essay when the user’s pain is project-story weakness.
- Do not fabricate precise metrics. Use qualitative effects unless the user provides numbers.
- Do not make the story too broad. One resume claim should map to one concrete feature or path.
- Do not bury the learner in all possible database knowledge. Only pull the theory needed to defend the project claim.
