"""
run_extraction.py — Call LLM extraction step via OpenClaw Gateway.
Reads buffer content and manual edits, calls llm-task, returns structured JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint


def run(
    *,
    buffer_content_file: Path,
    manual_edits_file: Path,
    agent: str = "main",
    memory_path: Path,
    timeout: int = 120,
) -> dict:
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

    input_data = {
        "buffer_content": buffer_content,
        "manual_edits": manual_edits,
    }

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

    result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=timeout)

    if isinstance(result, dict) and result.get("ok") is False:
        raise RuntimeError(result.get("error", "Gateway returned ok=false"))

    # Extract JSON from response
    try:
        content = result["result"]["content"]
        text_item = next(item for item in content if item.get("type") == "text")
        output_json = json.loads(text_item["text"])
    except (KeyError, StopIteration, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to extract JSON from response: {e}") from e

    # Save to file so downstream steps can read it
    run_dir = memory_path / "run"
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "extraction-output.json").write_text(json.dumps(output_json), encoding="utf-8")
    except Exception as e:
        print(json.dumps({"warn": f"could not save extraction output to file: {e}"}),
              file=sys.stderr)

    return output_json
