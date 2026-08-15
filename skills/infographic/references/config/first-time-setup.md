---
name: first-time-setup
description: First-time setup flow for infographic preferences
---

# First-Time Setup

## Overview

When no EXTEND.md is found, ask for default preferences before generating any infographic. Saved preferences shift Step-3 recommendations and Step-4 defaults only — they never bypass Step 4 confirmation (see the `## Confirmation Policy` section in SKILL.md).

## Questions

**Language**: Use the user's input language for question text. Do not always default to English.

Ask the user all questions in one request when possible. Save the result to `infographic/EXTEND.md` under the workspace hidden directory, then continue to Step 1.2.

### Question 1: Preferred Layout

```
header: "Layout"
question: "Default layout preference?"
options:
  - label: "Auto-select (Recommended)"
    description: "Pick layout per content in Step 3"
  - label: "bento-grid"
    description: "Multiple topics, overview (general default)"
  - label: "linear-progression"
    description: "Timelines, processes, tutorials"
  - label: "dense-modules"
    description: "High-density modules, data-rich guides"
```

### Question 2: Preferred Style

```
header: "Style"
question: "Default visual style preference?"
options:
  - label: "Auto-select (Recommended)"
    description: "Pick style per tone in Step 3"
  - label: "craft-handmade"
    description: "Hand-drawn, paper craft (general default)"
  - label: "corporate-memphis"
    description: "Flat vector, vibrant"
  - label: "morandi-journal"
    description: "Hand-drawn doodle, warm Morandi tones"
```

### Question 3: Preferred Aspect

```
header: "Aspect"
question: "Default aspect ratio?"
options:
  - label: "Auto-select (Recommended)"
    description: "Pick per layout in Step 4"
  - label: "landscape"
    description: "16:9 (slides, blogs, web)"
  - label: "portrait"
    description: "9:16 (mobile, social, dense modules)"
  - label: "square"
    description: "1:1 (social, thumbnails)"
```

### Question 4: Language

```
header: "Language"
question: "Output language for infographic text?"
options:
  - label: "Auto-detect (Recommended)"
    description: "Match source content language"
  - label: "zh"
    description: "Chinese (中文)"
  - label: "en"
    description: "English"
```

## After Setup

1. Create the directory if needed
2. Write EXTEND.md using the schema in `references/config/preferences-schema.md`
3. Confirm: "Preferences saved to the workspace hidden directory."
4. Continue to Step 1.2

## Modifying Preferences Later

See the `## Changing Preferences` section in `SKILL.md` for the canonical list of common edits. Full schema: `references/config/preferences-schema.md`.
