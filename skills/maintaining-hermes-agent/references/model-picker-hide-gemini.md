# Hiding Gemini from the Hermes model picker

Use when the user asks to remove a provider/model family from the visible Hermes model list.

## First choice: look for supported config

Before editing source, inspect the active config and docs/commands for a supported model-picker filter:

```bash
hermes config path
hermes config
hermes model --help 2>&1 | sed -n '1,160p'
grep -R "model_catalog\|provider_filter\|exclude\|hide" ~/.hermes/hermes-agent/hermes_cli -n --include='*.py' | head -80
```

If a config knob exists, use it. If no supported knob exists, tell the user that a source patch is required and ask before editing unless the user's request explicitly authorizes source modification.

## Local source-patch pattern

For the current Hermes codebase, the user-facing model inventory is centralized in:

```text
~/.hermes/hermes-agent/hermes_cli/inventory.py
```

`build_models_payload()` feeds the TUI/dashboard `/model` options. A local policy filter there can hide provider rows and model IDs after rows are assembled but before picker hints/canonical ordering are applied.

Pattern:

```python
_HIDDEN_MODEL_PICKER_PROVIDERS = {"gemini", "google-gemini-cli"}


def _is_hidden_model_id(model_id: object) -> bool:
    text = str(model_id or "").lower()
    return "gemini" in text


def _hide_models_from_picker(rows: list[dict]) -> list[dict]:
    filtered = []
    for row in rows:
        slug = str(row.get("slug") or "").strip().lower()
        if slug in _HIDDEN_MODEL_PICKER_PROVIDERS:
            continue
        models = row.get("models")
        if isinstance(models, list):
            kept = [m for m in models if not _is_hidden_model_id(m)]
            if len(kept) != len(models):
                row = dict(row)
                row["models"] = kept
                row["total_models"] = len(kept)
        filtered.append(row)
    return filtered
```

Call it in `build_models_payload()` after optional unconfigured rows are appended and before `_apply_picker_hints()` / `_reorder_canonical()`.

## Verification

Run with the Hermes venv, not system Python:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
from hermes_cli.inventory import load_picker_context, build_models_payload
ctx = load_picker_context()
p = build_models_payload(ctx, include_unconfigured=True, picker_hints=True, canonical_order=True, max_models=50)
hits=[]
for row in p['providers']:
    s = str(row.get('slug',''))
    n = str(row.get('name',''))
    ms = row.get('models') or []
    if 'gemini' in s.lower() or 'gemini' in n.lower() or any('gemini' in str(m).lower() for m in ms):
        hits.append((s,n,[m for m in ms if 'gemini' in str(m).lower()][:5]))
print('gemini_hits:', hits)
PY
./venv/bin/python -m py_compile hermes_cli/inventory.py
```

Expected: `gemini_hits: []` and no py_compile output.

## Runtime note

New CLI sessions see the change immediately. A running gateway/TUI process may need a restart to reload Python modules; ask before restarting.
