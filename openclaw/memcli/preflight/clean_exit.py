#!/usr/bin/env python3
"""
clean_exit.py — Emit a clean exit signal for Lobster when there is nothing to sync.

Optionally releases the sync lock before exiting.

Returns JSON to stdout:
  { "ok": true, "action": "exit", "message": str }
"""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="Nothing to sync.")
    parser.add_argument("--release-lock", action="store_true")
    parser.add_argument("--memory-path", default=None)
    args = parser.parse_args()

    if args.release_lock and args.memory_path:
        lock_path = Path(args.memory_path) / "sync.lock"
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            pass

    print(json.dumps({"ok": True, "action": "exit", "message": args.message}))


if __name__ == "__main__":
    main()
