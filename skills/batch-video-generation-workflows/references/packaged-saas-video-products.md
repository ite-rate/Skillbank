# Packaged SaaS Video Generation Products (China + International)

For users who want register-and-use products, not low-code workflow building.

## Chinese Products

### 腾讯智影 (Tencent ZenVideo)
- **What**: Digital human + AI video generation platform
- **Type**: SaaS, web-based
- **Key features**: Digital human口播, template-based video generation, batch generation (enterprise), custom avatar (e.g. company uniform), subtitle auto-generation
- **Ecosystem**: Tencent — best fit for 视频号 (WeChat Channels)
- **Trial**: WeChat mini-program "腾讯智影" — free tier available
- **Enterprise**: Custom digital human, batch API, enterprise pricing
- **Best for**: B2B product marketing videos for 视频号, 15s highlight videos, telecom/financial/government sales teams
- **URL**: https://zenvideo.qq.com (may require direct access; mini-program more reliable)

### 硅基智能 (GuijiAI)
- **What**: Enterprise digital human platform, API-first
- **Type**: SaaS + API
- **Key features**: Digital human batch video generation, custom avatar cloning, API integration for enterprise systems, multi-scenario templates
- **Typical clients**: China Mobile, China Construction Bank, government agencies — strong in regulated industries
- **Best for**: Large-scale batch generation (hundreds/thousands), API integration with CRM/marketing systems, industries with compliance requirements
- **Note**: More enterprise-oriented than 腾讯智影; higher volume, higher cost

### 即创 (Ocean Engine / 巨量引擎)
- **What**: AI creative production platform by ByteDance
- **Type**: SaaS
- **Key features**: AI video generation, digital human, image generation, copywriting, batch creative production
- **Ecosystem**: ByteDance — best fit for Douyin (抖音) advertising
- **Best for**: Douyin ad creatives, e-commerce product videos, performance marketing
- **URL**: https://aic.oceanengine.com
- **Note**: Skewed toward ad creative production rather than general marketing

### 度加剪辑 (Baidu DuJia)
- **What**: Baidu's AIGC creation platform
- **Type**: SaaS, web-based
- **Key features**: AI video editing, AI script generation, AI voiceover
- **Note**: More of an editing tool than a batch generation platform; limited batch capability

### 万兴播爆 Virbo
- **What**: Wondersshare's digital human video marketing tool
- **Type**: SaaS
- **Key features**: Multi-language digital human, batch generation, cross-border marketing focus
- **Best for**: Cross-border e-commerce, international marketing
- **Note**: Domestic B2B fit is mediocre; better for export-oriented businesses

## International Products

### HeyGen
- **What**: AI digital human video generator
- **Type**: SaaS + API
- **Key features**: Best-in-class digital human quality, 175+ language translation, talking photos, batch API
- **Pricing**: Free trial, then subscription tiers; enterprise pricing for API/batch
- **Best for**: Multi-language content, global brands, high-quality digital human
- **Limitation**: No Chinese platform integration (视频号/抖音); international pricing

### Synthesia
- **What**: AI video generation with avatars
- **Type**: SaaS
- **Key features**: 140+ languages, 230+ avatars, enterprise-focused
- **Best for**: Corporate training, internal comms, explainer videos
- **Limitation**: Less suited for short-form marketing; no Chinese ecosystem integration

## n8n Low-Code Workflow Taxonomy (for comparison)

Six complexity tiers, from simplest to most complex:

1. **Template-fill** (n8n + Creatomate): Fixed template, swap dynamic content via API. Best for structured marketing videos.
2. **AI full pipeline** (n8n + OpenAI + Flux + Kling + ElevenLabs + Creatomate): 8+ node chain. Best for faceless content matrix accounts. Overkill for product highlights.
3. **Long video multi-segment** (n8n + RunPod WAN 2.5 + Fal.ai FFmpeg): Segment-by-segment generation with frame continuity. For AI micro-films.
4. **Veo 3 cinematic** (n8n + Veo 3 + Sheets): Highest quality, highest cost. Scheduled autonomous generation.
5. **Vertical scenarios**: E-commerce product image→video, ASMR, children's stories, fashion — each has niche templates.
6. **Self-hosted FFmpeg** (n8n + Execute Command): Zero API cost, full control, requires server maintenance.

## Key Insight: SaaS vs Low-Code Equivalence

The core function of many SaaS products = the simplest n8n approach (template-fill):
- 腾讯智影/硅基智能 = n8n Path A (Creatomate template) but with Chinese-optimized digital humans, voice, and platform integration built in
- The difference is build-vs-buy: n8n gives flexibility, SaaS gives immediate usability
- For 15s product-highlight videos, SaaS is almost always the right choice unless the user has specific integration needs