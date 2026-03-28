#!/usr/bin/env python3
"""
prepare_extraction.py - Prepare extraction input for llm.invoke
Reads buffer content and manual edits, outputs JSON payload for llm.invoke.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Prepare extraction input")
    parser.add_argument("--buffer-content-file", required=True)
    parser.add_argument("--manual-edits-file", required=True)
    args = parser.parse_args()

    buffer_path = Path(args.buffer_content_file)
    edits_path = Path(args.manual_edits_file)

    if not buffer_path.exists():
        print(json.dumps({"error": f"Buffer file not found: {buffer_path}"}), file=sys.stderr)
        sys.exit(1)

    buffer_content = buffer_path.read_text(encoding="utf-8")
    manual_edits = edits_path.read_text(encoding="utf-8") if edits_path.exists() else ""

    # Load schema
    script_dir = Path(__file__).parent
    schema_file = script_dir.parent / "schemas" / "extraction_schema.json"
    
    if not schema_file.exists():
        print(json.dumps({"error": f"Schema file not found: {schema_file}"}), file=sys.stderr)
        sys.exit(1)
    
    schema = json.loads(schema_file.read_text(encoding="utf-8"))

    # Output payload for llm.invoke
    payload = {
        "input": {
            "buffer_content": buffer_content,
            "manual_edits": manual_edits
        },
        "schema": schema
    }

    print(json.dumps(payload))


if __name__ == "__main__":
    main()
