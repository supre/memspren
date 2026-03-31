"""parallel_memory.py — Parallel dispatcher for Stage 2 memory refinement."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import gateway_client
from .. import PROMPTS_DIR, SCHEMAS_DIR
from ..gateway import get_gateway_token, get_gateway_endpoint
from ..log import Logger
from ..paths import VaultPaths

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

JOBS = [
    {
        "name": "insights",
        "agent": "memspren-heavy",
        "prompt_file": "insights_prompt.txt",
        "schema_file": "insights_schema.json",
        "memory_file": "insights.md",
        "extraction_keys": ["raw_insights", "raw_patterns"],
        "extra_keys": [],
    },
    {
        "name": "goals",
        "agent": "memspren-light",
        "prompt_file": "goals_prompt.txt",
        "schema_file": "goals_schema.json",
        "memory_file": "goals.md",
        "extraction_keys": ["raw_goals"],
        "extra_keys": ["task_inbox"],
    },
    {
        "name": "tasks",
        "agent": "memspren-light",
        "prompt_file": "tasks_prompt.txt",
        "schema_file": "tasks_schema.json",
        "memory_file": "tasks.md",
        "extraction_keys": ["raw_tasks"],
        "extra_keys": ["task_inbox"],
    },
    {
        "name": "hot_memory",
        "agent": "memspren-light",
        "prompt_file": "hot_memory_prompt.txt",
        "schema_file": "hot_memory_schema.json",
        "memory_file": "hot-memory.md",
        "extraction_keys": ["raw_goals", "raw_tasks"],
        "extra_keys": [],
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
    path = SCHEMAS_DIR / schema_file
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
    log: Logger,
) -> tuple[str, dict]:
    name = job["name"]
    log.debug(f"starting job: {name}", agent=job["agent"])

    gateway_token = get_gateway_token()
    job_input: dict = {k: extraction.get(k, []) for k in job["extraction_keys"]}
    job_input["existing_content"] = load_existing(memory_path, job["memory_file"])
    for key in job["extra_keys"]:
        if key == "task_inbox":
            job_input["task_inbox"] = task_inbox

    try:
        prompt = (PROMPTS_DIR / job["prompt_file"]).read_text(encoding="utf-8").strip()
    except Exception as e:
        log.error(f"could not read prompt file for {name}", error=str(e))
        return name, {"ok": False, "content": "", "error": f"could not read prompt file: {e}"}

    schema_obj = load_schema(job["schema_file"])
    if schema_obj is None:
        return name, {"ok": False, "content": "", "error": f"could not load schema: {job['schema_file']}"}

    payload = {
        "tool": "llm-task",
        "action": "invoke",
        "args": {"prompt": prompt, "input": job_input, "schema": schema_obj, "timeoutMs": 120000},
    }

    endpoint = get_gateway_endpoint()

    try:
        result = gateway_client.post_json(endpoint, payload, token=gateway_token, timeout=130)
    except RuntimeError as exc:
        log.error(f"gateway error for {name}", error=str(exc))
        return name, {"ok": False, "content": "", "error": str(exc)}

    if isinstance(result, dict) and result.get("ok") == False:
        error_msg = result.get("error", {}).get("message", "Unknown error")
        log.error(f"gateway returned error for {name}", error=error_msg)
        return name, {"ok": False, "content": "", "error": f"Gateway error: {error_msg}"}

    if isinstance(result, dict) and "result" in result:
        if "details" in result["result"] and "json" in result["result"]["details"]:
            output = result["result"]["details"]["json"]
        else:
            output = result["result"]
    else:
        output = result

    if not validate(output, schema_obj):
        log.warn(f"schema validation failed for {name}")
        return name, {"ok": False, "content": "", "error": "output failed schema validation"}

    if isinstance(output, dict) and "content" in output:
        content = output["content"]
    elif isinstance(output, str):
        content = output
    else:
        content = json.dumps(output)

    log.info(f"job {name} succeeded", content_len=len(content))
    return name, {"ok": True, "content": content, "error": None}


def run(
    *,
    vault_path: Path,
    extraction_file: Path,
    task_inbox_file: Path,
    log: Logger,
) -> dict:
    paths = VaultPaths(vault_path)

    if not extraction_file.exists():
        raise RuntimeError(f"Extraction file not found: {extraction_file}")
    if not task_inbox_file.exists():
        raise RuntimeError(f"Task inbox file not found: {task_inbox_file}")

    try:
        extraction = json.loads(extraction_file.read_text(encoding="utf-8"))
        task_inbox = json.loads(task_inbox_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Failed to load input files: {e}") from e

    log.info("starting parallel memory refinement", jobs=len(JOBS))

    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_job, job, extraction, paths.memory, task_inbox, log): job["name"]
            for job in JOBS
        }
        for future in as_completed(futures):
            name, result = future.result()
            results[name] = result

    ok_count = sum(1 for r in results.values() if r.get("ok"))
    log.info("parallel memory complete", ok=ok_count, failed=len(JOBS) - ok_count)
    return results
