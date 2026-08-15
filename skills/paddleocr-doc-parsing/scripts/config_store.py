#!/usr/bin/env python3
# Copyright (c) 2025 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Persistent configuration store for the PaddleOCR document parsing skill.

Non-sensitive settings are stored in a JSON file under the user's config
directory. Sensitive secrets are stored in the OS keyring when available.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

API_GUIDE_URL = "https://paddleocr.com"
DEFAULT_API_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
APP_NAME = "XingchenSuperAgent"
SKILL_NAME = "paddleocr-doc-parsing"
KEYRING_SERVICE = "xingchen-super-agent-desktop.paddleocr-doc-parsing"
KEYRING_USERNAME = "PADDLEOCR_ACCESS_TOKEN"


class ConfigStoreError(RuntimeError):
    """Raised when persisted configuration cannot be used safely."""


def get_config_dir() -> Path:
    """Return the per-user config directory for this skill."""
    if sys.platform == "win32":
        base_dir = (
            os.getenv("APPDATA")
            or os.getenv("LOCALAPPDATA")
            or str(Path.home() / "AppData" / "Roaming")
        )
        return Path(base_dir) / APP_NAME / "skills" / SKILL_NAME
    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / APP_NAME
            / "skills"
            / SKILL_NAME
        )
    base_dir = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base_dir) / APP_NAME / "skills" / SKILL_NAME


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def normalize_api_url(api_url: str | None = None) -> str:
    """Normalize and validate the document parsing endpoint.

    If api_url is empty/None, returns the default async API URL.
    Bare domains are resolved to the async endpoint.
    """
    value = (api_url or "").strip()
    if not value:
        return DEFAULT_API_URL

    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"

    api_path = urlparse(value).path.rstrip("/")

    # Accept known endpoint path
    if api_path.endswith("/api/v2/ocr/jobs"):
        return value

    # Bare domain (no API path) → default to async endpoint
    if not api_path or api_path == "/":
        return value.rstrip("/") + "/api/v2/ocr/jobs"

    raise ValueError(
        "PADDLEOCR_DOC_PARSING_API_URL must be a valid PaddleOCR async API endpoint:\n"
        f"  - Default: {DEFAULT_API_URL}\n"
        "  - Or bare domain: https://your-service.paddleocr.com\n"
        "Or simply omit the URL to use the default endpoint."
    )


def load_persisted_settings() -> dict[str, Any]:
    """Read non-secret settings from disk."""
    config_path = get_config_path()
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigStoreError(f"Cannot read persisted config: {e}") from e

    if not isinstance(data, dict):
        raise ConfigStoreError("Persisted config must be a JSON object")

    return data


def save_persisted_settings(api_url: str, timeout: str | None = None) -> Path:
    """Persist non-secret settings to disk."""
    payload: dict[str, Any] = {"api_url": normalize_api_url(api_url)}
    if timeout is not None and str(timeout).strip():
        payload["timeout"] = str(timeout).strip()

    config_path = get_config_path()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as e:
        raise ConfigStoreError(f"Cannot write persisted config: {e}") from e
    return config_path


def clear_persisted_settings() -> None:
    """Delete the JSON config file if it exists."""
    config_path = get_config_path()
    try:
        if config_path.exists():
            config_path.unlink()
    except OSError as e:
        raise ConfigStoreError(f"Cannot delete persisted config: {e}") from e


def _load_keyring():
    try:
        import keyring
        from keyring.errors import KeyringError
    except ImportError:
        return None, None
    return keyring, KeyringError


def get_keyring_backend_name() -> str:
    """Return the active keyring backend name, or an explanatory message."""
    keyring, _ = _load_keyring()
    if keyring is None:
        return "missing:keyring"
    try:
        return keyring.get_keyring().__class__.__name__
    except Exception as e:
        return f"unavailable:{e}"


def save_access_token(access_token: str) -> None:
    """Persist the token to the OS keyring."""
    token = (access_token or "").strip()
    if not token:
        raise ValueError(
            f"PADDLEOCR_ACCESS_TOKEN not configured. Get your API at: {API_GUIDE_URL}"
        )

    keyring, keyring_error = _load_keyring()
    if keyring is None:
        raise ConfigStoreError(
            "Secure token storage requires the 'keyring' package. "
            "Install dependencies with: pip install -r scripts/requirements.txt"
        )

    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, token)
    except keyring_error as e:
        raise ConfigStoreError(f"Cannot save token to system keyring: {e}") from e


def load_access_token() -> str:
    """Read the token from the OS keyring."""
    keyring, keyring_error = _load_keyring()
    if keyring is None:
        return ""

    try:
        return (keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) or "").strip()
    except keyring_error as e:
        raise ConfigStoreError(f"Cannot read token from system keyring: {e}") from e


def clear_access_token() -> None:
    """Delete the token from the OS keyring if present."""
    keyring, keyring_error = _load_keyring()
    if keyring is None:
        return

    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring_error:
        return


def load_runtime_config() -> tuple[str, str, str]:
    """
    Resolve runtime config with precedence:
    1. Environment variables
    2. Persisted config file / OS keyring
    """
    api_url = os.getenv("PADDLEOCR_DOC_PARSING_API_URL", "").strip()
    token = os.getenv("PADDLEOCR_ACCESS_TOKEN", "").strip()
    timeout = os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", "").strip()

    settings: dict[str, Any] = {}
    if not api_url or not timeout:
        settings = load_persisted_settings()

    if not api_url:
        api_url = str(settings.get("api_url", "")).strip()
    if not timeout:
        timeout = str(settings.get("timeout", "")).strip()
    if not token:
        token = load_access_token()

    return api_url, token, timeout
