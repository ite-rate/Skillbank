---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '3c7d7597-eb41-48ec-920d-8b0f62d46859'
  PropagateID: '3c7d7597-eb41-48ec-920d-8b0f62d46859'
  ReservedCode1: '65cbb831-e415-45cd-93ec-f18094d6c061'
  ReservedCode2: '65cbb831-e415-45cd-93ec-f18094d6c061'
---

# Text Overlay Fallback Protocol

When the AI-generated image fails the text verification check (Step 2D), fall back to generating the image WITHOUT text and overlaying text locally using Pillow.

## When to Use

This protocol is triggered when:
- The vision model detects text errors in the initially generated image (wrong characters, missing strokes, garbled text, illegible words)
- The text content does not match what was specified in the prompt

## Steps

### 1. Regenerate Image Without Text

Re-assemble the same prompt assembled in Step 2B, but replace the text instruction block with the following text exclusion directive:

```
no text, no typography, no words, no letters, no characters, no writing in image
```

All other prompt components (subject, philosophy, composition, color, texture, artist anchor, aspect ratio) remain unchanged. Generate the image with the same model.

### 2. Overlay Text Locally with Pillow

Use Python PIL to overlay text elements onto the generated image.

**Font Selection:**
- Chinese text: ONLY use MiSans series fonts from the `./canvas-fonts` directory (MiSans-Regular, MiSans-Bold)
- English text: Use other fonts from `./canvas-fonts` directory (Instrument Sans, Instrument Serif, Work Sans, IBMPlexSerif, CrimsonPro, Lora, Gloock, YoungSerif, Tektur, PixelifySans, EricaOne, JetBrainsMono, etc.)
- Choose font weight based on the design philosophy's typography guidance

**Text Placement Philosophy:**
- Text should feel "discovered" within the image, not "pasted onto" it
- Position text at points of maximum stillness or visual quiet in the composition
- Text serves as a visual anchor, not an information carrier
- The design philosophy's typography guidance determines whether text is whisper-quiet or bold

**Spacing and Boundaries:**
- Nothing falls off the page, nothing overlaps — this is non-negotiable
- Every text element must be contained within the canvas boundaries with proper margins
- All text must have breathing room and clear separation from other elements
- Check carefully that text, graphics, and visual elements do not collide

**Text Content:**
- Keep text extremely minimal — only essential anchoring words or phrases
- Never use explanatory paragraphs
- If the user specified a title, place it with design-forward typography
- Subtle reference markers (coordinates, dates, catalog numbers) can be added as quiet labels

**Text Transparency:**
- Subtle text shadow can be added for depth (offset 1-2px, low alpha)
- Text alpha should typically be 150-220 (not fully opaque) to integrate with the visual
- Whisper-quiet labels can use alpha 60-100

**Semi-transparent Backdrop (if needed):**
- If the text area has too much visual complexity behind it, add a soft semi-transparent dark overlay before placing text
- Use `ImageDraw.rounded_rectangle` with fill like `(40, 30, 15, 55)` then `GaussianBlur(radius=18-20)`
- The backdrop should be subtle — barely noticeable, not a hard panel

### 3. Save the Result

Save the final composited image as .png alongside the design philosophy .md file.

### 4. Proceed to Step 3 (Refinement)

The image now follows the same refinement process as the primary path.

> AI生成