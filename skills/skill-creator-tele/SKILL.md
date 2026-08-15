---
name: skill-creator-tele
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends LLM's capabilities with specialized knowledge, workflows, or tool integrations.
level: auto
native_agent: TeleAgent
description_zh: 手把手引导用户从零创建或迭代 AI 技能，精准应对各类场景。只需描述需求，它将引导你完成技能的创作或优化。
name_zh: 技能孵化器
license: Complete terms in LICENSE.txt
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend LLM's capabilities by providing
specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific
domains or tasks—they transform LLM from a general-purpose agent into a specialized agent
equipped with procedural knowledge that no model can fully possess.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else LLM needs: system prompt, conversation history, other Skills' metadata, and the actual user request.

**Default assumption: LLM is already very smart.** Only add context LLM doesn't already have. Challenge each piece of information: "Does LLM really need this explanation?" and "Does this paragraph justify its token cost?"

Prefer concise examples over verbose explanations.

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

**High freedom (text-based instructions)**: Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

**Medium freedom (pseudocode or scripts with parameters)**: Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

**Low freedom (specific scripts, few parameters)**: Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

Think of LLM as exploring a path: a narrow bridge with cliffs needs specific guardrails (low freedom), while an open field allows many routes (high freedom).

### Anatomy of a Skill

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   ├── description: (required)
│   │   ├── name_cn: (required, frontend display only)
│   │   ├── description_cn: (required, frontend display only)
│   │   └── create_source: (optional, auto-added by initializer for newly created skills)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

#### SKILL.md (required)

Every SKILL.md consists of:

- **Frontmatter** (YAML): Must include `name`, `description`, `name_cn`, and `description_cn`. LLM trigger logic reads `name` and `description`, while `name_cn` and `description_cn` are required for frontend display only.
- **Source marker** (`create_source`, optional): For newly created skills initialized via `scripts/init_skill.py`, the initializer auto-adds `create_source: super-agent-skill-creator` to frontmatter. Existing skills being modified are not required to add this field. Treat this field as metadata only and do not edit it unless the user explicitly asks.
- **Body** (Markdown): Instructions and guidance for using the skill. Only loaded AFTER the skill triggers (if at all).

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

Executable code (Python/Bash/etc.) for tasks that require deterministic reliability or are repeatedly rewritten.

- **When to include**: When the same code is being rewritten repeatedly or deterministic reliability is needed
- **Example**: `scripts/rotate_pdf.py` for PDF rotation tasks
- **Benefits**: Token efficient, deterministic, may be executed without loading into context
- **Note**: Scripts may still need to be read by LLM for patching or environment-specific adjustments

##### References (`references/`)

Documentation and reference material intended to be loaded as needed into context to inform LLM's process and thinking.

- **When to include**: For documentation that LLM should reference while working
- **Examples**: `references/finance.md` for financial schemas, `references/mnda.md` for company NDA template, `references/policies.md` for company policies, `references/api_docs.md` for API specifications
- **Use cases**: Database schemas, API documentation, domain knowledge, company policies, detailed workflow guides
- **Benefits**: Keeps SKILL.md lean, loaded only when LLM determines it's needed
- **Best practice**: If files are large (>10k words), include grep search patterns in SKILL.md
- **Avoid duplication**: Information should live in either SKILL.md or references files, not both. Prefer references files for detailed information unless it's truly core to the skill—this keeps SKILL.md lean while making information discoverable without hogging the context window. Keep only essential procedural instructions and workflow guidance in SKILL.md; move detailed reference material, schemas, and examples to references files.

##### Assets (`assets/`)

Files not intended to be loaded into context, but rather used within the output LLM produces.

- **When to include**: When the skill needs files that will be used in the final output
- **Examples**: `assets/logo.png` for brand assets, `assets/slides.pptx` for PowerPoint templates, `assets/frontend-template/` for HTML/React boilerplate, `assets/font.ttf` for typography
- **Use cases**: Templates, images, icons, boilerplate code, fonts, sample documents that get copied or modified
- **Benefits**: Separates output resources from documentation, enables LLM to use files without loading them into context

#### What to Not Include in a Skill

A skill should only contain essential files that directly support its functionality. Do NOT create extraneous documentation or auxiliary files, including:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- etc.

The skill should only contain the information needed for an AI agent to do the job at hand. It should not contain auxilary context about the process that went into creating it, setup and testing procedures, user-facing documentation, etc. Creating additional documentation files just adds clutter and confusion.

### Progressive Disclosure Design Principle

Skills use a three-level loading system to manage context efficiently:

