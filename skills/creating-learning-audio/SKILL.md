---
name: creating-learning-audio
description: Use when creating or reworking spoken study audio, podcast scripts, or TTS voice notes from notes, especially when prior audio was repetitive, shallow, truncated, or lacks substantive content.
level: manual
native_agent: Hermes
---

# Creating Learning Audio

## Overview

Learning audio should teach, not merely read a generic summary. For interview prep and technical review, structure the script around concrete scenarios, the underlying conflict, failed naive approaches, the chosen tradeoff, costs, and a spoken answer the user can reuse.

## When to Use

Use this for:
- TTS-generated study audio, voice memos, podcast-style review, or NotebookLM-style source material.
- Reworking a failed audio file where the user reports repetition, empty content, truncation, or low substance.
- Turning technical notes into mobile-friendly oral review material.

Do not use for music generation or speech-to-text transcription; use the dedicated media/ASR skills for those.

## Core Workflow

1. **Inspect the prior artifact when reworking.** Check the existing script and audio metadata first: duration, size, and whether the source script was too generic.
2. **Write the script before generating audio.** Do not rely on a tiny summary prompt. The script should include:
   - a concrete scenario or object name;
   - why intuitive solutions fail;
   - the actual mechanism;
   - tradeoffs/pitfalls;
   - a 20–30 second interview answer or recall block.
3. **Prefer substantive monologue over fake banter for study audio.** Dialogue is fine only if it adds contrast and correction; avoid filler host chatter.
4. **Chunk long TTS input.** Split by semantic sections before calling TTS. This reduces provider truncation, repeated loops, and overlong-input failures.
5. **Concatenate and verify.** Combine chunks with ffmpeg, then verify duration/size and decode with `ffmpeg -v error -i file.mp3 -f null -` before claiming success.
6. **Preserve the user-facing filename when replacing failed audio.** Write a `*-v2` script/audio for traceability, then copy or replace the originally referenced file if that is what the user will tap.

## Script Pattern

For each technical topic, write in this order:

```text
现实场景 → 核心矛盾 → 朴素方案为什么错 → 正确折中 → 代价/坑点 → 面试表达
```

Good learning-audio cues:
- “先设一个具体场景……”
- “为什么不直接……”
- “这里有两个面试坑……”
- “面试表达可以这样说……”

## TTS Chunking Pattern

1. Create `topic-v2-script.md` as the source of truth.
2. Create `topic-v2-chunk1.txt`, `topic-v2-chunk2.txt`, etc. Split on section boundaries, not arbitrary character counts.
3. Generate one audio file per chunk.
4. Concatenate:

```bash
printf "file '%s'\n" "$PWD/topic-v2-part1.mp3" "$PWD/topic-v2-part2.mp3" > topic-v2-concat.txt
ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i topic-v2-concat.txt -c copy topic-v2.mp3
ffprobe -v error -show_entries format=duration,size -of json topic-v2.mp3
ffmpeg -v error -i topic-v2.mp3 -f null -
```

If codec/container mismatch causes concat issues, re-encode instead of stream-copying.

## Common Mistakes

- **Mistake: generating audio from a shallow short summary.** Fix: write a full script with scenarios and interview answers first.
- **Mistake: long single TTS call.** Fix: split into chunks and concatenate.
- **Mistake: reporting only that a file exists.** Fix: verify duration, size, and decode success.
- **Mistake: verbose podcast filler.** Fix: remove empty host banter; use contrast only to explain misconceptions.
- **Mistake: losing the attachment path the user already has.** Fix: also replace or copy to the original filename when the user asked to redo a failed attachment.

## References

- `references/redis-podcast-rework.md` — example of turning a repetitive Redis review audio into substantive interview-prep TTS with chunked generation and ffmpeg verification.
