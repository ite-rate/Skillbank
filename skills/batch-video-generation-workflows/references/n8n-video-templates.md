# n8n Video Generation Templates — Full Inventory

As discovered on 2026-07-26 via https://n8n.io/workflows/?q=video+generation and ?q=bulk+video

## Batch-Specific Templates (4)

### 1. Bulk AI Video Generation with Freepik Minimax Hailuo & Google Suite Integration
- **Author**: Robert Breen (rbreen)
- **Date**: ~1 year ago
- **Cost**: Free
- **Nodes**: Google Sheets, HTTP Request, Google Drive, +1
- **Flow**: Reads video prompts from Google Sheet → calls Freepik Image-to-Video API (powered by Minimax Hailuo-02-768p) → generates multiple variations → async polling for completion → auto-uploads to Google Drive
- **Best for**: Batch generation with 海螺 model, Google Sheets-driven

### 2. Generate bulk Veo 3 videos from Google Sheets via Vertex AI
- **Author**: Salman Mehboob (salmanmehboob)
- **Date**: ~4 months ago
- **Cost**: Free
- **Nodes**: Google Sheets, HTTP Request, Google Drive
- **Flow**: Google Sheet with prompts + video settings + checkbox → sends to Google Veo 3 via Vertex AI → waits for generation → downloads to Drive
- **Best for**: Veo 3 batch generation, Google ecosystem

### 3. Fully Automated AI Video Generation & Multi-Platform Publishing
- **Author**: Juan Carlos Cavero Gracia (carlosgracia)
- **Date**: ~1 year ago
- **Cost**: Free
- **Nodes**: Google Sheets, HTTP Request, Google Drive, +3
- **Flow**: Takes ideas from Google Sheet → generates POV-style short-form videos using multiple AI services → auto-publishes across social media platforms
- **Best for**: End-to-end from idea to published video

### 4. Bulk Auto-Publish Videos to Social Networks with AI Copy and Client Approval
- **Author**: Juan Carlos Cavero Gracia (carlosgracia)
- **Date**: ~8 months ago
- **Cost**: Free
- **Nodes**: Google Sheets, Google Drive, Code, +4
- **Flow**: Fetches videos from Google Drive folder → AI generates platform-specific copy → approval queue in Google Sheets → batch publish
- **Best for**: Distribution phase after videos are already generated

## Other Video-Related Templates (8)

### 5. AI Virtual Try-On Image, Video Generation for Telegram, Discord & YouTube
- **Author**: AttenSys AI (attensys)
- **Date**: ~7 months ago
- **Nodes**: HTTP Request, Telegram, Discord, +1
- **Flow**: Upload dress image + fashion model image → generate try-on image → generate fashion walking video → share via Telegram/Discord/YouTube

### 6. Async Video Polling Engine — Background Job Handler for AI Video Generation
- **Author**: Joe V (joevenner)
- **Date**: ~6 months ago
- **Nodes**: HTTP Request, Redis, Telegram, +2
- **Flow**: Async polling engine for Veo, Sora & Seedance — companion to AI Shorts Reactor workflow
- **Note**: This is infrastructure, not a standalone generator

### 7. Automated News Video Generation with HeyGen AI, Apify, and GPT-4.1 Mini
- **Author**: Jadai kongolo (jadai-ai-automation)
- **Date**: ~9 months ago
- **Nodes**: HTTP Request, AI Agent, OpenRouter Chat Model
- **Flow**: Scrapes daily newsletter content → AI generates scripts → HeyGen avatar + voice produces video summaries

### 8. Recreate Instagram Reels with Gemini 2.0 Analysis & Minimax Video Generation
- **Author**: Aditya Malur (aditya-malur)
- **Date**: ~9 months ago
- **Nodes**: HTTP Request
- **Flow**: Download Instagram Reel → Gemini 2.0 video analysis → regenerate similar video with AI video generation

