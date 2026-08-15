#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml


ALLOWED_PROPERTIES = {
    "name",
    "description",
    "name_cn",
    "description_cn",
    "create_source",
    "AIGC",
    "license",
    "allowed-tools",
    "metadata",
}


def _extract_frontmatter_blocks(markdown_content: str) -> list[dict[str, Any]]:
    """Extract all top-level consecutive YAML frontmatter blocks.

    The parser supports markdown files that may contain multiple YAML blocks at
    the beginning (for example an AIGC watermark block followed by the skill
    metadata block). Only frontmatter blocks at file start are considered.
    """
    if not markdown_content.startswith("---\n"):
        return []

    blocks: list[dict[str, Any]] = []
    cursor = 0
    pattern = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)

    while True:
        match = pattern.match(markdown_content, cursor)
        if not match:
            break
        frontmatter_text = match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in frontmatter: {exc}") from exc
        if not isinstance(frontmatter, dict):
            raise ValueError("Frontmatter must be a YAML dictionary")
        blocks.append(frontmatter)
        cursor = match.end()
        if cursor < len(markdown_content) and markdown_content[cursor] == "\n":
            cursor += 1

    return blocks


def _find_skill_frontmatter(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the frontmatter block containing required skill metadata."""
    for block in blocks:
        if "name" in block or "description" in block:
            return block
    return None


def validate_skill(skill_path: str) -> tuple[bool, str]:
    """Validate core skill structure and SKILL.md frontmatter semantics.

    Args:
        skill_path: Path to the skill directory to validate.

    Returns:
        A tuple `(is_valid, message)` where `is_valid` indicates validation
        success, and `message` contains either success text or error details.
    """
    skill_path_obj = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path_obj / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    try:
        frontmatter_blocks = _extract_frontmatter_blocks(content)
    except ValueError as exc:
        return False, str(exc)

    if not frontmatter_blocks:
        return False, "Invalid frontmatter format"

    frontmatter = _find_skill_frontmatter(frontmatter_blocks)
    if frontmatter is None:
        return False, "Missing skill frontmatter block with 'name' and 'description'"

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (hyphen-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Required Chinese display fields for frontend
    for zh_field in ("name_cn", "description_cn"):
        if zh_field not in frontmatter:
            return False, f"Missing '{zh_field}' in frontmatter"
        zh_value = frontmatter.get(zh_field)
        if not isinstance(zh_value, str):
            return False, f"{zh_field} must be a string, got {type(zh_value).__name__}"

    # Optional source marker for skills created by the skill-creator initializer.
    # Existing or manually authored skills are valid without this key.
    create_source = frontmatter.get("create_source")
    if create_source is not None:
        if not isinstance(create_source, str):
            return False, f"create_source must be a string, got {type(create_source).__name__}"
        if create_source != "super-agent-skill-creator":
            return False, (
                "Invalid 'create_source' value. "
                "When present, it must be 'super-agent-skill-creator'"
            )

    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
