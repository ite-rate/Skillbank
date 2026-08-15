---
name: batch-video-generation-workflows
description: Use when researching batch AI video generation workflows.
level: manual
native_agent: Hermes
---

# Batch AI Video Generation Workflows

## When to use
- User wants to find, compare, or set up batch/bulk video generation workflows or tools
- User asks about automating short-form video creation (TikTok/Reels/视频号)
- User wants to know which platforms (n8n/Coze/ModelScope/ComfyUI) have mature video automation templates
- User wants to integrate AI video APIs (海螺/可灵/Veo/Seedance/即梦) into an automation pipeline
- User asks about **packaged SaaS products** for marketing video generation (腾讯智影/硅基智能/即创/HeyGen)
- User wants to compare low-code (n8n/Coze) vs ready-made products for video marketing

## First step: assess user's technical comfort
Ask or infer: does the user want to **build a workflow** (low-code: n8n/Coze/ComfyUI) or **use a packaged product** (SaaS: 腾讯智影/硅基智能/HeyGen)? Non-technical business/sales users almost always want the latter. Recommending n8n to someone who just wants 15s product-highlight videos is a mismatch — see Decision Framework below.

## Platform Overview (as of 2026-07)

### n8n — Most mature, free templates available
n8n community has ~12 video generation templates, 4 specifically for batch:
- **Bulk AI Video Generation with Freepik Minimax Hailuo** — Google Sheets → Freepik API (Hailuo-02) → async polling → Google Drive upload
- **Generate bulk Veo 3 videos from Google Sheets via Vertex AI** — Sheets prompt → Veo 3 → auto-download
- **Fully Automated AI Video Generation & Multi-Platform Publishing** — Sheets idea → POV shorts → auto-publish to social platforms
- **Bulk Auto-Publish Videos to Social Networks with AI Copy** — Drive folder → AI copy per platform → approval queue → publish
- See `references/n8n-video-templates.md` for full n8n template inventory with details
- See `references/packaged-saas-video-products.md` for Chinese & international SaaS products (腾讯智影/硅基智能/即创/HeyGen/etc.) and n8n workflow taxonomy comparison

Key n8n patterns:
- Google Sheets as the prompt/job queue driver
- HTTP Request node to call AI video APIs
- Async polling loop for video generation completion
- Google Drive for output storage
- Community nodes exist for Seedance 2.0 (Anil-matcha/n8n-nodes-seedance2)

### Coze (扣子) — Has workflow capability, fewer ready-made templates
- Coze store requires login to browse; no public "batch video" template found
- Can build workflows calling 即梦/可灵 plugins
- GitHub projects exist but are small/immature:
  - Dream-buider/video-automation-workflow-setup — Coze 短视频自动化工作流调试
  - redAntCpp/Novel2ShortVideo-Coze — novel→short video on Coze
  - yuanyifan686/gouxue — Coze + Seedance 2.0 for short drama marketing videos
  - LinXingjian365/jimeng-video-workflow — 即梦/火山引擎 batch generation

### ModelScope (魔搭) — Model hosting, no workflow templates
- Like HuggingFace for Chinese models; provides inference/deployment, not workflow orchestration
- No batch video generation workflow templates available

### ComfyUI — Local model batch generation
- alt-key-project/comfyui-dream-video-batches ⭐94 — SVD & AnimateDiff batch nodes
- princepainter/ComfyUI-PainterNodes ⭐158 — comprehensive toolkit incl. video gen, lip-sync
- Requires local GPU; higher technical barrier than API-based approaches

### LibTV (LiblibAI) — AI video creation platform with CLI batch capability
- **What**: LiblibAI (哩布哩布AI) is China's leading AI image/model community (like domestic Civitai); LibTV is their video creation platform
- **URL**: https://www.liblib.tv (main site) / https://www.liblib.tv/cli (CLI docs)
- **Positioning**: AI creative video generation — input inspiration → pick a Skill (preset workflow template) → generate video. NOT a digital-human口播 tool; more like MidJourney/可灵's video edition
- **Built-in Skills**: 皮克斯动画广告, 爆款拉片复刻, 新中式美学TVC, etc. Categories: 商业广告, 专业影视, 短剧漫剧, 动漫游戏, 教育生活
- **Pricing**: Membership-based, year card 4折 promo; free tier (~40 images or 2 videos)
- **Best for**: Brand-level creative videos (1-2 hero pieces), NOT for daily batch marketing video production (each requires prompt tuning, no obvious bulk UI)
- **BUT**: Has official CLI with batch capability — see LibTV CLI section below

