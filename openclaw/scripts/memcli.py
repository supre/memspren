#!/usr/bin/env python3
"""
Lobster compatibility shim.

Called by: python -m scripts.runner scripts/memcli.py <command> [args...]

Do NOT delete or rename this file.  The Lobster workflow (workflows/sync.lobster)
invokes this exact path.  All real logic lives in memcli/cli.py.
"""
import sys
from pathlib import Path

# Ensure the skill root is on sys.path so the `memcli` package is importable
# regardless of how this file is invoked.
_skill_root = Path(__file__).resolve().parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))

from memcli.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
