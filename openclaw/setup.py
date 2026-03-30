#!/usr/bin/env python3
"""
One-click bootstrap installer for memcli.

Run EITHER of these to install the package and register the `memcli` command:

    python setup.py install   # traditional install
    pip install -e .          # editable/development install (recommended)

After installation, the `memcli` command is available in your shell:
    memcli --help
    memcli write-lock --help

All project metadata (dependencies, entry points) is in pyproject.toml.
"""
from setuptools import setup

setup()
