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
Persist PaddleOCR document parsing credentials for future runs.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_store import (
    DEFAULT_API_URL,
    ConfigStoreError,
    clear_access_token,
    clear_persisted_settings,
    get_config_path,
    get_keyring_backend_name,
    load_access_token,
    load_persisted_settings,
    normalize_api_url,
    save_access_token,
    save_persisted_settings,
)


def _mask(secret: str) -> str:
    if not secret:
        return "(not set)"
    if len(secret) <= 12:
        return "*" * len(secret)
    return f"{secret[:6]}...{secret[-4:]}"


def _print_status() -> int:
    settings = load_persisted_settings()
    token = load_access_token()

    print("PaddleOCR Document Parsing Credential Status")
    print("=" * 50)
    print(f"Config file: {get_config_path()}")
    print(f"Keyring backend: {get_keyring_backend_name()}")
    print(f"API URL: {settings.get('api_url') or DEFAULT_API_URL}")
    print(f"Timeout: {settings.get('timeout') or '(not set)'}")
    print(f"Access token: {_mask(token)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Persist PaddleOCR document parsing credentials securely"
    )
    parser.add_argument(
        "--api-url",
        help="PaddleOCR API endpoint (optional, defaults to the official async API). "
        "Use this only for self-hosted deployments.",
    )
    parser.add_argument("--access-token", help="PaddleOCR access token")
    parser.add_argument("--timeout", help="Optional timeout in seconds")
    parser.add_argument(
        "--show", action="store_true", help="Show persisted configuration status"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Remove persisted settings and token"
    )
    args = parser.parse_args()

    try:
        if args.clear:
            clear_persisted_settings()
            clear_access_token()
            print("Persisted PaddleOCR settings cleared.")
            return 0

        if args.show:
            return _print_status()

        api_url = args.api_url or ""
        if not api_url:
            api_url = input(
                f"PaddleOCR API URL (press Enter to use default: {DEFAULT_API_URL}): "
            ).strip()
        access_token = args.access_token or getpass.getpass(
            "PaddleOCR Access Token: "
        ).strip()
        timeout = args.timeout

        normalized_api_url = normalize_api_url(api_url or None)
        save_persisted_settings(normalized_api_url, timeout)
        save_access_token(access_token)

        print("Credentials saved.")
        print(f"API URL: {normalized_api_url}")
        print(f"Config file: {get_config_path()}")
        print(f"Keyring backend: {get_keyring_backend_name()}")
        print("The API URL is persisted in the user config directory.")
        print("The access token is stored in the OS secure credential store.")
        return 0

    except (ValueError, ConfigStoreError) as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
