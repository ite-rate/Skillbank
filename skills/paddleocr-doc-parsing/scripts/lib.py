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
PaddleOCR Document Parsing Library

Simple document parsing API wrapper for PaddleOCR.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx

from config_store import (
    ConfigStoreError,
    API_GUIDE_URL,
    load_runtime_config,
    normalize_api_url,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

DEFAULT_TIMEOUT = 180  # seconds (3 minutes)

# Async API defaults
DEFAULT_ASYNC_MODEL = "PaddleOCR-VL-1.6"
ASYNC_POLL_INTERVAL = 5  # seconds between polls


# =============================================================================
# Environment
# =============================================================================


def _get_env(key: str, *fallback_keys: str) -> str:
    """Get environment variable with fallback keys."""
    value = os.getenv(key, "").strip()
    if value:
        return value
    for fallback in fallback_keys:
        value = os.getenv(fallback, "").strip()
        if value:
            logger.debug(f"Using fallback env var: {fallback}")
            return value
    return ""


def get_config() -> tuple[str, str]:
    """
    Get API URL and token from environment.

    Returns:
        tuple of (api_url, token)

    Raises:
        ValueError: If not configured
    """
    try:
        persisted_api_url, persisted_token, _ = load_runtime_config()
    except ConfigStoreError as e:
        raise ValueError(str(e)) from e

    api_url = _get_env("PADDLEOCR_DOC_PARSING_API_URL") or persisted_api_url
    token = _get_env("PADDLEOCR_ACCESS_TOKEN") or persisted_token

    if not token:
        raise ValueError(
            f"PADDLEOCR_ACCESS_TOKEN not configured. Get your API at: {API_GUIDE_URL}"
        )

    api_url = normalize_api_url(api_url)

    return api_url, token


# =============================================================================
# Async API
# =============================================================================


def _submit_async_job(
    api_url: str,
    token: str,
    file_path: Optional[str],
    file_url: Optional[str],
    file_type: Optional[int],
    model: Optional[str],
    options: dict,
) -> str:
    """Submit an async OCR job, return jobId."""
    headers = {
        "Authorization": f"bearer {token}",
        "Client-Platform": "official-skill",
    }

    # Build optionalPayload from recognized options
    async_option_keys = {
        "useDocOrientationClassify",
        "useDocUnwarping",
        "useChartRecognition",
    }
    optional_payload = {k: v for k, v in options.items() if k in async_option_keys}

    effective_model = model or DEFAULT_ASYNC_MODEL

    if file_url:
        # URL mode — JSON body
        headers["Content-Type"] = "application/json"
        payload: dict[str, Any] = {
            "fileUrl": file_url,
            "model": effective_model,
        }
        if file_type is not None:
            payload["fileType"] = file_type
        if optional_payload:
            payload["optionalPayload"] = optional_payload
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(api_url, json=payload, headers=headers)
        except httpx.RequestError as e:
            raise RuntimeError(f"Async API submit request failed: {e}")
    else:
        # Local file mode — multipart form
        file_bytes = Path(file_path).read_bytes()
        form_data: dict[str, Any] = {"model": effective_model}
        if file_type is not None:
            form_data["fileType"] = str(file_type)
        if optional_payload:
            form_data["optionalPayload"] = json.dumps(optional_payload)

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    api_url,
                    headers=headers,
                    data=form_data,
                    files={"file": (Path(file_path).name, file_bytes)},
                )
        except httpx.RequestError as e:
            raise RuntimeError(f"Async API submit request failed: {e}")

    if resp.status_code != 200:
        error_detail = resp.text[:300]
        if resp.status_code == 403:
            raise RuntimeError(f"Async API auth failed (403): {error_detail}")
        elif resp.status_code == 429:
            raise RuntimeError(f"Async API rate limit (429): {error_detail}")
        else:
            raise RuntimeError(
                f"Async API submit failed ({resp.status_code}): {error_detail}"
            )

    try:
        return resp.json()["data"]["jobId"]
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Invalid async API submit response: {e}")


def _poll_async_job(
    api_url: str, token: str, job_id: str, timeout: float
) -> str:
    """Poll async job until done, return JSONL URL."""
    poll_url = f"{api_url}/{job_id}"
    headers = {"Authorization": f"bearer {token}"}
    elapsed = 0.0

    while elapsed < timeout:
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(poll_url, headers=headers)
        except httpx.TimeoutException:
            logger.debug(f"Poll timeout, retrying… elapsed={elapsed:.0f}s")
            time.sleep(ASYNC_POLL_INTERVAL)
            elapsed += ASYNC_POLL_INTERVAL
            continue
        except httpx.RequestError as e:
            raise RuntimeError(f"Poll request failed: {e}")

        if resp.status_code != 200:
            logger.warning(f"Poll HTTP {resp.status_code}, retrying…")
            time.sleep(ASYNC_POLL_INTERVAL)
            elapsed += ASYNC_POLL_INTERVAL
            continue

        try:
            data = resp.json()["data"]
        except (KeyError, json.JSONDecodeError):
            raise RuntimeError(f"Invalid poll response: {resp.text[:200]}")

        state = data.get("state", "")

        if state == "done":
            try:
                return data["resultUrl"]["jsonUrl"]
            except KeyError:
                raise RuntimeError(
                    f"Async job done but missing resultUrl: {data}"
                )
        elif state == "failed":
            raise RuntimeError(
                f"Async job failed: {data.get('errorMsg', 'Unknown error')}"
            )
        elif state in ("pending", "running"):
            progress = data.get("extractProgress", {})
            logger.debug(
                f"Async job {state}, "
                f"pages={progress.get('extractedPages', '?')}/{progress.get('totalPages', '?')}, "
                f"elapsed={elapsed:.0f}s"
            )
            time.sleep(ASYNC_POLL_INTERVAL)
            elapsed += ASYNC_POLL_INTERVAL
        else:
            raise RuntimeError(f"Async job unknown state: {state}")

    raise RuntimeError(f"Async job timed out after {timeout:.0f}s")