### LibTV CLI — Official command-line tool for batch video generation
- **What**: `libtv` CLI operates LibTV canvas/projects/nodes/models from terminal
- **Install**: Download skill zip from `https://liblibai-web-static.liblib.cloud/cli/1.1.1/libtv-cli-skill.zip` — designed as a "Skill" for AI agents (Kimi Code, MiniMax Agent, Trae, 通义灵码, etc.)
- **Core concept**: Canvas = project file; Workspace = container for canvases; Nodes = text/image/video/audio/script/storyboard/video-clip
- **Batch mechanism**: NDJSON UNIX pipes (`libtv node "选题" | libtv node create "视频" ...`), group batch (`libtv group create 组名` → bind nodes → `libtv group 组名 --run`)
- **All-in-one**: `libtv node create "镜头A" -t video --prompt "..." --set "model=Seedance 2.0" --set modeType=text2video --set ratio=9:16 --set duration=5 --run`
- **Video models**: Seedance 2.0 (star-video2), Kling O1, etc. Modes: text2video, singleImage2video, mixed2video, frames2video, audio2video
- **Batch loop example**: `for topic in "卖点1" "卖点2" ...; do libtv node create "$topic" -t video --prompt "..." --set "model=Seedance 2.0" ... --run; done`
- **Supporting AI agents**: Kimi Code/Claw, MiniMax Agent, 小龙虾, Trae, 腾讯云代码助手, 通义灵码, 文心快码
- **See**: `references/libtv-cli-reference.md` for full command reference and batch patterns

### Dify — No video-specific workflow templates found
- General-purpose AI workflow platform but no video generation templates in community

## Low-Code vs Packaged SaaS — Choose the Right Tier First

**Critical**: Before recommending n8n/Coze/ComfyUI, assess whether the user wants a **low-code platform** (build it themselves) or a **packaged SaaS product** (register and use). Many users — especially non-technical business/sales users — want the latter and will explicitly reject low-code solutions ("n8n和coze本质上还是低代码").

### Packaged SaaS Products (register and use, no workflow building)

| Product | Type | Best For | Notes |
|---------|------|----------|-------|
| **腾讯智影** | Digital human + template | 视频号 marketing, B2B product highlights | Tencent ecosystem, Chinese digital humans, enterprise version supports batch + custom avatar. WeChat mini-program available for quick trial |
| **硅基智能** | Digital human, enterprise API | Large-scale batch, regulated industries | Used by China Mobile, banks, government. API-driven, can integrate with enterprise systems. Supports custom avatar (e.g. telecom uniform) |
| **即创 (巨量引擎)** | AI creative platform | Douyin ad creatives, e-commerce | ByteDance ecosystem, batch generation, but skewed toward performance ads |
| **HeyGen** | Digital human, international | Multi-language, global brands | Best quality digital humans, but expensive, no Chinese platform integration |
| **万兴播爆 Virbo** | Digital human | Cross-border marketing | Wondersshare product, decent but domestic B2B fit is mediocre |
| **Creatomate** | Video template API | Template-based batch generation (overseas) | Good for programmatic template filling, but Chinese voice/digital human support is weak. Often paired with n8n |

### Decision Framework

| User situation | Recommend |
|----------------|-----------|
| Non-technical, wants 15s product-highlight videos for 视频号 | **腾讯智影** (packaged, Tencent ecosystem) |
| Enterprise needs API-driven large-scale batch (e.g. telecom/banking) | **硅基智能** (enterprise digital human API) |
| Running Douyin ad campaigns | **即创** (ByteDance ecosystem) |
| Needs multi-language / global markets | **HeyGen** |
| Has technical skills, wants full control / custom pipeline | n8n / Coze / ComfyUI (see n8n paths below) |
| Wants template-filling approach with API integration | n8n + Creatomate (see n8n Path A below) |

