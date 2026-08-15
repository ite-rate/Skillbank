---
name: canvas-design
description: Create beautiful visual art using design philosophy + AI image generation. When the user asks to create a poster, piece of art, design, or other static piece, use this skill. Creates original visual designs, never copying existing artists' work to avoid copyright violations.
level: manual
native_agent: TeleAgent
description_zh: 设计哲学驱动 + AI生图的高品质海报创作工具。先构思美学理念，再精准转化为AI提示词生成专业级视觉作品，支持降级到本地绘制。
name_zh: 创意海报设计
license: Complete terms in LICENSE.txt
---

These are instructions for creating design philosophies — aesthetic movements that are then EXPRESSED VISUALLY through AI image generation. Output only .md files, .pdf files, and .png files.

Complete this in four steps:
0. Interactive Q&A (gather poster requirements)
1. Design Philosophy Creation (.md file)
2. Philosophy-to-Prompt Translation (2A) + AI Image Generation (2C) + Text Verification (2D)
3. Refinement Pass

---

## STEP 0: INTERACTIVE Q&A

Before creating the design philosophy, gather key information from the user. The answers will serve as **constraints** for the design philosophy creation — they guide the aesthetic direction, not replace it.

### 5 Required Information Dimensions

| # | Question | Options |
|---|----------|---------|
| 1 | What is this poster for? | Brand campaign, Event promo, Product launch, Anniversary, Education/info, Custom |
| 2 | Who is the primary audience? | General public, Young people / Gen-Z, Industry professionals, High-end clients, Families, Custom |
| 3 | What style or feeling do you prefer? | Modern minimal, Warm & humanistic, Tech/futuristic, Classical elegance, Avant-garde/street, Retro/nostalgia, New Chinese ink, Cartoon/hand-drawn, Custom |
| 4 | What dominant color tone do you want? | Blue + white (professional trust), Deep blue + gold (premium authority), Dark + neon (trendy tech), Green + white (fresh natural), Warm orange + cream (friendly warmth), Custom |
| 5 | Where will this be published? | Event/movie poster (9:16), Xiaohongshu (3:4), WeChat article cover (21:9), Article illustration (16:9), Album cover (1:1), Custom (specify dimensions) |

### Interaction Rules

Present all 5 questions in a single batch — one AskUserQuestion call. Never ask one by one.

**For each question, pick 4 most relevant options based on the poster's theme, plus always include "Custom (describe yourself)" as the last option.** The full option catalog in the table above is for reference; show only the 4-5 that are most likely to match. If a question is already clearly answered in the user's initial input, skip it.

**Q5 exception**: Always ask Q5 unless the user explicitly names the target platform (e.g., "Xiaohongshu", "WeChat article cover"). "I want a poster" alone is not enough — poster could mean event poster (9:16), Xiaohongshu post (3:4), or WeChat cover (21:9), and the aspect ratio differs completely.

### How Answers Drive Philosophy Creation

The answers are not directly copied into the philosophy — they are **extended and transformed**:

| User says | Philosophy extends to |
|-----------|----------------------|
| "Techy" | "Kinetic Dawn" — industrial geometry, diagonal acceleration, hard-edged chromatic bands |
| "Artsy & quiet" | "Textural Quiet" — paper grain, soft light, atmospheric breathing room, layered visual poetry |
| "Blue dominant" | Philosophy specifies the exact blue range: "navy, cobalt, slate" rather than just "blue" |
| "For young people" | Philosophy adjusts rhythm toward kinetic, high-contrast rather than subdued |
| "Minimalist focus" | Spatial Strategy locked to Single Focal Point — philosophy emphasizes solitude, vast negative space, one dominant subject |
| "Layered depth" | Spatial Strategy locked to Atmospheric Layered — philosophy emphasizes layered depth, foreground/midground/background, atmospheric haze |
| "Radiant burst" | Spatial Strategy locked to Radiant Centrifugal — philosophy emphasizes radiating outward, explosive center, kinetic pulse |

The philosophy INFORMS the design; the user's answers CONSTRAIN the philosophy. Both must align.

---

## STEP 1: DESIGN PHILOSOPHY CREATION

Create a VISUAL PHILOSOPHY from user's Step 0 answers — aesthetic movement expressed through form, space, color, composition. 90% visual design, 10% essential text.

**Name the movement** (1-2 words), then write 4-6 paragraphs of poetic manifesto.

