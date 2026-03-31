#!/usr/bin/env python3
"""
save_extraction.py - Save extraction output for downstream steps
Reads llm.invoke output from stdin, saves to run/ directory, outputs to stdout.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Save extraction output")
    parser.add_argument("--memory-path", required=True)
    args = parser.parse_args()

    # Read llm.invoke output from stdin
    stdin_text = sys.stdin.read().strip()
    
    if not stdin_text:
        print(json.dumps({"ok": False, "error": "Empty input from llm.invoke"}))
        sys.exit(1)

    try:
        result = json.loads(stdin_text)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid JSON from llm.invoke: {e}"}))
        sys.exit(1)

    # Save to file for entity_plan step
    run_dir = Path(args.memory_path) / "run"
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "extraction-output.json").write_text(json.dumps(result), encoding="utf-8")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Could not save extraction output: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Pass through to stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()