def _fetch_and_normalize_jsonl(jsonl_url: str) -> dict:
    """Fetch JSONL result and normalize to sync API response format."""
    try:
        with httpx.Client(timeout=120) as client:
            resp = client.get(jsonl_url)
    except (httpx.TimeoutException, httpx.RequestError) as e:
        raise RuntimeError(f"Failed to fetch JSONL result: {e}")

    if resp.status_code != 200:
        raise RuntimeError(
            f"JSONL fetch failed ({resp.status_code}): {resp.text[:200]}"
        )

    lines = resp.text.strip().split("\n")
    all_pages: list[dict] = []

    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            logger.warning(f"JSONL line {line_num} parse error: {e}")
            continue
        pages = data.get("result", {}).get("layoutParsingResults", [])
        all_pages.extend(pages)

    if not all_pages:
        raise RuntimeError("Async API returned empty result")

    # Map to the same schema as sync API response
    return {
        "logId": "async-normalized",
        "errorCode": 0,
        "errorMsg": "Success",
        "result": {
            "layoutParsingResults": all_pages,
        },
    }


def _call_async_api(
    api_url: str,
    token: str,
    file_path: Optional[str],
    file_url: Optional[str],
    file_type: Optional[int],
    model: Optional[str],
    timeout: float,
    **options,
) -> dict:
    """Call async API: submit → poll → fetch JSONL → normalize.

    Returns a dict in the same schema as the sync API response.
    """
    job_id = _submit_async_job(api_url, token, file_path, file_url, file_type, model, options)
    logger.info(f"Async job submitted: {job_id}")

    jsonl_url = _poll_async_job(api_url, token, job_id, timeout)
    logger.info("Async job completed, fetching results…")

    return _fetch_and_normalize_jsonl(jsonl_url)


# =============================================================================
# Main API
# =============================================================================


def parse_document(
    file_path: Optional[str] = None,
    file_url: Optional[str] = None,
    file_type: Optional[int] = None,
    model: Optional[str] = None,
    **options,
) -> dict[str, Any]:
    """
    Parse document with PaddleOCR async API.

    Args:
        file_path: Local file path
        file_url: URL to file
        file_type: Optional file type hint (0=PDF, 1=Image).
                   The API can auto-detect, but explicit hints may improve accuracy.
        model: Optional model name (e.g. "PaddleOCR-VL-1.6").
               Defaults to PaddleOCR-VL-1.6.
        **options: Additional API options (useDocOrientationClassify, etc.)

    Returns:
        {
            "ok": True,
            "text": "extracted text...",
            "result": { raw API result },
            "error": None
        }
        or on error:
        {
            "ok": False,
            "text": "",
            "result": None,
            "error": {"code": "...", "message": "..."}
        }
    """
    # Validate input
    if not file_path and not file_url:
        return _error("INPUT_ERROR", "file_path or file_url required")

    # Get config
    try:
        api_url, token = get_config()
    except ValueError as e:
        return _error("CONFIG_ERROR", str(e))

    # Get timeout
    try:
        _, _, persisted_timeout = load_runtime_config()
    except ConfigStoreError as e:
        return _error("CONFIG_ERROR", str(e))
    timeout = float(
        os.getenv("PADDLEOCR_DOC_PARSING_TIMEOUT", "").strip()
        or persisted_timeout
        or str(DEFAULT_TIMEOUT)
    )

    # Call async API
    try:
        result = _call_async_api(
            api_url, token, file_path, file_url, file_type, model, timeout, **options
        )
    except (ValueError, FileNotFoundError) as e:
        return _error("INPUT_ERROR", str(e))
    except RuntimeError as e:
        return _error("API_ERROR", str(e))

    # Extract text
    try:
        text = _extract_text(result)
    except ValueError as e:
        return _error("API_ERROR", str(e))

    return {
        "ok": True,
        "text": text,
        "result": result,
        "error": None,
    }


def _extract_text(result) -> str:
    """Extract text from document parsing result."""
    if not isinstance(result, dict):
        raise ValueError(
            "Invalid response schema: top-level response must be an object"
        )

    raw_result = result.get("result")
    if not isinstance(raw_result, dict):
        raise ValueError("Invalid response schema: missing result object")

    pages = raw_result.get("layoutParsingResults")
    if not isinstance(pages, list):
        raise ValueError(
            "Invalid response schema: result.layoutParsingResults must be an array"
        )

    texts = []
    for i, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{i}] must be an object"
            )

        markdown = page.get("markdown")
        if not isinstance(markdown, dict):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{i}].markdown must be an object"
            )

        text = markdown.get("text")
        if not isinstance(text, str):
            raise ValueError(
                f"Invalid response schema: result.layoutParsingResults[{i}].markdown.text must be a string"
            )
        texts.append(text)

    return "\n\n".join(texts)


def _error(code: str, message: str) -> dict:
    """Create error response."""
    return {
        "ok": False,
        "text": "",
        "result": None,
        "error": {"code": code, "message": message},
    }
