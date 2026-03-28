#!/usr/bin/env python3
"""
run_extraction.py - Call LLM extraction step via OpenClaw Gateway.
Reads buffer content and manual edits, calls llm-task, outputs JSON.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path


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
    script_dir = Path(__file__).parent
    prompt_file = script_dir.parent / "prompts" / "extraction_prompt.txt"
    schema_file = script_dir.parent / "schemas" / "extraction_schema.json"

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

    # Use simple curl call - bypass all Python/Lobster complexity
    gateway_url = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
    gateway_token = os.environ.get("OPENCLAW_TOKEN", "")
    
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
    
    payload_json = json.dumps(payload)
    
    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload_json)
        temp_file = f.name
    
    try:
        # Use curl - it handles JSON properly
        cmd = [
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {gateway_token}",
            "-d", f"@{temp_file}",
            f"{gateway_url}/tools/invoke"
        ]
        
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout + 10)
        os.unlink(temp_file)
        
        if proc.returncode != 0:
            print(json.dumps({"ok": False, "error": f"curl failed: {proc.stderr}"}))
            sys.exit(1)
        
        result = json.loads(proc.stdout)
        
        # Check for error
        if isinstance(result, dict) and result.get("ok") == False:
            print(json.dumps(result))
            sys.exit(1)
        
        # Extract JSON from response
        if isinstance(result, list) and len(result) > 0:
            if "details" in result[0] and "json" in result[0]["details"]:
                output_json = result[0]["details"]["json"]
            else:
                output_json = result[0]
        else:
            output_json = result
        
        stdout = json.dumps(output_json)
        
    except Exception as e:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        print(json.dumps({"ok": False, "error": f"Extraction failed: {str(e)}"}))
        sys.exit(1)

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
