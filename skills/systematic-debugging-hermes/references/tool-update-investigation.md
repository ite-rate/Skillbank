# Tool/Software Update Investigation Notes

Session: 2026-06-29 — User asked "reasonix最近有什么修改", I checked local config first, user corrected: "我说的是官方更新" (I mean official updates).

## Lesson: Distinguish local vs official when user asks about "changes/updates"

When a user asks about a tool/product's recent changes, the request spans two distinct layers:

| Layer | What to check | Commands/Approach |
|-------|--------------|-------------------|
| **Local** | User's config, skills, customizations | `~/.reasonix/config.toml`, `~/.reasonix/skills/`, `ls -lt` for recent files |
| **Official** | Upstream releases, changelogs, version tags | GitHub releases page, `github.com/<org>/<repo>/releases`, version tags |

## Default heuristic

Start with the **official layer** unless context strongly suggests local. Users asking "what's changed with X" typically mean upstream news, not their own config.

## Checking installed vs latest version (macOS)

```bash
# Get installed app version from Info.plist
plutil -p /Applications/Reasonix.app/Contents/Info.plist | grep CFBundleShortVersion

# Find the app's binary
find /Applications/Reasonix.app -name "reasonix*" -type f

# Check if binary responds to --version (often doesn't for desktop apps)
/Applications/Reasonix.app/Contents/MacOS/reasonix-desktop --version
```

## Finding official updates

1. **Identify the official repo**: Search GitHub for the tool name, verify it's the right org (e.g., `esengine/DeepSeek-Reasonix`)
2. **Check releases**: `github.com/<org>/<repo>/releases`
3. **Compare versions**: Installed (from Info.plist or `--version`) vs latest release tag
4. **Extract changelog**: Use `browser_console` to pull the release notes text from GitHub release pages
5. **Check commit history**: Recent commits on default branch for bleeding-edge changes

## Version gap awareness

In this session, user had **v1.6.0** installed (Jun 11) while latest was **v1.13.1** (10 hours ago) — a significant gap of ~7 minor versions over ~2-3 weeks. This is common with rapidly evolving tools. Always surface the version gap to the user.

## Pitfall: Don't assume local config is what the user wants

The user's local `~/.reasonix/` contained:
- `config.toml` (Jun 18 updated)
- 24 new `dbs-*` skills (Jun 16)
- Symlinked skills from `~/.agents/skills/` (Jun 9)

But the user explicitly wanted **official** updates, not local customizations. The local changes were irrelevant to their question.