## n8n Workflow Approaches (for users who DO want low-code)

### n8n Path A: Template-fill (Creatomate) — simplest, best for structured marketing videos
1. Design video template in Creatomate (dynamic text/image/video placeholders)
2. n8n HTTP Request → Creatomate API with dynamic data → render → poll status → download
3. Supports subtitle animation + ElevenLabs AI voiceover
4. Best match for B2B product-highlight videos (fixed template, swap copy per product)

### n8n Path B: AI Full Pipeline — hottest, most complex
Chain: Google Sheets → OpenAI (script) → Flux (image) → Kling/Runway (image-to-video) → ElevenLabs (voiceover) → Creatomate (compose) → Whisper (captions) → multi-platform publish
- **Warning**: 8+ node chain, high API cost, failure-prone. Add error handling + retry logic. Overkill for 15s single-highlight videos.

### n8n Path C: Google Sheets + 海螺 API (low barrier for 海螺 users)
1. Import "Bulk AI Video Generation with Freepik Minimax Hailuo" template from n8n.io/workflows
2. Configure Freepik API key (provides Hailuo-02-768p access)
3. Set up Google Sheet with prompt columns
4. Workflow auto-polls for completion and uploads to Drive
5. Pull from Drive into 剪映 for final edit

### n8n Path D: Seedance/即梦 API
1. Install n8n community node: `npm install n8n-nodes-seedance2`
2. Reference: Anil-matcha/n8n-nodes-seedance2 (⭐7) — Text-to-Video, Image-to-Video
3. Or use HTTP Request node to call 火山引擎 API directly
4. Drive with Google Sheets for batch job queue

### n8n Path E: Long video multi-segment (RunPod WAN 2.5 + Fal.ai FFmpeg)
- Google Sheet as "director storyboard": per-segment prompt, duration, start frame
- n8n generates each segment → extracts last frame as next segment's start image → Fal.ai FFmpeg merges
- For AI micro-films / coherent long-form content, NOT for 15s product highlights

### n8n Path F: Veo 3 cinematic quality
- Scheduled trigger → OpenAI Agent brainstorm → Veo 3 prompt → Veo 3 API → Google Drive
- Highest quality, highest cost. Overkill for short marketing videos.

### n8n Path G: Self-hosted FFmpeg (zero API cost, needs server)
- n8n Execute Command node runs FFmpeg directly
- Concat, subtitles, audio mix, transcode all possible
- Use SplitInBatches for batch rendering, control concurrency to avoid CPU/memory exhaustion

### Coze custom workflow
1. Build workflow in Coze with 即梦 plugin
2. No ready-made template — manual configuration needed
3. Better for interactive/iterative generation than pure batch

## Research Workflow (how to search these communities)
1. **n8n**: Browse https://n8n.io/workflows/?q=video+generation or ?q=bulk+video — templates are public, no login needed
2. **Coze**: Store requires login (火山引擎 account); search on coze.cn for video-related bots/workflows
3. **GitHub**: `curl "https://api.github.com/search/repositories?q=KEYWORDS&sort=stars"` — effective for finding projects
4. **ModelScope**: Search modelscope.cn — model-focused, not workflow-focused
5. **Chinese blogs**: Bing search with site:csdn.net OR site:zhihu.com for tutorials/walkthroughs
6. **Bing search tips**: Chinese queries with "即梦" get tokenized — use English model names (Seedance, Hailuo, Veo) for better results

## 15s Product-Highlight Video Format (B2B marketing)

For 15s product-highlight videos (e.g. telecom products: 云电脑/商务宽带/直播专线), the most effective formats are NOT digital-human-only口播. User feedback: "只有数字人是不是太单调了无法吸引眼球" — digital humans alone are too monotonous for 15s short videos.

### Effective 15s structures (by product type)

