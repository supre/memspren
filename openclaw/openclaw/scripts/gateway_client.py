#!/usr/bin/env python3
"""Minimal HTTP client for calling the OpenClaw Gateway via urllib."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def post_json(url: str, payload: dict, token: str = "", timeout: int = 120) -> dict:
    """POST JSON payload to the given URL and return the decoded JSON response."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gateway HTTP {err.code}: {detail}") from err
    except urllib.error.URLError as err:
        raise RuntimeError(f"Gateway request failed: {err}") from err

    try:
        return json.loads(body)
    except json.JSONDecodeError as err:
        raise RuntimeError(f"Gateway returned invalid JSON: {err}") from err
