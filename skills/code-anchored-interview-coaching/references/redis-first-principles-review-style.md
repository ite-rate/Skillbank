# Redis First-Principles Review Style

Use this reference when coaching Redis/backend interview prep after a session where the learner explicitly rejected official/black-box phrasing and asked for mechanism-level but plain-language explanations.

## Core user preference

The desired style is:

> 深度要够，但语言要本质；不堆官方黑话，不用名词压人。

Operational rule:

```text
First expose the concrete tension,
then show why the naive alternatives fail,
then let the mechanism feel inevitable,
then attach the formal term,
then compress into interview wording.
```

Avoid leading with terms like `COW`, `binlog`, `AOF rewrite`, `eventual consistency` before the learner understands the underlying pressure.

## Good pattern

```text
现实矛盾 -> 朴素方案 A 为什么不行 -> 朴素方案 B 为什么不行 -> 折中机制 -> 术语 -> 代价 -> 面试版
```

Example for Redis COW:

```text
The child process needs the old snapshot, while the parent must keep serving writes.
If they always share memory, parent writes corrupt the child snapshot.
If Redis copies all memory up front, it is too slow and may double memory.
So they share first, and only copy a page when the parent writes it.
That mechanism is Copy-On-Write.
```

Chinese interview wording:

```text
COW 其实不是神秘机制，而是一个必要折中：子进程需要 fork 那一刻的旧快照，父进程又要继续写。如果一直共享，快照会被污染；如果全量复制，太慢太占内存。所以 fork 后先共享内存页，父进程真正修改某一页时再复制这一页。子进程继续看旧页生成 RDB，父进程改新页继续服务。
```

## Redis session-specific pitfalls captured

### 1. Cache consistency / binlog listening

Learner confusion signal: “通过 MQ、binlog 监听、定时任务做异步补偿 这些不知道” and “binlog监听没懂”.

Plain explanation:

```text
binlog 监听不是业务代码里再写一遍删除缓存。
它是不靠每个业务入口手动通知，而是监听 MySQL 自己的变更日志。
只要数据库真的变了，就解析 table/id，再映射 Redis key 删除。
```

Useful chain:

```text
update MySQL
 -> MySQL writes binlog
 -> Canal/Debezium listens like a replica
 -> parse table=product, id=1001
 -> map to Redis key product:1001
 -> DEL product:1001
```

Mention the real difficulty:

```text
The hard part is not “listening”; it is mapping table changes to all affected Redis keys, especially list/aggregate caches.
```

### 2. COW and RDB

Learner confusion signals:
- “cow没懂 原理是啥”
- “为什么有这个机制没理解 直接复制整份内存会怎么样”
- “感觉cow很慢啊 啥时候才能落实快照rdb文件”
- “cow解决的是 啥问题呢”

Final stable explanation:

```text
不能一直共享，也不能全量复制，所以只能写时复制。
```

Important timing distinction:

```text
fork 成功 = 快照时间点确定。
子进程马上开始写 RDB。
COW 不是先完成再写 RDB；它只在父进程后续写共享页时发生，用来保护子进程的旧快照。
子进程写完临时文件并 rename 后，新的 RDB 文件才生效。
```

### 3. AOF normal path vs rewrite path

Learner correction: “没说aof啥时候执行 会不会fork 只说了 aof rewrite aof会fork”.

Encode this distinction explicitly:

```text
AOF normal append path: every write command appends to AOF buffer; no fork.
AOF fsync timing: appendfsync always/everysec/no.
AOF rewrite path: heavy maintenance path; may fork child process to generate new compact AOF from current memory.
```

When explaining AOF, always separate:

```text
正常路径 / 后台重写维护路径 / 恢复路径
```

### 4. Running Redis then enabling AOF

Learner question: “那如果redis启动中 开启了aof 后面的写操作会记录 之前的数据状态怎么办”.

Plain answer:

```text
运行中开启 AOF，不能只从开启那一刻开始记录新命令，否则之前已有的内存数据重启后恢复不了。
Redis 需要先根据当前内存状态生成一份基础 AOF，然后后续写命令再追加。
这个过程本质上类似一次 AOF rewrite。
```

### 5. Depth control for Redis mainline

Learner later corrected: “持久化不用这么细我感觉 我说的是redis主线”.

Use this pacing rule:

```text
For Redis mainline coaching, go deep enough to survive common mechanism follow-ups, but do not keep drilling one subtopic once the user is trying to advance the Redis roadmap.
```

Default answer depth:

```text
mechanism-level, not source-code-level.
```

## Repository artifact pattern

When asked to persist the learning session as a Redis review repo, use a class-level repository under the interview source of truth, not one-off scattered notes. Useful structure:

```text
README.md
00-学习风格与答题标准.md
01-Redis主线地图.md
02-缓存一致性.md
03-持久化机制.md
04-本次疑惑点复盘.md
notebooklm-source.md
podcast-script.md
audio-short-script.md
redis-review-podcast.mp3
```

NotebookLM/podcast source should preserve the first-principles style and focus on the learner's actual confusion points, not a generic Redis article.