### 9. UGC Video Generation with Wan 2.5 on Replicate
- **Author**: Yaron Been (yaron-nofluff)
- **Date**: ~10 months ago
- **Nodes**: HTTP Request, Code
- **Flow**: Converts static images into dynamic videos using Wan 2.5 on Replicate — for product photos/marketing images

### 10. Automate AI video ad generation with Google Veo 3, Gemini, and Airtable
- **Author**: Intuz (intuz)
- **Date**: ~10 months ago
- **Nodes**: Airtable, HTTP Request, Code, +1
- **Flow**: Static product image + creative idea → Veo 3 generates video ad → downloadable file

### 11. Automate S3 Video Transcoding, Thumbnail Generation & CDN Distribution
- **Author**: Tomoki (tomoki)
- **Date**: ~7 months ago
- **Nodes**: Google Sheets, HTTP Request, Slack, +1
- **Flow**: Monitors S3 for uploads → thumbnails, preview clips, metadata extraction → transcodes to multiple formats → CDN distribution

### 12. Automated YouTube Video Scheduling & AI Metadata Generation
- **Author**: JPres (stardawnai)
- **Date**: ~1 year ago
- **Nodes**: HTTP Request, YouTube, Code, +3
- **Flow**: AI-generated descriptions/tags/scheduled releases for YouTube videos

## GitHub Projects — n8n Video Automation

| Repo | Stars | Description |
|------|-------|-------------|
| ezedinff/TikTok-Forge | 82 | Automated TikTok video generation pipeline |
| Hritikraj8804/Autotube | 53 | n8n + AI script gen + video processing → YouTube Shorts |
| theone-ctrl/ai-content-automation-n8n | 23 | End-to-end social media content automation with n8n |
| Awaisali36/ai-avatar-video-generation-system | 18 | n8n + RSS + Gemini + AI avatar for news videos |
| abhiii-22/n8n-VEO-Video-Idea-Prompt-Generator | 8 | Generate video ideas and VEO3 production prompts |
| Anil-matcha/n8n-nodes-seedance2 | 7 | n8n community node for ByteDance Seedance 2.0 (Text/Image-to-Video) |
| ariapioquinto/auto-veo3-generator | 7 | Claude + Airtable + FAL Veo 3 API |
| pilotwaffle/n8n-YouTube-Video-Generator-system | 4 | 4-phase AI YouTube video generation with n8n |

## GitHub Projects — Other Platforms

### Coze-related
| Repo | Stars | Description |
|------|-------|-------------|
| Dream-buider/video-automation-workflow-setup | 0 | Coze 短视频自动化工作流调试与交付 |
| redAntCpp/Novel2ShortVideo-Coze | 0 | Novel-to-short-video on Coze, full dev log |
| yuanyifan686/gouxue | 0 | Coze + Seedance 2.0 for short drama marketing |
| LinXingjian365/jimeng-video-workflow | 1 | 即梦/火山引擎 batch generation, auto-concat, progress notes |

### ComfyUI-related
| Repo | Stars | Description |
|------|-------|-------------|
| princepainter/ComfyUI-PainterNodes | 158 | Comprehensive: video gen, image editing, audio lip-sync, Flux/LTXV/Wan |
| alt-key-project/comfyui-dream-video-batches | 94 | Batch video generation nodes (SVD & AnimateDiff) |
| mikehalleen/the-halleen-machine | 16 | Agentic workflow management for ComfyUI video projects |

### Standalone Tools
| Repo | Stars | Description |
|------|-------|-------------|
| IgorShadurin/app.yumcut.com | 836 | AI video generator: prompt → vertical videos for TikTok/Reels/Shorts |
| trgkyle/veo-automation-user-guide | 38 | Chrome extension: batch video/image gen on Google VEO3 |
| cronux-ind/ai-video-generation-workflow | 7 | Finance explainer videos: script+slides+voice+subtitles+batch render |