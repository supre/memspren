#!/usr/bin/env python3
"""
run_extraction.py — Stage 1 extraction wrapper.

Reads heavy input from temp files (buffer content, manual edits) rather than
accepting it as shell-interpolated strings, which breaks on quotes/newlines.
Builds a JSON payload and calls openclaw.invoke --tool llm-task --args-json directly.
Saves output to MEMORY_PATH/run/extraction-output.json for downstream steps
(e.g. run_entity_plan.py) that also cannot safely receive it via shell arg.

Returns JSON to stdout (runner-compatible — no other stdout output).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
# Prompt and schema are fixed for Stage 1 extraction — not exposed as CLI flags
PROMPT_FILE = SCRIPT_DIR.parent / "prompts" / "extraction_prompt.txt"
SCHEMA_FILE = SCRIPT_DIR.parent / "schemas" / "extraction_schema.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buffer-content-file", required=True,
                        help="Path to file containing raw buffer text")
    parser.add_argument("--manual-edits-file", default="",
                        help="Path to file containing manual edits text (optional)")
    parser.add_argument("--agent", default="memspren-heavy")
    parser.add_argument("--memory-path", required=True,
                        help="MEMORY_PATH — extraction output saved here for downstream steps")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    # Read buffer content from file
    try:
        buffer_content = Path(args.buffer_content_file).read_text(encoding="utf-8")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"could not read buffer-content file: {e}"}))
        sys.exit(1)

    # Read manual edits content from file (non-fatal if absent)
    manual_edits = ""
    if args.manual_edits_file:
        try:
            p = Path(args.manual_edits_file)
            if p.exists():
                manual_edits = p.read_text(encoding="utf-8")
        except Exception:
            pass

    # Load prompt and schema to build --args-json payload for openclaw.invoke
    try:
        prompt = PROMPT_FILE.read_text(encoding="utf-8").strip()
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"could not read prompt file: {e}"}))
        sys.exit(1)

    try:
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"could not read schema file: {e}"}))
        sys.exit(1)

    input_data = {
        "buffer_content": buffer_content,
        "manual_edits":   manual_edits,
    }
    payload = {"prompt": prompt, "input": input_data, "schema": schema}

    cmd = [
        "openclaw.invoke", "--tool", "llm-task", "--action", "json",
        "--agent", args.agent,
        "--args-json", json.dumps(payload),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout + 10)
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "error": f"openclaw.invoke timed out after {args.timeout}s"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"openclaw.invoke failed: {e}"}))
        sys.exit(1)

    if proc.returncode != 0:
        stderr_snippet = proc.stderr[:300] if proc.stderr else ""
        print(json.dumps({"ok": False, "error": f"openclaw.invoke exited {proc.returncode}: {stderr_snippet}"}))
        sys.exit(1)

    stdout = proc.stdout.strip()
    if not stdout:
        print(json.dumps({"ok": False, "error": "openclaw.invoke returned empty output"}))
        sys.exit(1)

    try:
        json.loads(stdout)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"openclaw.invoke output is not valid JSON: {e}"}))
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
