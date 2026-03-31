#!/usr/bin/env python3
"""Minimal HTTP client for calling the OpenClaw Gateway via urllib."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


def post_json(url: str, payload: dict, token: str = "", timeout: int = 120, retries: int = MAX_RETRIES) -> dict:
    """POST JSON payload to the given URL and return the decoded JSON response.

    Retries on HTTP 500 errors up to `retries` times with a delay between attempts.
    """
    data = json.dumps(payload).encode("utf-8")
    last_error = None

    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, data=data, method="POST")
        request.add_header("Content-Type", "application/json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
            try:
                return json.loads(body)
            except json.JSONDecodeError as err:
                raise RuntimeError(f"Gateway returned invalid JSON: {err}") from err
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"Gateway HTTP {err.code}: {detail}")
            if err.code >= 500 and attempt < retries:
                time.sleep(RETRY_DELAY)
                continue
            raise last_error from err
        except urllib.error.URLError as err:
            raise RuntimeError(f"Gateway request failed: {err}") from err

    raise last_error  # should not reach here
