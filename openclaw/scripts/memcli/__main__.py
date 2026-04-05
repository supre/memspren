#!/usr/bin/env python3
"""
Entry point for `uv run -m scripts.memcli <command> [args...]`.

The Lobster workflow (workflows/sync.lobster) invokes this via:
  uv run -m scripts.memcli <command> [args...]

All real logic lives in memcli/cli.py.
"""
import sys
from pathlib import Path

# Ensure scripts/ is on sys.path so `import memcli` resolves to scripts/memcli/
# regardless of how this file is invoked.
_scripts_dir = Path(__file__).resolve().parent.parent  # openclaw/scripts/
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from memcli.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
