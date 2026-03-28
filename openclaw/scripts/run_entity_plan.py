#!/usr/bin/env python3
"""
run_entity_plan.py — Stage 4b entity plan wrapper.

Reads extraction, frontmatter, and task_inbox all from temp files to avoid
shell interpolation of user-authored strings (descriptions, task titles) in
Lobster YAML. All three inputs are written to MEMORY_PATH/run/ by their
respective pipeline steps before this script is called.

Returns JSON to stdout (runner-compatible — no other stdout output).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
# Prompt and schema are fixed for Stage 4b entity plan — not exposed as CLI flags
PROMPT_FILE = SCRIPT_DIR.parent / "prompts" / "entity_plan_prompt.txt"
SCHEMA_FILE = SCRIPT_DIR.parent / "schemas" / "entity_plan_schema.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extraction-file", required=True,
                        help="Path to extraction-output.json saved by run_extraction.py")
    parser.add_argument("--frontmatter-file", default="",
                        help="Path to frontmatter.json saved by read_frontmatter.py")
    parser.add_argument("--task-inbox-file", default="",
                        help="Path to task-inbox.json saved by task_inbox_scanner.py")
    parser.add_argument("--agent", default="memspren-heavy")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    # Read extraction output from file (avoids shell-interpolating large JSON)
    try:
        extraction = json.loads(Path(args.extraction_file).read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"could not read extraction file: {e}"}))
        sys.exit(1)

    frontmatter: list = []
    if args.frontmatter_file:
        try:
            frontmatter = json.loads(Path(args.frontmatter_file).read_text(encoding="utf-8"))
        except Exception:
            frontmatter = []

    task_inbox: dict = {}
    if args.task_inbox_file:
        try:
            task_inbox = json.loads(Path(args.task_inbox_file).read_text(encoding="utf-8"))
        except Exception:
            task_inbox = {}

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
        "extraction":  extraction,
        "frontmatter": frontmatter,
        "task_inbox":  task_inbox,
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

    print(stdout)


if __name__ == "__main__":
    main()
