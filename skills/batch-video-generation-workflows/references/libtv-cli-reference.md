# LibTV CLI Reference (libtv)

LibTV official CLI — operates LibTV canvas/projects/nodes/models from terminal.
Downloaded from: https://liblibai-web-static.liblib.cloud/cli/1.1.1/libtv-cli-skill.zip

## Terminology

| Term | Meaning |
|------|---------|
| **画布 (project)** | The actual canvas file |
| **项目 (workspace)** | Container for canvases (one workspace holds multiple projects) |
| **节点 (node)** | A unit on the canvas: text/image/video/audio/script/storyboard/video-clip |
| **分组 (group)** | A named group of nodes; can trigger batch generation per group |

## Core Commands

```bash
# Login
libtv login web        # browser-based login
libtv login phone      # phone-based login

# Workspace (项目/工作区)
libtv workspace create <name>
libtv workspace list
libtv workspace use <id>     # bind current directory to workspace

# Project (画布)
libtv project create <name>
libtv project list
libtv project use <uuid>     # bind to canvas; writes .libtv/project.json
libtv project unuse

# Node — the core command
libtv node create "名称" -t <type> --prompt "..." --set "key=value" --left <upstream> --run
libtv node "名称" --run       # trigger generation on existing node
libtv node "名称" --left <upstream>  # connect upstream
libtv node list
libtv node delete "名称"

# Group — batch execution
libtv group create <name>
libtv group use <name>        # bind to group
libtv group <name> --node A --node B  # bind nodes to group
libtv group <name> --run      # trigger all nodes in group

# Upload resources
libtv upload "名称" -t image --resource ./path/to/file.png

# Model search
libtv model search --type video
libtv model <modelKey>        # full schema for a model

# Account
libtv account info
libtv account list
libtv account use <id>
```

## Node Types

| Type (-t) | Purpose |
|-----------|---------|
| `text` | Text/script generation (uses GVLM 3.1 etc.) |
| `image` | Image generation (uses LibNano Pro etc.) |
| `video` | Video generation (uses Seedance 2.0, Kling O1 etc.) |
| `audio` | Audio/music generation (uses Mureka V8 etc.) |
| `script` | Script/storyboard node with rows/table structure |
| `storyboard` | Storyboard node |
| `video-clip` | Video clip editing node |

## Video Node Parameters (-s / --set)

| Field | Values |
|-------|--------|
| `model` | "Seedance 2.0", "Kling O1", etc. (use `libtv model search --type video` to list) |
| `modeType` | text2video, singleImage2video, frames2video, image2video, video2video, videoEdit2video, audio2video, mixed2video |
| `count` | Number of outputs |
| `ratio` | adaptive, 16:9, 4:3, 1:1, 3:4, 9:16, 21:9 |
| `resolution` | 480p, 720p (Seedance 2.0) |
| `duration` | Integer seconds (4-15 for Seedance 2.0) |
| `enableSound` | on / off |
| `search_enabled` | 1 / 0 (联网开关) |

## NDJSON Pipe Pattern (key for batch)

LibTV CLI outputs NDJSON (one JSON object per line) on stdout when piped. Downstream nodes read stdin and use `nodeKey` / `newNodeKey` as `--left` references.

```bash
# Simple: two upstreams → one downstream
(libtv node "选题" && libtv node "主KV") | libtv node create "下游" -t video ...

# All-in-one: create + connect + run in one command
libtv node create "剧情" -t text \
  --prompt "根据参考图写一段分镜旁白" \
  --set "model=GVLM 3.1" \
  --left 参考图 \
  --run
```

## Batch Generation Patterns

### Pattern 1: Group batch (simplest)
```bash
libtv group create "云电脑卖点集"
libtv group use "云电脑卖点集"

libtv node create "卖点1-一台手机一台超级电脑" -t video \
  --prompt "电信云电脑品牌片：一台手机一台超级电脑，15s，赛博蓝色调" \
  --set "model=Seedance 2.0" --set modeType=text2video \
  --set ratio=9:16 --set duration=5 --set count=1

libtv node create "卖点2-随时随地办公" -t video \
  --prompt "电信云电脑品牌片：随时随地办公，15s，赛博蓝色调" \
  --set "model=Seedance 2.0" --set modeType=text2video \
  --set ratio=9:16 --set duration=5 --set count=1

# Bind and batch run
libtv group "云电脑卖点集" --node 卖点1-一台手机一台超级电脑 --node 卖点2-随时随地办公
libtv group "云电脑卖点集" --run
```

### Pattern 2: Shell loop batch
```bash
for topic in "一台手机一台超级电脑" "随时随地办公" "3A大作秒开" "设计渲染不卡" "数据安全云端存储"; do
  libtv node create "云电脑-$topic" -t video \
    --prompt "电信云电脑品牌片：$topic，15s，赛博蓝色调，未来感" \
    --set "model=Seedance 2.0" --set modeType=text2video \
    --set ratio=9:16 --set duration=5 --set count=1 \
    --run
done
```

### Pattern 3: Full DAG pipeline (multi-node creative)
```bash
set -euo pipefail

(
  libtv node create "选题" -t text --prompt "60s 都市情感短视频" --set "model=GVLM 3.1" &&
  libtv node create "主KV" -t image --prompt "9:16 竖版主 KV" --set "model=LibNano Pro" --set ratio=9:16
) | libtv node create "拼图D" -t image \
    --prompt "拼合选题与主 KV" \
    --set "model=LibNano Pro" --set ratio=9:16 --set modeType=image2image

# Then pipe into video generation...
```

## Key Behaviors

- `--left` accepts display name or nodeKey (must be unique in current scope)
- `--run` triggers generation immediately after node creation
- `>/dev/null` on a create command suppresses its NDJSON from flowing to downstream pipe
- `libtv node "名称"` (no write params) = query only, outputs NDJSON for pipe reuse
- `set -euo pipefail` recommended for multi-step pipelines
- Do NOT parallelize writes to the same pipe (NDJSON collision risk)

## Install

```bash
# Option A: Via AI Agent (Kimi Code, Trae, etc.)
# Send this prompt to your AI assistant:
# "请帮我安装 LibTV CLI Skill：https://liblibai-web-static.liblib.cloud/cli/1.1.1/libtv-cli-skill.zip"

# Option B: Manual install
# Download and unzip the skill package, then run the install script:
bash scripts/install-libtv-cli.sh   # macOS/Linux
# or
powershell scripts/install-libtv-cli.ps1  # Windows
```

## AI Agent Integration

LibTV CLI is designed as a "Skill" package for AI coding assistants. Supported:
- Kimi Code/Claw
- MiniMax Agent
- 小龙虾
- Trae
- 腾讯云代码助手
- 通义灵码
- 文心快码

The Skill package contains full command docs in SKILL.md + examples/ directory, so the AI agent knows how to use `libtv` commands.