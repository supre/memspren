"""memcli — re-exported from cli for backward-compatible imports.

Existing tests import ``from openclaw.scripts import memcli`` and call
``memcli.main()``.  This shim keeps that interface working.
"""

from .cli import cli, main  # noqa: F401
