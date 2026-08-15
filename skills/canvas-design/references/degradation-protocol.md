---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'ab01ac14-eafd-4002-823b-421f4e34c302'
  PropagateID: 'ab01ac14-eafd-4002-823b-421f4e34c302'
  ReservedCode1: 'f5a91b9d-16fe-476a-9aa3-5cdab9d6790d'
  ReservedCode2: 'f5a91b9d-16fe-476a-9aa3-5cdab9d6790d'
---

# Degradation Protocol

When the AI image generation service fails (rate limit, service unavailable, or other errors), follow this protocol.

## Step 1: Inform the User

Gently inform the user:

> "图片生成服务暂时不太稳定，是否需要我换用本地绘制的方式来为您生成？效果会略有不同，但依然会遵循您的设计哲学。"

## Step 2: Branch by User Choice

### If the user agrees → Local Canvas Fallback

Fall back to the local canvas creation method described in `references/canvas-creation-fallback.md`. This method generates the entire image from scratch using Python (Pillow), including both visual elements and text overlay. The design philosophy remains the guiding principle.

### If the user declines → Output Documents

Output the design philosophy (.md) and the assembled prompt, so the user can use them in their preferred image generation tool. The user does not leave empty-handed.

> AI生成