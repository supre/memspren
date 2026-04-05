"""Memspren pipeline scripts package.

Defines shared path constants so all sub-packages resolve prompts and schemas
relative to the package directory (scripts/memcli/prompts/, scripts/memcli/schemas/).
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent          # scripts/memcli/
PROMPTS_DIR  = PACKAGE_ROOT / "prompts"
SCHEMAS_DIR  = PACKAGE_ROOT / "schemas"