| Structure | Example | Tools |
|-----------|---------|-------|
| **大字报+动效+配音** | Big text pops: "上行对等100M!" → product screenshot → "直播不卡顿!" | 剪映 template / Creatomate / 腾讯智影 template mode |
| **产品录屏+标注动画** | Screen recording → arrow/circle annotation → voiceover | Screen record + 剪映 annotations |
| **对比反转式** | Left: "普通宽带: 直播卡成PPT" → Right: "电信专线: 丝滑4K" → product info | 剪映 split screen + text + voiceover |
| **数字人+B-roll混合** | Digital human 3s hook only → 12s product footage/data animation/scene | 腾讯智影 + 剪映 for B-roll edit |

### 15s B2B product video template

For each product, break into 5+ selling points, each = one 15s video:
- 0-3s: Pain point hook (visual + text)
- 3-13s: Product demo / data / comparison (screen recording or AI-generated visuals)
- 13-15s: CTA + brand info

### Batch production approach for non-technical users

1. **Fastest**: Make 1 template in 剪映 (大字报 style + AI voiceover + product image slot + BGM) → duplicate per selling point → swap copy + image → export. ~10 min per video.
2. **Semi-auto**: 腾讯智影 template mode (not digital human mode) — template fill, batch in enterprise version
3. **Full auto (technical)**: LibTV CLI batch loop or n8n + Creatomate

## Writing Prompts for SeedDance Mini 2.0 (豆包/字节)

SeedDance Mini 2.0 is the video generation model accessible via 豆包 (Doubao). When writing prompts for 10s single-scene marketing videos on this model:

### Principles
- **One scene, one continuous action** — SeedDance Mini's strength is single-shot camera + audio-visual sync. Multi-scene cuts in a 10s clip easily break.
- **Don't over-constrain** — write the scene setup, key visual beats, and brand elements, but leave specific dialogue and character details open for AI to fill. The user explicitly said "不要写的太死限制AI发挥".
- **Brand elements via subtitle text, not scene props** — e.g. add `画面底部滚过字幕"中国电信直播专线·上行450M稳如磐石"` rather than forcing logos into the scene description. User feedback: "不是说完全电信 而是台词或者文字 加上电信" — don't make it a Telecom ad set, just weave the brand in via text/字幕.
- **Audio-visual anchor points** — give SeedDance natural rhythm beats: an action → a visual reaction → a data change. E.g. "主播说到激动处拍了下桌子→弹幕刷过'画质真稳'→订单数字跳动".
- **Scene must match the product's real usage context** — user corrected: outdoor scenes for "直播专线" don't make sense because 专线 is for fixed locations. "不是户外 怎么用专线" — always ground the scene in where the product is actually installed/used.
- **Device reference via uploaded photo** — when the product is a physical device (e.g. 天翼AI云电脑 tablet), the user may upload a reference photo to 豆包. Write "设备参考我的附件" in the prompt and don't describe the device appearance — let the photo handle it.
- **Mode-switching products** — for products like 天翼AI云电脑 that switch between 云电脑/平板/AI学习机 modes, show the switch as an action sequence: mode A in use → 轻点切换 → mode B in use → 轻点切换 → mode C in use. Don't just list modes, show the transition.
- **Seasonal context** — user mentioned 暑假 (summer vacation) as timing. Weave seasonal cues naturally (暑假作业本, 暑假书店, etc.) when relevant.

### Prompt template for 10s single-scene B2B marketing video

```
[场景环境一句话: 时间+地点+氛围]. [人物角色]正在[核心动作], [画面中的数据/弹幕/反馈细节]. [品牌字幕: 画面底部滚过字幕"..."]. [音画锚点: 动作→反馈→数据变化]. [整体氛围+电影级画质+竖屏9:16].
```

### Example: 直播基地场景 (直播专线)
```
夜晚一座电商直播基地内，走廊两侧排列着多间透明玻璃直播间，每间直播间都在同时开播，不同主播各自对着镜头卖力讲解不同品类商品。走廊中央的监控墙上实时显示每间直播间的推流状态和在线人数，所有数据全绿稳定运行。一位基地运营人员走过走廊，扫了一眼监控墙满意地点了点头。画面底部滚过字幕"中国电信直播专线·多间并开稳如磐石"。整体灯光从各直播间透出来交织在走廊上，氛围繁忙有序，电影级画质，竖屏9:16。
```

