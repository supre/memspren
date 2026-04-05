"""Shared vault path resolution.

All modules derive their file paths from a single VaultPaths instance
rather than receiving individual path parameters.
"""

from __future__ import annotations

from pathlib import Path


class VaultPaths:
    """Derives all pipeline paths from the vault root."""

    def __init__(self, vault_path: str | Path):
        self.vault = Path(vault_path)
        self.base = self.vault / ".second-brain"
        self.memory = self.base / "memory"
        self.run = self.base / "run"
        self.buffers = self.base / "buffers"
        self.logs = self.base / "logs"

    def ensure(self) -> None:
        """Create all required directories if they don't exist."""
        for d in (self.memory, self.run, self.buffers, self.logs):
            d.mkdir(parents=True, exist_ok=True)