1. **Metadata (name + description)** - Always in context (~100 words)
2. **SKILL.md body** - When skill triggers (<5k words)
3. **Bundled resources** - As needed by LLM (Unlimited because scripts can be executed without reading into context window)

#### Progressive Disclosure Patterns

Keep SKILL.md body to the essentials and under 500 lines to minimize context bloat. Split content into separate files when approaching this limit. When splitting out content into other files, it is very important to reference them from SKILL.md and describe clearly when to read them, to ensure the reader of the skill knows they exist and when to use them.

**Key principle:** When a skill supports multiple variations, frameworks, or options, keep only the core workflow and selection guidance in SKILL.md. Move variant-specific details (patterns, examples, configuration) into separate reference files.

**Pattern 1: High-level guide with references**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

LLM loads FORMS.md, REFERENCE.md, or EXAMPLES.md only when needed.

**Pattern 2: Domain-specific organization**

For Skills with multiple domains, organize content by domain to avoid loading irrelevant context:

```
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

When a user asks about sales metrics, LLM only reads sales.md.

Similarly, for skills supporting multiple frameworks or variants, organize by variant:

```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

When the user chooses AWS, LLM only reads aws.md.

**Pattern 3: Conditional details**

Show basic content, link to advanced content:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

LLM reads REDLINING.md or OOXML.md only when the user needs those features.

**Important guidelines:**

- **Avoid deeply nested references** - Keep references one level deep from SKILL.md. All reference files should link directly from SKILL.md.
- **Structure longer reference files** - For files longer than 100 lines, include a table of contents at the top so LLM can see the full scope when previewing.

## Skill Creation Process

**Skill storage directory (strict constraint)**

Use `SKILL_STORAGE_DIR` as the single working location for skill creation/modification.

At the start of every skill creation/modification task, resolve `SKILL_STORAGE_DIR` from scratch. Always read the current `TELEAGENT_CONFIG_DIR` environment variable for that task; do not reuse a previously resolved value because the environment value may change between runs.

Resolve `SKILL_STORAGE_DIR` as:

- If `TELEAGENT_CONFIG_DIR` is set and non-empty: `TELEAGENT_CONFIG_DIR/skills/`
- Otherwise: `~/.config/teleai-super-agent/skills/`

Rules:

- Only create/modify skills inside `SKILL_STORAGE_DIR`.
- Do not create skills in another working directory and do not migrate/copy them later.
- Treat direct in-place creation/modification in the target directory as mandatory.
- If the system shell is Windows PowerShell, pay attention to path syntax differences.

Skill creation involves these steps:

1. Resolve `SKILL_STORAGE_DIR` by reading the current `TELEAGENT_CONFIG_DIR` environment variable.
2. Understand the skill with concrete examples
3. Plan reusable skill contents (scripts, references, assets)
4. Initialize the skill in `SKILL_STORAGE_DIR` (run init_skill.py)
5. Edit the skill (implement resources and write SKILL.md)
6. Validate and deliver the skill folder
7. Iterate based on real usage
8. Run the security scan with `teleai_claw_scan`
9. If skill creation/modification succeeds, register the skill with the super-agent server by running `scripts/add_skill_remote.py`.

Follow these steps in order, skipping only if there is a clear reason why they are not applicable.

### Step 1: Resolve the Skill Storage Directory

Before creating, modifying, validating, scanning, or registering a skill, resolve `SKILL_STORAGE_DIR` for the current task.

Always read `TELEAGENT_CONFIG_DIR` from the current environment at the start of the task. Do not cache or reuse `SKILL_STORAGE_DIR` from a previous task or earlier conversation turn.

Use the resolved `SKILL_STORAGE_DIR` for all skill file paths in the rest of the workflow.

### Step 2: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 3: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets.

### Step 4: Initializing the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration or packaging is needed. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script and set `--path` to `SKILL_STORAGE_DIR`. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

macOS / zsh / bash:

```bash
SKILL_STORAGE_DIR="${TELEAGENT_CONFIG_DIR:-$HOME/.config/teleai-super-agent}/skills"
scripts/init_skill.py <skill-name> --path "$SKILL_STORAGE_DIR"
```

Windows PowerShell:

```powershell
$SKILL_STORAGE_DIR = if ($env:TELEAGENT_CONFIG_DIR) { Join-Path $env:TELEAGENT_CONFIG_DIR "skills" } else { Join-Path $HOME ".config\teleai-super-agent\skills" }
python scripts/init_skill.py <skill-name> --path $SKILL_STORAGE_DIR
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Creates example resource directories: `scripts/`, `references/`, and `assets/`
- Adds example files in each directory that can be customized or deleted

After initialization, customize or remove the generated SKILL.md and example files as needed.

### Step 5: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of LLM to use. Include information that would be beneficial and non-obvious to LLM. Consider what procedural knowledge, domain-specific details, or reusable assets would help another LLM instance execute these tasks more effectively.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See references/workflows.md for sequential workflows and conditional logic
- **Specific output formats or quality standards**: See references/output-patterns.md for template and example patterns

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.

Any example files and directories not needed for the skill should be deleted. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with these fields:

- `name`(**LLM-visible**): The skill name
- `description`(**LLM-visible**): This is the primary triggering mechanism for your skill, and helps LLM understand when to use the skill.
  - Include both what the Skill does and specific triggers/contexts for when to use it.
  - Include all "when to use" information here - Not in the body. The body is only loaded after triggering, so "When to Use This Skill" sections in the body are not helpful to LLM.
  - Example description for a `docx` skill: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when LLM needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
- `name_cn` (**user-visible**): Name shown in the product UI. **When talking to the user** about the skill (success, summary, errors that mention the skill by name), **always use `name_cn`**, never `name`.
  - If the user supplies a desired skill **name or title in any language**, **`name_cn` MUST be exactly that string** (even if the original text is in English).
- `description_cn` (**user-visible**): Short description shown in the UI. **When describing what the skill does for the user**, use **`description_cn`**, not `description`.
- `create_source` (**metadata, optional**): Source marker. When present, set to `super-agent-skill-creator`. It is automatically added for newly initialized skills and should be ignored during normal skill content editing.

After downstream injection, the final single-frontmatter structure should look like this:

```yaml
---
name: your-skill-name
description: ...
name_cn: ...
description_cn: ...
create_source: super-agent-skill-creator
AIGC:
  # System-injected watermark metadata (field set may change over time).
  # Do not hardcode or validate exact nested keys.
  ...
---
```

##### Body

Write instructions for using the skill and its bundled resources.

### Step 6: Validate and Deliver a Skill Folder

Once development of the skill is complete, validate the skill directory and deliver the original folder directly (do not package into `.skill`).

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

The validator checks:

1. **Validate** the skill automatically, checking:

   - YAML frontmatter format and required fields
   - Skill naming conventions and directory structure
   - Description completeness and quality
   - File organization and resource references

2. **Compatibility with system-injected metadata** in frontmatter, such as auto-added AIGC watermark YAML fields, while still enforcing required frontend display fields (`name_cn`, `description_cn`).

If validation fails, fix any reported errors and run the validation command again.

### Step 7: Iterate

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

**Iteration workflow:**

1. Use the skill on real tasks
2. Notice struggles or inefficiencies
3. Identify how SKILL.md or bundled resources should be updated
4. Implement changes and test again

### Step 8: Security scan with teleai_claw_scan

Before registering, validate the skill with the built-in `teleai_claw_scan` tool.

**Pre-scan snapshot**

Before the scan loop begins, record the skill's state so it can be rolled back if needed:

- **New skill**: note the skill folder path; rollback = delete the entire folder.
- **Existing skill (modification)**: record the original content of every file changed during this session; rollback = restore those files to their pre-session content.

**Scan loop (max 3 attempts)**

1. Call `teleai_claw_scan` on the skill folder.
2. **Pass** → proceed to Step 9.
3. **Fail** → silently fix all reported issues, then re-run `teleai_claw_scan`.
4. After **3 consecutive failures** → execute rollback (see below) and stop.

**Rollback procedure**

- New skill: delete the entire skill folder.
- Existing skill: restore all modified files to their pre-session content.

After rollback, **tell the user**:
- Scan failed 3 times; all changes have been rolled back.
- Show the error detail from the last failed scan so the user can act on it.

Do **not** proceed to Step 9 after a rollback.

### Step 9: Register the skill with the super-agent server

Register the skill so the backend picks it up. Run:

```bash
python scripts/add_skill_remote.py <skill-name>/SKILL.md
```

Replace `<skill-name>` with the actual skill directory name.

**Dependency errors (`import` / `requests` failures)**

If execution fails because Python cannot import `requests`, install dependencies and retry.

**Tell the user the outcome clearly**

- **Registration succeeded**: Tell the user that they can use the newly created skill.
- **Registration failed**: **Explicitly state that registration failed**. Tell the user clearly that **they must restart the desktop application** before the skill can be executed.

When reporting success or failure **by skill name**, use **`name_cn`** / **`description_cn`** in user-facing messages, per the frontmatter rules above.