**CRITICAL GUIDELINES:**
- **ANCHOR TO CONCRETE SUBJECTS WITH FULL VISUAL SPECIFICATION**: Every philosophy MUST include a **concrete visual anchor** that provides not just WHAT is seen, but enough rendering detail to feed prompt construction directly. The anchor must cover four inseparable layers:
    - **Subject** — the recognizable, namable thing (e.g., "a solitary clock tower")
    - **Subject Detail** — 1-2 material/trait specifics (e.g., "weathered granite facade, ornate iron clock hands frozen at 6:47")
    - **Environment** — the surrounding scene (e.g., "emerging from a mist-filled valley, distant mountain silhouettes fading to pale grey")
    - **Surface Quality** — the physical feel of the image surface (e.g., "visible paper grain, slight ink bleed at the tower's edges")
  Pure atmosphere without subject is not a philosophy — it is a mood board.  **DECLARE SPATIAL STRATEGY**: Every philosophy MUST explicitly commit to exactly ONE of the three proven prompt patterns as its spatial strategy. This declaration must appear as a clearly labeled line in the philosophy, using this exact format:

  `Spatial Strategy: [Single Focal Point | Atmospheric Layered | Radiant Centrifugal]`

  The philosophy's spatial descriptions (space, rhythm, visual weight) must then be **consistent with** the declared strategy — do not write "vast negative space" while declaring Radiant Centrifugal, or "radiating outward" while declaring Single Focal Point. If the philosophy's temperament spans two strategies, pick the dominant one and mention the secondary impulse as a modifier in the philosophy text (e.g., "with subtle kinetic undertone" for a Single Focal Point philosophy that hints at energy).

  | Strategy | Philosophy must emphasize | Forbidden phrases |
  |----------|--------------------------|-------------------|
  | **Single Focal Point** | Solitude, emptiness, one subject, vast breathing space, negative space | "layered depth", "radiating", "expanding", "outward" |
  | **Atmospheric Layered** | Layered depth, foreground/midground/background, atmospheric haze, breathing room | "solitary", "radiating", "explosive", "kinetic pulse" |
  | **Radiant Centrifugal** | Radiating outward, explosive center, kinetic pulse, diagonal arcs, expanding energy | "vast negative space", "quiet contemplation", "stillness" |

  This declaration is read during 2A extraction to select the matching prompt template — no keyword matching or subjective judgment needed.

### PHILOSOPHY EXAMPLES

**"Concrete Poetry"**

**Spatial Strategy**: Single Focal Point

**Visual Anchor**: A solitary monumental form — a single sculptural block of rough-hewn concrete, weathered surface with visible aggregate grain, standing alone in a vast empty plaza under harsh overhead light, subtle vignette darkening the edges of the frame

**Philosophy**: Communication through monumental form and bold geometry. Massive color blocks, sculptural typography (huge single words, tiny labels), Brutalist spatial divisions, Polish poster energy meets Le Corbusier. Ideas expressed through visual weight and spatial tension, not explanation. Text as rare, powerful gesture — never paragraphs, only essential words integrated into the visual architecture.

**Color Direction**: burnt orange, black, cream, charcoal grey

**Craft Standard**: Every element placed with the precision of a master craftsman. Meticulously crafted, the product of countless refinements.

---

**"Urban Strata"**

**Spatial Strategy**: Atmospheric Layered

**Visual Anchor**: A figure on a wet sidewalk in the foreground — one hand raised to hail a taxi, coat collar turned up against drizzle, rain-slicked pavement reflecting amber streetlight — midground of blurred yellow headlights cutting through evening fog between steel-and-glass towers, background of distant skyscraper silhouettes dissolving into a gradient of slate grey mist and amber haze — risograph grain throughout, paper texture visible in the fog zones

**Philosophy**: Depth as information hierarchy. Foreground sharp and human-scale — the individual, the gesture, the immediate. Midground softened into motion — lights, reflections, the city's pulse rendered as translucent veils. Background dissolved to atmosphere — architecture reduced to silhouette, scale reduced to feeling. Each plane tells a different temperature of the same city. Typography understated — small sans-serif labels anchoring each depth zone. Ideas encoded spatially: foreground urgency, midground rhythm, background memory.

**Color Direction**: slate grey, amber gold, steel blue, mist white

**Craft Standard**: Each atmospheric plane calibrated with architectural precision. Meticulously crafted, the product of deep expertise in spatial orchestration.

---

**"Chromatic Detonation"**

**Spatial Strategy**: Radiant Centrifugal

