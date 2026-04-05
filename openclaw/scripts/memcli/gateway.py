"""OpenClaw Gateway — configuration and HTTP client.

Single source of truth for gateway URL, token, endpoint resolution,
and the JSON POST call used by all pipeline LLM steps.
"""

import json
import os
import time
import urllib.error
import urllib.request

MAX_RETRIES = 5
RETRY_DELAY = 30  # seconds


def get_gateway_url() -> str:
    return os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")


def get_gateway_token() -> str:
    return os.environ.get("OPENCLAW_TOKEN", "")


def get_gateway_endpoint() -> str:
    return get_gateway_url().rstrip("/") + "/tools/invoke"


def post_json(url: str, payload: dict, token: str = "", timeout: int = 600, retries: int = MAX_RETRIES) -> dict:
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
