#!/usr/bin/env python3
"""
run_extraction.py - Call LLM extraction step via OpenClaw Gateway.
Reads buffer content and manual edits, calls llm-task, outputs JSON.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR


def main():
    parser = argparse.ArgumentParser(description="Run extraction step via OpenClaw llm-task")
    parser.add_argument("--buffer-content-file", required=True, help="Path to buffer content file")
    parser.add_argument("--manual-edits-file", required=True, help="Path to manual edits file")
    parser.add_argument("--agent", default="main", help="OpenClaw agent ID")
    parser.add_argument("--memory-path", required=True, help="Memory directory path")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    args = parser.parse_args()

    buffer_path = Path(args.buffer_content_file)
    edits_path = Path(args.manual_edits_file)

    if not buffer_path.exists():
        print(json.dumps({"ok": False, "error": f"Buffer file not found: {buffer_path}"}))
        sys.exit(1)

    buffer_content = buffer_path.read_text(encoding="utf-8")
    manual_edits = edits_path.read_text(encoding="utf-8") if edits_path.exists() else ""

    # Load extraction prompt and schema
    prompt_file = PROMPTS_DIR / "extraction_prompt.txt"
    schema_file = SCHEMAS_DIR / "extraction_schema.json"

    if not prompt_file.exists():
        print(json.dumps({"ok": False, "error": f"Prompt file not found: {prompt_file}"}))
        sys.exit(1)
    if not schema_file.exists():
        print(json.dumps({"ok": False, "error": f"Schema file not found: {schema_file}"}))
        sys.exit(1)

    prompt = prompt_file.read_text(encoding="utf-8")
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    input_data = {
        "buffer_content": buffer_content,
        "manual_edits":   manual_edits,
    }

    gateway_url = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
    gateway_token = os.environ.get("OPENCLAW_TOKEN", "")
    endpoint = gateway_url.rstrip("/") + "/tools/invoke"

    # Match Lobster's exact payload format
    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt": prompt,
            "input": input_data,
            "schema": schema,
            "timeoutMs": args.timeout * 1000
        }
    }

    try:
        result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=args.timeout)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)

    # Check for error
    if isinstance(result, dict) and result.get("ok") is False:
        print(json.dumps(result))
        sys.exit(1)

    # Extract JSON from response: { ok, result: { content: [{ type, text, ... }] } }
    try:
        content = result["result"]["content"]
        text_item = next(item for item in content if item.get("type") == "text")
        output_json = json.loads(text_item["text"])
    except (KeyError, StopIteration, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": f"Failed to extract JSON from response: {e}", "raw": result}))
        sys.exit(1)

    stdout = json.dumps(output_json)

    # Save to file so run_entity_plan.py can read it without shell interpolation
    run_dir = Path(args.memory_path) / "run"
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "extraction-output.json").write_text(stdout, encoding="utf-8")
    except Exception as e:
        print(json.dumps({"warn": f"could not save extraction output to file: {e}"}),
              file=sys.stderr)

    print(stdout)


if __name__ == "__main__":
    main()