**Visual Anchor**: A single electric guitar silhouette at absolute center frame, its strings mid-vibration with visible motion blur streaks, concentric rings of neon light expanding outward from the instrument's body in cyan-to-magenta arcs, diagonal speaker-stack lines radiating toward all four edges — screen print aesthetic with slight color misregistration between layers, halftone dots visible at the periphery

**Philosophy**: Pure kinetic release. Sound visualised as chromatic shockwave radiating from a single explosive center. Diagonal acceleration, expanding arcs, outward pulse in every element. Color as energy vector — cyan and magenta colliding at supersonic speed. Typography dynamic but sparse — single bold word locked into the radial geometry. Screen print grit amplifies the rawness.

**Color Direction**: cyan, magenta, electric yellow, deep black

**Craft Standard**: Every line radiating with the precision of a shockwave captured mid-burst. Meticulously crafted, the product of master-level kinetic control.

*Examples above are condensed. Actual philosophy should be 4-6 substantial paragraphs. Output as .md file.*

### Philosophy Output Format

Every philosophy .md file MUST follow this fixed section structure:

```markdown
# [Philosophy Name]

**Spatial Strategy**: [Single Focal Point | Atmospheric Layered | Radiant Centrifugal]

## Visual Anchor
[The single source of truth for prompt construction. Must cover four layers: Subject + Subject Detail + Environment + Surface Quality. E.g., "A weathered stone clock tower with ornate iron hands frozen at dusk, emerging from a mist-filled valley with distant mountains fading to pale grey, visible paper grain and slight ink bleed at edges"]

## Philosophy
[4-6 paragraphs of aesthetic manifesto, covering space & form, color & material, scale & rhythm, composition & balance, visual hierarchy. This is the free-form poetic heart of the document.]

## Color Direction
[Specific color names listed, e.g., slate blue, jade green, moss green, chalk white. Must use precise names — no vague descriptors like "blue-green tones".]

## Craft Standard
[Craftsmanship emphasis — e.g., "meticulously crafted, the product of deep expertise, painstaking attention, master-level execution." Restate at least twice that the work must appear as though it took countless hours by someone at the absolute top of their field.]
```

---

## STEP 2: PHILOSOPHY-TO-PROMPT TRANSLATION + AI IMAGE GENERATION + TEXT VERIFICATION

With the philosophy established, translate it into a structured AI image generation prompt, generate the image (with text), then verify text correctness via vision model.

### 2A: PHILOSOPHY-TO-PROMPT TRANSLATION

The design philosophy must be systematically converted into prompt components. Follow this mapping:

#### Subject Extraction (DO THIS FIRST)
Extract primary subject from the Visual Anchor. If none, STOP — revise philosophy.
- "A clock tower silhouette against dawn sky" → `a clock tower silhouette against dawn sky`

#### Color Extraction
Extract precise color names from philosophy's Color Direction:
- "Mineral palette: slate, jade, moss, chalk" → `limited palette: slate blue, jade green, moss green, chalk white`

#### Composition Extraction
Extract composition keywords from philosophy's spatial descriptions:
- "Vast breathing space" → `dramatic negative space, minimal elements, breathing room`

#### Texture & Material Extraction
Extract finish keywords from philosophy's material descriptions:
- "Paper grain, ink bleeds" → `paper texture grain, ink bleed effect, risograph printing`

#### Subject Detail Extraction
Extract the subject's distinctive features from the Visual Anchor's second layer — material, scale, or defining trait. The philosophy's anchor now contains this directly; read it out, don't invent:
- Anchor: "weathered stone clock tower, ornate iron hands frozen at 6:47" → Subject: `a clock tower`. Detail: `weathered stone facade, ornate iron clock hands frozen at 6:47`

#### Environment Extraction
Extract the surrounding scene from the Visual Anchor's third layer:
- Anchor: "emerging from a mist-filled valley, distant mountain silhouettes fading to pale grey" → `mist-filled valley, distant fading mountain silhouettes`

#### Fine Details Extraction
Extract micro surface elements from the Visual Anchor's fourth layer (Surface Quality):
- Anchor: "visible paper grain, slight ink bleed at tower edges" → `paper fiber texture, ink bleed effect at edges`

#### Artist / Style Anchors (Optional)

**NEVER rely solely on an artist name. The prompt must carry the full visual specification from the philosophy.**

#### Q3 → Artist Mapping

Q3 answer maps to a master pool. Select 1-2 masters from the pool whose visual temperament best matches the philosophy text. Single-master styles → pick the one. Custom → match user description to closest row, then select within pool.

