"""OpenClaw Gateway — configuration and HTTP client.

Single source of truth for gateway URL, token, endpoint resolution,
and the JSON POST call used by all pipeline LLM steps.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MAX_RETRIES = 5
RETRY_DELAY = 30  # seconds
DEFAULT_GATEWAY_URL = "http://127.0.0.1:18789"
_BOOTSTRAP_CACHE: dict[str, str] | None = None


def _memspren_config_path() -> Path:
    return Path.home() / ".memspren-config"


def _read_kv_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def _write_kv_config(path: Path, updates: dict[str, str]) -> None:
    current = _read_kv_config(path)
    current.update({k: v for k, v in updates.items() if v is not None and v != ""})
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={v}" for k, v in current.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_openclaw_config() -> dict:
    path = Path.home() / ".openclaw" / "openclaw.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _bootstrap_gateway_config() -> dict[str, str]:
    global _BOOTSTRAP_CACHE
    if _BOOTSTRAP_CACHE is not None:
        return _BOOTSTRAP_CACHE

    cfg_path = _memspren_config_path()
    cfg = _read_kv_config(cfg_path)
    url = cfg.get("openclaw_url", "")
    token = cfg.get("openclaw_token", "")
    if url and token:
        _BOOTSTRAP_CACHE = {"openclaw_url": url, "openclaw_token": token}
        return _BOOTSTRAP_CACHE

    oc = _read_openclaw_config()
    gateway = oc.get("gateway", {}) if isinstance(oc, dict) else {}
    auth = gateway.get("auth", {}) if isinstance(gateway, dict) else {}

    env_url = os.environ.get("OPENCLAW_URL", "")
    env_token = os.environ.get("OPENCLAW_TOKEN", "")
    oc_port = gateway.get("port", 18789)
    oc_token = auth.get("token", "")

    discovered = {
        "openclaw_url": url or env_url or (f"http://127.0.0.1:{oc_port}" if oc else DEFAULT_GATEWAY_URL),
        "openclaw_token": token or env_token or oc_token,
    }

    should_persist = bool(env_url or env_token or oc_token or (oc and gateway.get("port") is not None))
    if should_persist:
        updates = {}
        if discovered.get("openclaw_url"):
            updates["openclaw_url"] = discovered["openclaw_url"]
        if discovered.get("openclaw_token"):
            updates["openclaw_token"] = discovered["openclaw_token"]
        if updates:
            _write_kv_config(cfg_path, updates)

    _BOOTSTRAP_CACHE = discovered
    return discovered


def get_gateway_url() -> str:
    return os.environ.get("OPENCLAW_URL") or _bootstrap_gateway_config().get("openclaw_url") or DEFAULT_GATEWAY_URL


def get_gateway_token() -> str:
    return os.environ.get("OPENCLAW_TOKEN") or _bootstrap_gateway_config().get("openclaw_token", "")


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
