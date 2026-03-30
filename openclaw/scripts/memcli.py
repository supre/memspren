#!/usr/bin/env python3
"""
Lobster compatibility shim.

Called by: python -m scripts.runner scripts/memcli.py <command> [args...]

Do NOT delete or rename this file.  The Lobster workflow (workflows/sync.lobster)
invokes this exact path.  All real logic lives in openclaw/scripts/cli.py.
"""
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so the `openclaw` package is importable
# regardless of how this file is invoked.
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from openclaw.scripts.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
