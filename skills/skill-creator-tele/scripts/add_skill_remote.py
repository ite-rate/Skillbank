#!/usr/bin/env python3
"""POST ``{"path": ...}`` to ``$SUPER_AGENT_SERVER_URL/skill/add``."""

import argparse
import logging
import os
import sys
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def resolve_basic_auth() -> tuple[str, str] | None:
    """Read desktop-provided Basic Auth credentials from env."""
    username = (
        os.getenv("SUPER_AGENT_OPENCODE_USERNAME")
        or os.getenv("OPENCODE_SERVER_USERNAME")
        or ""
    ).strip()
    password = (
        os.getenv("SUPER_AGENT_OPENCODE_PASSWORD")
        or os.getenv("OPENCODE_SERVER_PASSWORD")
        or ""
    )
    if not username or not password:
        return None
    return username, password


def resolve_skill_storage_dir() -> Path:
    """Resolve skill storage root from TELEAGENT_CONFIG_DIR with legacy fallback."""
    config_dir = os.getenv("TELEAGENT_CONFIG_DIR")
    if config_dir and config_dir.strip():
        return Path(config_dir.strip()).expanduser() / "skills"
    return Path.home() / ".config" / "teleai-super-agent" / "skills"


def main(argv: list[str] | None = None) -> int:
    """Parse args, resolve path, POST, return shell exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="POST skill path to SUPER_AGENT_SERVER_URL/skill/add",
    )
    parser.add_argument(
        "path",
        help=(
            "Relative to SKILL_STORAGE_DIR "
            "($TELEAGENT_CONFIG_DIR/skills when set, otherwise "
            "~/.config/teleai-super-agent/skills/), or absolute path to SKILL.md or folder"
        ),
    )
    args = parser.parse_args(argv)

    raw = args.path.strip()
    if not raw:
        logger.error("path must be non-empty")
        return 1

    user_path = Path(raw).expanduser()
    skills_root = resolve_skill_storage_dir()
    candidate = user_path if user_path.is_absolute() else skills_root / user_path
    skill_path = str(candidate.resolve(strict=False))

    if not Path(skill_path).is_file():
        logger.error("SKILL.md not found: %s", skill_path)
        return 1

    base = os.getenv("SUPER_AGENT_SERVER_URL")
    if not base or not str(base).strip():
        logger.error("Missing or empty SUPER_AGENT_SERVER_URL")
        return 1

    url = f"{str(base).strip().rstrip('/')}/skill/add"
    auth = resolve_basic_auth()

    try:
        response = requests.post(
            url,
            json={"path": skill_path},
            auth=auth,
            timeout=60.0,
        )
    except requests.RequestException as exc:
        logger.error("Request failed: %s", exc)
        return 1

    if response.ok:
        logger.info("Regsiter success")
        return 0

    logger.error("Error: HTTP %s: %s", response.status_code, response.text or response.reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