### Example: 天翼AI云电脑一机多用 (暑假书房)
```
暑假白天一间书房里，书架上摆满了书，阳光从侧面照进来。一位年轻爸爸坐在书桌前，面前的设备参考我的附件，屏幕上显示着多窗口办公文档。他合上一份文件后轻点屏幕角落的切换按钮，界面瞬间从办公桌面变为平板娱乐模式，他随手刷了几下短视频。镜头一转，他上小学的女儿走过来坐到桌前，爸爸又轻点切换，界面变为AI学习机模式，女儿拿起设备对着一本暑假数学练习册拍照，屏幕上立即圈出错误题目并弹出知识点讲解，随后界面底部出现"学科网"等教育平台的教学资源入口。画面底部滚过字幕"天翼AI云电脑·办公娱乐学习三合一"。整体氛围温馨有序，电影级画质，竖屏9:16。
```

### Available platforms (confirmed accessible without VPN, as of 2026-07)
| Platform | URL | Notes |
|----------|-----|-------|
| 即梦 | jimeng.jianying.com | ByteDance, best Chinese prompt understanding, free daily credits, max 10s per generation |
| 可灵 | klingai.com | Kuaishou, high quality, free daily credits |
| Google AI Studio (Veo 3) | aistudio.google.com | ❌ times out without VPN in user's network |
| GoEnhance | goenhance.ai | Accessible, aggregates Veo 3/Kling/Sora 2, has free trial |

## Pitfalls
- **Assuming everyone wants low-code**: n8n/Coze are powerful but require workflow building. For non-technical users who just need 15s product-highlight videos, packaged SaaS (腾讯智影/硅基智能) is the right tier. User explicitly said "n8n和coze本质上还是低代码" — always assess technical comfort first
- **Recommending digital-human-only for 15s marketing videos**: Digital humans talking for 15s is monotonous and loses viewer attention. Use digital humans only as a 3s hook, then cut to product footage/data/comparison. User feedback: "只有数字人是不是太单调了无法吸引眼球"
- **Over-engineering simple video needs**: A 15s single-highlight product video does not need an 8-node AI pipeline (OpenAI→Flux→Kling→ElevenLabs→Creatomate→Whisper→publish). Template-fill or digital-human SaaS is sufficient
- **Confusing LibTV with 腾讯智影**: LibTV (liblib.tv) is LiblibAI's AI creative video platform (input prompt → AI generates cinematic visuals). 腾讯智影 is Tencent's digital human + template video tool. Different positioning — LibTV is for creative/brand videos, 腾讯智影 is for marketing/口播 videos
- **Outdoor scenes for fixed-line products**: 直播专线/商务宽带 are installed in fixed locations (直播间/办公室/直播基地). Don't put them in outdoor/scenic scenes — user corrected: "不是户外 怎么用专线". Always ground the scene in the product's actual installation context.
- **Over-stuffing brand into scene props**: Don't make every scene a Telecom store with logos everywhere. User said "不是说完全电信 而是台词或者文字 加上电信" — weave brand via subtitle text and natural UI elements, not forced set dressing.
- **Describing device appearance when user provides a reference photo**: If the user uploads a device photo to 豆包/即梦, write "设备参考我的附件" and don't describe the device's physical form — the photo handles it, text description conflicts with the reference image.
- Bing search for "即梦" returns dictionary results for the character 即 — use "jimeng" or "Seedance" instead
- Bing search results in this environment are poor for Chinese product queries — Chinese product names (硅基智能, 腾讯智影) get tokenized into individual characters. Use direct product URLs when possible, or rely on known knowledge
- Coze store (coze.cn/store) requires 火山引擎 login — cannot browse anonymously
- ModelScope is a model hub, not a workflow platform — don't expect workflow templates there
- n8n template URLs are not guessable from titles — search on n8n.io/workflows to find the actual URL
- Some n8n templates use Freepik as a proxy API for Hailuo — Freepik API key needed, not direct Hailuo key