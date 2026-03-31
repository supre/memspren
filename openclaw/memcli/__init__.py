"""Memspren pipeline scripts package.

Defines shared path constants so all sub-packages resolve prompts and schemas
relative to the repo root rather than their own file location.
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent   # memcli/
REPO_ROOT    = PACKAGE_ROOT.parent    # skill root (openclaw/)
PROMPTS_DIR  = REPO_ROOT / "prompts"
SCHEMAS_DIR  = REPO_ROOT / "schemas"
