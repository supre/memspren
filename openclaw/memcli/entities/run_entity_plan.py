"""
run_entity_plan.py — Stage 4b entity plan wrapper.

Reads extraction, frontmatter, and task_inbox from temp files to avoid
shell interpolation of user-authored strings in Lobster YAML.
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint

PROMPT_FILE = PROMPTS_DIR / "entity_plan_prompt.txt"
SCHEMA_FILE = SCHEMAS_DIR / "entity_plan_schema.json"


def run(
    *,
    extraction_file: Path,
    frontmatter_file: str = "",
    task_inbox_file: str = "",
    agent: str = "memspren-heavy",
    timeout: int = 120,
) -> dict:
    try:
        extraction = json.loads(Path(extraction_file).read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"could not read extraction file: {e}") from e

    frontmatter: list = []
    if frontmatter_file:
        try:
            frontmatter = json.loads(Path(frontmatter_file).read_text(encoding="utf-8"))
        except Exception:
            frontmatter = []

    task_inbox: dict = {}
    if task_inbox_file:
        try:
            task_inbox = json.loads(Path(task_inbox_file).read_text(encoding="utf-8"))
        except Exception:
            task_inbox = {}

    try:
        prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise RuntimeError(f"could not read prompt file: {e}") from e

    try:
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"could not read schema file: {e}") from e

    gateway_token = get_gateway_token()
    endpoint = get_gateway_endpoint()

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": {"extraction": extraction, "frontmatter": frontmatter, "task_inbox": task_inbox},
            "schema": schema,
            "agent": agent,
            "timeoutMs": timeout * 1000,
        },
    }

    result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=timeout)

    # Extract JSON from Gateway response
    try:
        if "result" in result:
            inner = result["result"]
            if "details" in inner and "json" in inner["details"]:
                output = inner["details"]["json"]
            elif "content" in inner:
                items = inner["content"]
                text = next(i["text"] for i in items if i.get("type") == "text")
                output = json.loads(text)
            else:
                output = inner
        else:
            output = result
    except Exception as exc:
        raise RuntimeError(f"could not parse gateway response: {exc}") from exc

    return output
