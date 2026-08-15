# Skill Hygiene & Cleanup

Session-proven workflow for diagnosing and cleaning up the Hermes skill library to reduce system-prompt token bloat.

## Diagnosis Steps

### 1. Identify empty-shell / stub directories

Top-level dirs in `~/.hermes/skills/` that have **no SKILL.md** are stubs — they only contain a `DESCRIPTION.md` and never function as real skills. They still appear in `skills_list` output and waste context.

```bash
# Find top-level dirs without SKILL.md
for d in ~/.hermes/skills/*/; do
  name=$(basename "$d")
  [[ "$name" == .* ]] && continue
  count=$(find "$d" -name 'SKILL.md' 2>/dev/null | wc -l)
  [[ "$count" -eq 0 ]] && echo "STUB: $name"
done
```

Safe to `rm -rf` these — they have no SKILL.md and no real skill content.

### 2. Identify duplicate top-level symlinks

Hermes auto-creates symlinks from `~/.hermes/skills/<name>` → `~/.agents/skills/<name>` for certain skills (brainstorming, systematic-debugging, etc.). These also exist inside category dirs (e.g. `software-development/brainstorming/`), so the same skill appears **twice** in `skills_list`, doubling its description in the system prompt.

```bash
ls -la ~/.hermes/skills/ | grep '^l'
# Symlink targets: ../../.agents/skills/<name>  →  resolves to ~/.agents/skills/<name>
```

These symlinks are 0-file overhead on disk but cause duplicate entries in the skill index. They are safe to remove — the category-dir copy is the canonical one.

### 3. Check skill usage data

`~/.hermes/skills/.usage.json` tracks every skill's `use_count`, `created_at`, `created_by`, and `state`. This is the authoritative source for "which skills are actually used."

```python
import json
from pathlib import Path

with open(Path.home() / '.hermes/skills/.usage.json') as f:
    data = json.load(f)

never_used = sorted([name for name, v in data.items()
                     if v.get('state') == 'active' and v.get('use_count', 0) == 0])
used = sorted([name for name, v in data.items() if v.get('use_count', 0) > 0])
```

- `created_by: "agent"` → Hermes autonomously created this skill (usually high quality, keep).
- `created_by: null` → Installed via `hermes skills install` or bundled (bulk install, often never used).
- `use_count: 0` → Never loaded in any session; candidate for disabling.

### 4. Measure token impact

The skills prompt snapshot at `~/.hermes/.skills_prompt_snapshot.json` contains the actual data injected into the system prompt:

```python
import json
d = json.load(open('~/.hermes/.skills_prompt_snapshot.json'))
skills = d.get('skills', [])
total_desc = sum(len(s.get('description', '')) for s in skills)
print(f'Skills in prompt: {len(skills)}, description bytes: {total_desc}')
```

Each disabled skill removes its `skill_name + category + description` from the snapshot on the next session reset.

## Remediation

### Delete stub directories

```bash
rm -rf ~/.hermes/skills/<stub-name>/
```

Safe when the directory has no SKILL.md. Always check for a duplicate in the correct category dir first (e.g. `research/daily-agent-briefing/` before deleting top-level `daily-agent-briefing/`).

### Disable never-used skills via config.yaml

```yaml
# ~/.hermes/config.yaml
skills:
  disabled:
    - airtable
    - apple-notes
    - comfyui
    # ... all use_count=0 skills
```

Or via Python (batch update):

```python
import yaml
config_path = Path.home() / '.hermes/config.yaml'
parsed = yaml.safe_load(config_path.read_text())
parsed.setdefault('skills', {})['disabled'] = never_used_list
config_path.write_text(yaml.dump(parsed, default_flow_style=False, allow_unicode=True))
```

**Always back up config.yaml first:** `cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak`

**Takes effect on next `/reset` or new session.** The disabled skills stay on disk but are no longer injected into the system prompt.

### Re-enabling

Remove the skill name from `skills.disabled` in config.yaml, then `/reset`. No reinstall needed — the skill files are still on disk.

## Key Facts

- Top-level symlinks point to `~/.agents/skills/` (not `~/.hermes/.agents/skills/`).
- `.usage.json` tracks 88+ skills; on this system 60 were never used (use_count=0), all batch-installed on 2026-06-18 with `created_by: null`.
- Only 4 skills were agent-created (`created_by: "agent"`): `ai-coding-agent-research`, `creating-learning-audio`, `network-proxy-diagnostics`, `openclaw-operations` — all were actually used.
- The 5 stub dirs (diagramming, domain, feeds, gifs, inference-sh) were early-install remnants from 2026-04-09 — only a DESCRIPTION.md, no SKILL.md.
- The top-level `daily-agent-briefing/` was a duplicate of `research/daily-agent-briefing/` (identical `scripts/send-feishu-group-msg.py`, but the real 41KB SKILL.md lives under `research/`).