# Redis Podcast Rework Pattern

## Trigger

The user replied to a generated MP3 and said it failed because it kept repeating and had no actual content. Treat this as a learning-audio quality failure, not only a TTS failure.

## What worked

1. Inspect the old artifacts:
   - read the existing short script and full script;
   - check audio metadata with `ffprobe`;
   - note whether the old audio was very short or built from a generic summary.
2. Rewrite a substantive script before touching TTS:
   - concrete Redis examples such as `product:1001`;
   - cache consistency failure timelines;
   - binlog listener as a change-notification source;
   - RDB/COW tradeoff and costs;
   - AOF append vs fsync vs rewrite;
   - mixed persistence as RDB base + AOF delta;
   - explicit “面试表达” blocks.
3. Split the spoken text by semantic sections into separate chunk files.
4. Generate each chunk separately with TTS.
5. Concatenate chunks with ffmpeg and verify:
   - `ffprobe -show_entries format=duration,size`;
   - `ffmpeg -v error -i output.mp3 -f null -`.
6. Copy the final v2 MP3 over the originally attached filename so the user can tap the same artifact path.

## Content lesson

For technical interview audio, the user values practical substance over podcast polish. Prefer:

```text
现实场景 → 错误方案 → 正确机制 → 坑点/代价 → 30 秒口语答案
```

Avoid:

```text
泛泛开场 → 概念罗列 → 重复三句总结 → 空泛收尾
```

## Example section outline

```text
Part 1: 开场，总答案
Part 2: 缓存一致性，先更新 MySQL 再删 Redis
Part 3: binlog 监听，换通知源而不是强一致魔法
Part 4: RDB/COW，fork 后旧快照和继续写的矛盾
Part 5: AOF，追加、刷盘、rewrite
Part 6: 混合持久化，RDB 基础快照 + AOF 增量
Part 7: 结尾，四句可背口语答案
```
