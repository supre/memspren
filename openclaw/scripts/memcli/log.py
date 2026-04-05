"""Structured logging for memcli pipeline.

Each module receives a Logger instance and uses it for all output.
Logs are written to both stderr (for Lobster telemetry) and a daily
log file under /tmp/memcli/.
"""

from __future__ import annotations

import datetime
import json
import sys
from enum import IntEnum
from pathlib import Path


class Level(IntEnum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


LEVEL_NAMES = {
    "debug": Level.DEBUG,
    "info": Level.INFO,
    "warn": Level.WARN,
    "error": Level.ERROR,
}


class Logger:
    def __init__(self, name: str, level: Level = Level.DEBUG, log_dir: Path | None = None):
        self.name = name
        self.level = level
        self.log_path: Path | None = None
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.date.today().isoformat()
            self.log_path = log_dir / f"memcli-{today}.log"

    def _emit(self, lvl: Level, msg: str, **kwargs) -> None:
        if lvl < self.level:
            return
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [{lvl.name}] [{self.name}] {msg}"
        if kwargs:
            # Truncate large values to keep logs readable
            trimmed = {}
            for k, v in kwargs.items():
                s = str(v) if not isinstance(v, str) else v
                trimmed[k] = s[:2000] if len(s) > 2000 else s
            entry += " " + json.dumps(trimmed, default=str)
        print(entry, file=sys.stderr)
        if self.log_path:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(entry + "\n")
            except OSError:
                pass

    def debug(self, msg: str, **kw) -> None:
        self._emit(Level.DEBUG, msg, **kw)

    def info(self, msg: str, **kw) -> None:
        self._emit(Level.INFO, msg, **kw)

    def warn(self, msg: str, **kw) -> None:
        self._emit(Level.WARN, msg, **kw)

    def error(self, msg: str, **kw) -> None:
        self._emit(Level.ERROR, msg, **kw)


def make_logger(name: str, verbosity: str = "debug", log_dir: Path | None = None) -> Logger:
    """Create a Logger with the given verbosity string."""
    level = LEVEL_NAMES.get(verbosity.lower(), Level.DEBUG)
    return Logger(name=name, level=level, log_dir=log_dir)