**Selection within a pool** — match philosophy emphasis to master tendency:
- Geometric/precise/austere → pick the architectonic master
- Organic/metaphoric/playful → pick the lyrical master
- Raw/kinetic/emotional → pick the expressive master

**Cross-style blending** (user wants two styles) → pick 1 master from each pool, combine their visual anchors.

| Q3 Option | Master Pool |
|-----------|-------------|
| Modern minimal | Saul Bass (symbolic metaphor), Olly Moss (visual pun, playful), Josef Müller-Brockmann (Swiss grid, geometric), Dan McCarthy (geometric abstraction, ultra-flat) |
| Warm & humanistic | Drew Struzan (painted realism), Paula Scher (typographic maximalism, vibrant) |
| Tech/futuristic | Kilian Eng (organic sci-fi, atmospheric), Cassandre (geometric futurism, monumental) |
| Classical elegance | Alphonse Mucha (Art Nouveau curves), Martin Ansin (Art Deco precision, refined vintage) |
| Avant-garde/street | Shepard Fairey (propaganda, stencil), Jock (expressive brushwork, kinetic comic) |
| Retro/nostalgia | Tadanori Yokoo (Japanese psychedelic pop collage) |
| New Chinese ink | Huang Hai (ink wash poetic minimalism) | 
| Cartoon/hand-drawn | Hayao Miyazaki (hand-drawn whimsical naturalism)| 
**On-demand artist detail loading**: After selecting, read only the chosen 1-2 `references/artists/{name}.md` files. File mapping:

| Artist | File |
|--------|------|
| Saul Bass | `saul-bass.md` |
| Olly Moss | `olly-moss.md` |
| Josef Müller-Brockmann | `josef-muller-brockmann.md` |
| Dan McCarthy | `dan-mccarthy.md` |
| Drew Struzan | `drew-struzan.md` |
| Paula Scher | `paula-scher.md` |
| Kilian Eng | `kilian-eng.md` |
| Cassandre | `cassandre.md` |
| Alphonse Mucha | `alphonse-mucha.md` |
| Martin Ansin | `martin-ansin.md` |
| Shepard Fairey | `shepard-fairey.md` |
| Jock | `jock.md` |
| Tadanori Yokoo | `tadanori-yokoo.md` |
| Huang Hai | `huang-hai.md` |
| Hayao Miyazaki | `hayao-miyazaki.md` |

#### Pattern Extraction
Read the philosophy's `Spatial Strategy` line — pick the matching template directly. No keyword matching.

| Label | Core Structure | Colors |
|-------|---------------|--------|
| **Single Focal Point** | Single center element + vast negative space + minimal visual interference | 2-3 |
| **Atmospheric Layered** | Foreground subject + simplified midground/background + 3-4 colors creating spatial atmosphere | 3-4 |
| **Radiant Centrifugal** | Central burst point + outward-expanding elements + diagonal/arc rhythm | 3-4 |

