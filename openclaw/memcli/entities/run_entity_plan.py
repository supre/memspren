"""run_entity_plan.py — Stage 4b entity plan.

Reads raw buffer content + manual edits + existing frontmatter and produces
a structured vault write plan via LLM.
"""

from __future__ import annotations

import json
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint
from ..log import Logger

PROMPT_FILE = PROMPTS_DIR / "entity_plan_prompt.txt"
SCHEMA_FILE = SCHEMAS_DIR / "entity_plan_schema.json"


def run(
    *,
    buffer_content_file: Path,
    manual_edits_file: Path,
    frontmatter_file: str = "",
    agent: str = "memspren-heavy",
    timeout: int = 120,
    log: Logger,
) -> dict:
    # Read raw buffer content
    if not buffer_content_file.exists():
        raise RuntimeError(f"Buffer content file not found: {buffer_content_file}")
    buffer_content = buffer_content_file.read_text(encoding="utf-8")
    log.debug("read buffer content", length=len(buffer_content))

    # Read manual edits
    manual_edits = ""
    if manual_edits_file.exists():
        manual_edits = manual_edits_file.read_text(encoding="utf-8")
    log.debug("read manual edits", length=len(manual_edits))

    # Read existing frontmatter
    frontmatter: list = []
    if frontmatter_file:
        try:
            frontmatter = json.loads(Path(frontmatter_file).read_text(encoding="utf-8"))
        except Exception:
            frontmatter = []
    log.debug("read frontmatter", count=len(frontmatter))

    # Load prompt and schema
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
            "input": {
                "buffer_content": buffer_content,
                "manual_edits": manual_edits,
                "frontmatter": frontmatter,
            },
            "schema": schema,
            "agent": agent,
            "timeoutMs": timeout * 1000,
        },
    }

    log.debug("entity plan gateway request",
              endpoint=endpoint, agent=agent,
              buffer_len=len(buffer_content),
              edits_len=len(manual_edits),
              frontmatter_count=len(frontmatter))
    log.debug("entity plan payload keys", payload_keys=list(payload["args"]["input"].keys()))

    try:
        result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=timeout)
    except RuntimeError as exc:
        log.error("entity plan gateway call failed", error=str(exc))
        raise

    log.debug("entity plan gateway response", response=json.dumps(result, default=str)[:5000])

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
        log.error("could not parse gateway response", error=str(exc), raw=str(result)[:1000])
        raise RuntimeError(f"could not parse gateway response: {exc}") from exc

    entity_count = len(output.get("entities", [])) if isinstance(output, dict) else 0
    log.info("entity plan complete", entity_count=entity_count,
             summary=output.get("summary", "") if isinstance(output, dict) else "")
    return output
