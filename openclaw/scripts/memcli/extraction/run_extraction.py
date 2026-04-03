"""run_extraction.py — Call LLM extraction step via OpenClaw Gateway."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint, post_json
from ..log import Logger
from ..paths import VaultPaths


def run(
    *,
    vault_path: Path,
    buffer_content_file: Path,
    manual_edits_file: Path,
    agent: str = "main",
    timeout: int = 120,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)
    paths.ensure()

    if not buffer_content_file.exists():
        raise RuntimeError(f"Buffer file not found: {buffer_content_file}")

    buffer_content = buffer_content_file.read_text(encoding="utf-8")
    manual_edits = manual_edits_file.read_text(encoding="utf-8") if manual_edits_file.exists() else ""

    prompt_file = PROMPTS_DIR / "extraction_prompt.txt"
    schema_file = SCHEMAS_DIR / "extraction_schema.json"

    if not prompt_file.exists():
        raise RuntimeError(f"Prompt file not found: {prompt_file}")
    if not schema_file.exists():
        raise RuntimeError(f"Schema file not found: {schema_file}")

    prompt = prompt_file.read_text(encoding="utf-8")
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    input_data = {"buffer_content": buffer_content, "manual_edits": manual_edits}

    gateway_token = get_gateway_token()
    endpoint = get_gateway_endpoint()

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": input_data,
            "schema": schema,
            "timeoutMs": timeout * 1000,
        },
    }

    log.debug("gateway request", endpoint=endpoint, agent=agent,
              buffer_len=len(buffer_content), edits_len=len(manual_edits))

    result = post_json(endpoint, payload, token=gateway_token, timeout=timeout)

    log.debug("gateway response received",
              result_type=type(result).__name__,
              result_keys=list(result.keys()) if isinstance(result, dict) else "n/a")

    if isinstance(result, dict) and result.get("ok") is False:
        log.error("gateway returned ok=false", error=str(result.get("error")))
        raise RuntimeError(result.get("error", "Gateway returned ok=false"))

    try:
        content = result["result"]["content"]
        text_item = next(item for item in content if item.get("type") == "text")
        output_json = json.loads(text_item["text"])
    except (KeyError, StopIteration, json.JSONDecodeError) as e:
        log.error("failed to extract JSON from response", error=str(e), raw=str(result)[:500])
        raise RuntimeError(f"Failed to extract JSON from response: {e}") from e

    try:
        out_file = paths.run / "extraction-output.json"
        out_file.write_text(json.dumps(output_json), encoding="utf-8")
        log.debug("saved extraction output", path=str(out_file))
    except Exception as e:
        log.warn(f"could not save extraction output to file: {e}")

    log.info("extraction complete",
             insights=len(output_json.get("raw_insights", [])),
             goals=len(output_json.get("raw_goals", [])),
             tasks=len(output_json.get("raw_tasks", [])))
    return output_json
