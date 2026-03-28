#!/usr/bin/env python3
"""
parallel_memory.py — Parallel dispatcher for Stage 2 memory refinement.

Dispatches 4 llm-task jobs simultaneously via ThreadPoolExecutor:
  - insights   (heavy agent) — uses raw_insights + raw_patterns
  - goals      (light agent) — uses raw_goals + task_inbox
  - tasks      (light agent) — uses raw_tasks + task_inbox
  - hot_memory (light agent) — uses raw_goals + raw_tasks

Each job:
  1. Builds input from extraction output + existing memory file content
  2. Calls openclaw.invoke --tool llm-task --args-json with prompt/schema/input payload
  3. Validates output immediately against its schema (jsonschema if available)
  4. On failure: slot returns ok=false, existing file retained by merge.py

Returns JSON to stdout:
{
  "insights":   { "ok": bool, "content": str, "error": str|null },
  "goals":      { "ok": bool, "content": str, "error": str|null },
  "tasks":      { "ok": bool, "content": str, "error": str|null },
  "hot_memory": { "ok": bool, "content": str, "error": str|null }
}
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SCHEMA_DIR = SCRIPT_DIR.parent / "schemas"
PROMPT_DIR = SCRIPT_DIR.parent / "prompts"

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

JOBS = [
    {
        "name":           "insights",
        "agent":          "memspren-heavy",
        "prompt_file":    "insights_prompt.txt",
        "schema_file":    "insights_schema.json",
        "memory_file":    "insights.md",
        "extraction_keys": ["raw_insights", "raw_patterns"],
        "extra_keys":     [],
    },
    {
        "name":           "goals",
        "agent":          "memspren-light",
        "prompt_file":    "goals_prompt.txt",
        "schema_file":    "goals_schema.json",
        "memory_file":    "goals.md",
        "extraction_keys": ["raw_goals"],
        "extra_keys":     ["task_inbox"],
    },
    {
        "name":           "tasks",
        "agent":          "memspren-light",
        "prompt_file":    "tasks_prompt.txt",
        "schema_file":    "tasks_schema.json",
        "memory_file":    "tasks.md",
        "extraction_keys": ["raw_tasks"],
        "extra_keys":     ["task_inbox"],
    },
    {
        "name":           "hot_memory",
        "agent":          "memspren-light",
        "prompt_file":    "hot_memory_prompt.txt",
        "schema_file":    "hot_memory_schema.json",
        "memory_file":    "hot-memory.md",
        "extraction_keys": ["raw_goals", "raw_tasks"],
        "extra_keys":     [],
    },
]


def load_existing(memory_path: Path, filename: str) -> str:
    path = memory_path / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(json.dumps({"warn": f"could not read {filename}: {e}"}), file=sys.stderr)
        return ""


def load_schema(schema_file: str) -> dict | None:
    path = SCHEMA_DIR / schema_file
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def validate(output: dict, schema: dict | None) -> bool:
    if schema is None or not _HAS_JSONSCHEMA:
        return True
    try:
        jsonschema.validate(output, schema)
        return True
    except jsonschema.ValidationError:
        return False


def run_job(
    job: dict,
    extraction: dict,
    memory_path: Path,
    task_inbox: dict,
) -> tuple[str, dict]:
    name = job["name"]

    job_input: dict = {k: extraction.get(k, []) for k in job["extraction_keys"]}
    job_input["existing_content"] = load_existing(memory_path, job["memory_file"])
    for key in job["extra_keys"]:
        if key == "task_inbox":
            job_input["task_inbox"] = task_inbox

    # Read prompt and schema files; build --args-json payload for openclaw.invoke
    try:
        prompt = (PROMPT_DIR / job["prompt_file"]).read_text(encoding="utf-8").strip()
    except Exception as e:
        return name, {"ok": False, "content": "", "error": f"could not read prompt file: {e}"}

    schema_obj = load_schema(job["schema_file"])
    if schema_obj is None:
        return name, {"ok": False, "content": "", "error": f"could not load schema: {job['schema_file']}"}

    payload = {"prompt": prompt, "input": job_input, "schema": schema_obj}

    cmd = [
        "openclaw.invoke", "--tool", "llm-task", "--action", "json",
        "--agent",    job["agent"],
        "--args-json", json.dumps(payload),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
    except subprocess.TimeoutExpired:
        return name, {"ok": False, "content": "", "error": "llm-task timed out (120s)"}
    except Exception as e:
        return name, {"ok": False, "content": "", "error": f"subprocess error: {e}"}

    if proc.returncode != 0:
        return name, {
            "ok": False, "content": "",
            "error": f"openclaw.invoke exited {proc.returncode}: {proc.stderr[:200]}",
        }

    try:
        parsed = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return name, {"ok": False, "content": "", "error": "openclaw.invoke output is not valid JSON"}

    if not validate(parsed, schema_obj):
        return name, {"ok": False, "content": "", "error": "schema validation failed"}

    content = parsed.get("content", "")
    return name, {"ok": True, "content": content, "error": None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extraction-file", required=True,
                        help="Path to extraction-output.json saved by run_extraction.py")
    parser.add_argument("--memory-path", required=True)
    parser.add_argument("--task-inbox-file", default="",
                        help="Path to task-inbox.json saved by task_inbox_scanner.py")
    args = parser.parse_args()

    try:
        extraction = json.loads(Path(args.extraction_file).read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"could not read extraction file: {e}"}))
        sys.exit(1)

    task_inbox: dict = {}
    if args.task_inbox_file:
        try:
            task_inbox = json.loads(Path(args.task_inbox_file).read_text(encoding="utf-8"))
        except Exception:
            task_inbox = {}

    memory_path = Path(args.memory_path)
    results: dict = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_job, job, extraction, memory_path, task_inbox): job["name"]
            for job in JOBS
        }
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result

    print(json.dumps(results))


if __name__ == "__main__":
    main()
