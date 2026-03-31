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
import os
import sys
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR

# Prompt and schema are fixed for Stage 4b entity plan — not exposed as CLI flags
PROMPT_FILE = PROMPTS_DIR / "entity_plan_prompt.txt"
SCHEMA_FILE = SCHEMAS_DIR / "entity_plan_schema.json"


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

    # Load prompt and schema
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

    gateway_url   = os.environ.get("OPENCLAW_URL", "http://127.0.0.1:18789")
    gateway_token = os.environ.get("OPENCLAW_TOKEN", "")
    endpoint      = gateway_url.rstrip("/") + "/tools/invoke"

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {
            "prompt":    prompt,
            "input":     {"extraction": extraction, "frontmatter": frontmatter, "task_inbox": task_inbox},
            "schema":    schema,
            "agent":     args.agent,
            "timeoutMs": args.timeout * 1000,
        },
    }

    try:
        result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=args.timeout)
    except RuntimeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)

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
        print(json.dumps({"ok": False, "error": f"could not parse gateway response: {exc}", "raw": str(result)[:300]}))
        sys.exit(1)

    print(json.dumps(output))


if __name__ == "__main__":
    main()
