#!/usr/bin/env python3
"""
runner.py — Enforces the JSON-only stdout contract for Lobster integration.

Every script in the memspren sync pipeline must emit valid JSON to stdout.
Lobster parses stdout as a JSON envelope — any stray text, print statement,
or exception traceback breaks the entire run.

This wrapper:
  - Runs the target script with all forwarded arguments
  - Validates stdout is parseable JSON before passing through
  - Routes all stderr output to the telemetry log
  - On success: passes the JSON stdout through unchanged
  - On failure: emits a structured JSON error object to stdout (never crashes)

Usage from Lobster workflow:
    python -m scripts.runner scripts/my_script.py --arg value

The runner is invoked as a module so it resolves from the skill root directory.
"""

import json
import subprocess
import sys
import os
import datetime

TELEMETRY_LOG = os.environ.get(
    "MEMSPREN_TELEMETRY_LOG",
    os.path.join(os.environ.get("MEMORY_PATH", "."), "sync-telemetry.log"),
)
SCRIPT_TIMEOUT = int(os.environ.get("MEMSPREN_SCRIPT_TIMEOUT", "300"))


def log_telemetry(level: str, action: str, result: str, detail: str = "") -> None:
    ts = datetime.datetime.now(datetime.UTC).isoformat()
    entry = f"[{ts}] [{level}] [runner] action={action} result={result}"
    if detail:
        entry += f" detail={detail[:300]}"
    try:
        with open(TELEMETRY_LOG, "a") as f:
            f.write(entry + "\n")
    except OSError:
        pass  # telemetry is best-effort — never crash the runner over logging


def emit_error(error: str, script: str = "", exit_code: int = 1) -> None:
    payload = {"ok": False, "error": error}
    if script:
        payload["script"] = script
    print(json.dumps(payload))
    sys.exit(exit_code)


def main() -> None:
    if len(sys.argv) < 2:
        emit_error("runner: no script specified")

    script_args = sys.argv[1:]
    script_name = script_args[0]

    cmd = [sys.executable] + script_args

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        log_telemetry("ERROR", f"run:{script_name}", "TIMEOUT")
        emit_error(f"runner: script timed out after {SCRIPT_TIMEOUT}s", script_name)
    except Exception as e:
        log_telemetry("ERROR", f"run:{script_name}", "LAUNCH_FAIL", str(e))
        emit_error(f"runner: failed to launch: {e}", script_name)

    # Route stderr to telemetry log
    if proc.stderr:
        log_telemetry("DEBUG", f"stderr:{script_name}", "OK", proc.stderr.strip()[:500])

    stdout = proc.stdout.strip()

    if not stdout:
        log_telemetry("ERROR", f"run:{script_name}", "EMPTY_STDOUT")
        emit_error("runner: script produced no stdout output", script_name)

    try:
        json.loads(stdout)  # Validate — pass through original if valid
    except json.JSONDecodeError as e:
        log_telemetry("ERROR", f"run:{script_name}", "INVALID_JSON")
        emit_error(
            f"runner: stdout is not valid JSON: {e}",
            script_name,
        )

    print(stdout)

    if proc.returncode != 0:
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
