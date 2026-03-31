"""Shared OpenClaw Gateway configuration.

Single source of truth for gateway URL, token, and endpoint resolution.
All modules that call the Gateway should import from here instead of
reading os.environ directly.
"""

import os


def get_gateway_url() -> str:
    return os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")


def get_gateway_token() -> str:
    return os.environ.get("OPENCLAW_TOKEN", "")


def get_gateway_endpoint() -> str:
    return get_gateway_url().rstrip("/") + "/tools/invoke"
