# OpenClaw Linux Gateway Installation

## Overview

OpenClaw Gateway is fully supported on Linux (Ubuntu, Debian, and other distributions). The native desktop companion app is NOT available on Linux, but the gateway/service functionality works perfectly via Node.js.

## Installation Method

Use the official install script:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

This script will:
1. Detect the OS (linux)
2. Install Node.js if not present (via NodeSource)
3. Install build tools (make, g++, cmake, python3)
4. Configure npm for user-local installs (avoids sudo)
5. Install the OpenClaw npm package globally

## What Gets Installed

- **Node.js**: Latest LTS version (e.g., v24.x)
- **npm**: Latest version (e.g., 11.x)
- **OpenClaw CLI**: Installed to `~/.npm-global/bin/openclaw`
- **npm prefix**: Set to `~/.npm-global` (user-local, no sudo needed)

## Post-Installation

### Add to PATH

The installer will warn if PATH is missing the npm global bin dir:

```bash
# Add to ~/.bashrc and ~/.profile
echo 'export PATH="/home/ubuntu/.npm-global/bin:$PATH"' >> ~/.bashrc
echo 'export PATH="/home/ubuntu/.npm-global/bin:$PATH"' >> ~/.profile
```

### Verify Installation

```bash
# Using full path (before PATH update)
~/.npm-global/bin/openclaw --version

# After PATH update
openclaw --version
```

Expected output: `OpenClaw 2026.6.8 (844f405)` or similar

### First-Time Setup

```bash
openclaw onboard
```

This interactive wizard configures:
- API keys for LLM providers
- Channel integrations (Feishu, Telegram, etc.)
- Gateway settings

## Common Issues

### Issue 1: "No TTY; run openclaw onboard to finish setup"

When installing via SSH without TTY, the installer completes but cannot run the interactive onboarding. Run it manually after installation.

### Issue 2: PATH not set

If `openclaw: command not found` after installation, the npm global bin directory is not in PATH. Add it as shown above.

### Issue 3: Network timeout during Node.js installation

On cloud servers in certain regions (e.g., mainland China), NodeSource downloads may timeout. Solutions:
- Use a mirror or proxy
- Install Node.js manually first, then re-run the OpenClaw installer

## Key Differences from macOS/Windows

| Feature | Linux | macOS/Windows |
|---------|-------|---------------|
| Gateway/CLI | Supported | Supported |
| Desktop companion app | Not available | Available |
| Installation method | npm/Node.js | DMG/EXE installer |
| System service | systemd (manual) | launchd/Windows Service |

## Cloud Server Specific Notes

When installing on cloud VPS (Tencent Cloud, AWS, etc.):

1. **Username**: Often `ubuntu` (not `root`) for Ubuntu images
2. **SSH key**: Use `-i` flag: `ssh -i ~/Downloads/key.pem ubuntu@<ip>`
3. **Firewall**: Ensure port 18789 (default gateway port) is open if using remote gateway
4. **No GUI**: Since there's no desktop companion, all configuration is CLI-based

## Verification Checklist

- [ ] `openclaw --version` returns version string
- [ ] `openclaw config file` shows config path
- [ ] `openclaw channels list --all` shows available channels
- [ ] `openclaw gateway --help` shows gateway commands
- [ ] `openclaw status` shows service status (if gateway running)