If Spatial Strategy declaration is missing (shouldn't happen), match to closest pattern by philosophy's space/rhythm/weight descriptions.

Fill the chosen template:

Single Focal Point:
```
[SUBJECT]. With [SUBJECT DETAIL],
in [minimal breathing room, vast negative space surrounding],
[COMPOSITION: centered isolation, dramatic emptiness, horizontal balance],
in [PHILOSOPHY NAME] style, [ARTIST ANCHOR if applicable],
[2-3 COLOR PALETTE], [TEXTURE/MATERIAL],
[FINE DETAILS: surface grain, subtle patina, edge vignette],
[single MOOD keyword],
[ASPECT RATIO]
```

Atmospheric Layered:
```
[SUBJECT]. With [SUBJECT DETAIL],
in [ENVIRONMENT: foreground sharp / midground soft / background mist],
[COMPOSITION: layered depth, atmospheric haze between planes],
in [PHILOSOPHY NAME] style, [ARTIST ANCHOR if applicable],
[3-4 COLOR PALETTE], [TEXTURE/MATERIAL],
[FINE DETAILS: light diffusion, softened edges at depth transitions],
[MOOD/TONE],
[ASPECT RATIO]
```

Radiant Centrifugal:
```
[SUBJECT]. With [SUBJECT DETAIL],
in [ENVIRONMENT: energy radiating outward from central burst point],
[COMPOSITION: radial from center, diagonal arcs, expanding concentric elements],
in [PHILOSOPHY NAME] style, [ARTIST ANCHOR if applicable],
[3-4 COLOR PALETTE], [TEXTURE/MATERIAL],
[FINE DETAILS: motion blur at periphery, light ray artifacts, kinetic energy trails],
[MOOD/TONE],
[ASPECT RATIO]
```

### 2B: PROMPT STRUCTURE

**Prompt Writing Rules:**
- **Be specific, never vague**: "Japanese-style fresh look" instead of "pretty style"; "students in school uniforms reading in the library" instead of "students doing things"
- **Core triad always complete**: Subject + Position + Action — all three required, or AI produces a floating generic figure
- **1-2 key details per field, no more**: one distinctive feature for subject, one atmosphere detail for scene. Overstacking scatters AI attention
- **Style-content alignment**: ancient ink subject ≠ cyberpunk backdrop; rustic nature ≠ neon lights. Every field must cohere
- **Composition matches intent**: close-up for detail, wide shot for scene. Don't use panorama when you want portrait intimacy

Assemble the prompt using this 8-layer structure. Each field carries one responsibility; don't merge or skip:

```
[SUBJECT] — the concrete visual anchor, what to shoot. With [SUBJECT DETAIL] — 1-2 distinctive features: material, scale, defining trait,
in [ENVIRONMENT / SCENE] — where the subject is, atmosphere that surrounds it,
[COMPOSITION + ANGLE] — framing, camera distance, spatial layout,
in [PHILOSOPHY NAME] style, [ARTIST ANCHOR if applicable],
[COLOR PALETTE] — precise color names,
[TEXTURE/MATERIAL] — surface finish, print quality,
[FINE DETAILS] — 1-2 micro elements: film grain, paper patina, subtle vignette, lighting nuance,
[MOOD/TONE],
[ASPECT RATIO]
```

**CRITICAL — TEXT INCLUSION**: The prompt MUST ALWAYS include a text instruction block that specifies what text should appear in the image. This replaces the old "no text" approach. Structure the text instruction as follows:

```
with text: "[EXACT TEXT CONTENT]" as [TYPOGRAPHY DESCRIPTION — style, position, scale, color],
```

Examples:
- `with text: "Renji Hospital" as large elegant serif title in warm gold, centered upper portion`
- `with text: "METROPOLIS" as bold condensed type at top, "2024" as small label at bottom`
- `with text: "Benevolent Healing" as subtle light-weight subtitle below main title, in muted champagne tone`

**Text instruction rules:**
- Specify the EXACT text content in quotes — character by character, no approximations
- Describe the typography style (serif/sans, weight, color) and approximate position
- If multiple text elements exist, list each one separately
- The text should feel integrated into the composition, not floating on top — describe it as part of the visual architecture

**Self-Check** (go through each item; fix if missing. Does not change philosophy direction):

| # | Check Item | Pass Criteria | Remedy if Missing |
|---|-----------|---------------|-------------------|
| 0 | **Subject present** | Does the prompt start with a concrete, recognizable noun-phrase subject? Not pure atmosphere. | Re-read philosophy's visual anchor, extract as subject; if none, revise philosophy first |
| 1 | **Subject detail** | Is there 1-2 distinctive features (material / scale / defining trait) after the subject? Not just subject name alone. | Derive from philosophy's visual anchor description; add e.g. "weathered stone surface", "rough calloused palms" |
| 2 | **Environment present** | Is there a scene/backdrop surrounding the subject? Not floating in void. | Derive from philosophy's spatial descriptions and mood |
| 3 | **Symbolic element** | Has core visual metaphor from philosophy been translated into a concrete image element? | Re-read philosophy, find key metaphor, concretize as visible element |
| 4 | **Color precision** | Are colors specified with concrete names (amber gold, burnt sienna) not vague ("warm tones")? At least one cool-color anchor present? | Replace vague color words with specific names; add cool anchor if missing |
| 5 | **Texture consistency** | Is the materiality from the philosophy reflected in the prompt? | Translate material descriptions into texture keywords |
| 6 | **Fine details** | Are there 1-2 micro surface elements (grain / patina / vignette / light nuance)? | Derive from texture: paper → fiber texture; screen print → halftone dots; aged → scratches, vignette |
| 7 | **Text instruction** | Does the prompt contain `with text: "..."` with precise content and layout? | Append text instruction block |
| 8 | **Style-content coherence** | Do subject, environment, and style all belong to the same world? No ancient scholar in cyberpunk city. | Fix the conflicting element to match the dominant aesthetic direction |

**Pixel Size**: Use Q5 answer to determine dimensions. **Never pass a ratio string like `9:16` as the size parameter.**

| Platform (Q5) | Ratio | Pixel Size (W×H) |
|---------------|-------|--------------------|
| Event/movie poster | 9:16 | 1440×2560 |
| Xiaohongshu | 3:4 | 1680×2240 |
| WeChat article cover | 21:9 | 2240×960 |
| Article illustration | 16:9 | 2560×1440 |
| Album cover | 1:1 | 2048×2048 |
| Custom | — | Use user-specified dimensions |

**Constraints**: Total pixels within [3,686,400 – 16,777,216]; ratio (w/h) within [1/16 – 16].

### 2C: AI IMAGE GENERATION

**If the AI image generation succeeds** → proceed to Step 2D (Text Verification).

**If the AI image generation fails** → follow the degradation protocol in `references/degradation-protocol.md`.

**About AI image watermarks**: Text-to-image models (e.g., Seedream) automatically add "AI Generated" watermark labels to generated images. This is built-in compliance behavior and is expected. **Do not attempt to remove, crop, or mask the watermark.**

### 2D: TEXT VERIFICATION

After the image is generated, use the vision model to verify whether all text elements in the image are correct. The verification uses a **two-stage isolation process** to prevent confirmation bias — the vision model must first read the text without knowing what to expect, and only then compare its independent reading against the expected text.

#### Stage 1: Blind Identification

Send the generated image to the vision model with the following prompt. **Do NOT include any expected text in this stage.**

```
Carefully identify all text in this image.
Requirements:
1. List every character you see, in top-to-bottom, left-to-right order
2. Only report characters you can confidently identify — do not guess or fill in gaps
3. If a character is blurry, deformed, has missing strokes, or cannot be confirmed, mark it as
   [BLURRY] and describe the shape you see (how many horizontal/vertical strokes, what radical it resembles)
4. Do not assume what the text should say — only report what you actually see
```

Record the complete output of Stage 1. This output becomes the input for Stage 2.

#### Stage 2: Independent Comparison

Using the Stage 1 output as input (do NOT re-examine the image), compare against the expected text:

```
Below is the text independently identified from the image in Stage 1:
[STAGE 1 FULL OUTPUT]

Below is the expected text that should appear:
- [EXPECTED TEXT 1]: [exact content]
- [EXPECTED TEXT 2]: [exact content]
...

Compare the identification results against the expected text character by character, marking each match and mismatch.
Pay special attention to:
- Common error types in AI-generated text: added/missing strokes, component substitution, look-alike character confusion
- Characters marked [BLURRY] in Stage 1 are highly likely to have generation errors — flag them as suspected errors
- Do not default to "correct" — only mark as matching when you are confident every stroke is right
- Any discrepancy between the identification and expected text (even a single stroke difference) must be explicitly flagged
Final conclusion: All text correct / The following text has errors (list differences character by character)
```

#### Decision Logic

| Stage 2 Result | Action |
|----------------|--------|
| **All text correct** | Output the image directly → skip to Step 3 (Refinement Pass) |
| **Text has errors** | Trigger fallback → execute the text overlay fallback process in `references/text-overlay-fallback.md` |
| **Stage 1 cannot identify any text** | Trigger fallback → execute the text overlay fallback process in `references/text-overlay-fallback.md` |

Falling back to text-free generation + local text overlay guarantees correct text.

---

## STEP 3: REFINEMENT PASS

After image produced, run one mandatory refinement pass — review the image and apply targeted prompt adjustments. Modify surgically: change only what needs improvement, preserve what works. Re-run Step 2D text verification after each regeneration.

**Fallback paths**: See `references/text-overlay-fallback.md`, `references/canvas-creation-fallback.md`, `references/degradation-protocol.md`.

**Always check**: color palette cohesive? composition balanced? central visual metaphor effective? typography integrated?

**When using the vision model to review**: Prepend this instruction: "Ignore the 'AI Generated' watermark label in the corner — it is automatically added by the image generation tool and cannot be removed. Do not flag it as a text error or design defect."

---

## MULTI-PAGE OPTION

To create additional pages when requested, create more creative pages along the same design philosophy but distinctly different. Bundle those pages in the same .pdf or many .pngs. Treat the first page as just a single page in a whole coffee table book waiting to be filled. Make the next pages unique twists and memories of the original. Have them almost tell a story in a very tasteful way. Exercise full creative freedom.
