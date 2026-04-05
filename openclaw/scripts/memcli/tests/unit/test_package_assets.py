"""Tests that prompts and schemas resolve correctly from the package directory.

These guard against path regressions — if PROMPTS_DIR or SCHEMAS_DIR ever
points to the wrong location, every LLM pipeline step breaks silently at
runtime rather than at test time.
"""
from __future__ import annotations

import json

import pytest

from memcli import PROMPTS_DIR, SCHEMAS_DIR

EXPECTED_PROMPTS = [
    "extraction_prompt.txt",
    "insights_prompt.txt",
    "goals_prompt.txt",
    "hot_memory_prompt.txt",
    "tasks_prompt.txt",
    "entity_plan_prompt.txt",
    "entity_content_prompt.txt",
    "entity_linking_prompt.txt",
]

EXPECTED_SCHEMAS = [
    "extraction_schema.json",
    "insights_schema.json",
    "goals_schema.json",
    "hot_memory_schema.json",
    "tasks_schema.json",
    "entity_plan_schema.json",
    "entity_content_schema.json",
    "entity_linking_schema.json",
]


def test_prompts_dir_exists():
    assert PROMPTS_DIR.is_dir(), f"PROMPTS_DIR not found: {PROMPTS_DIR}"


def test_schemas_dir_exists():
    assert SCHEMAS_DIR.is_dir(), f"SCHEMAS_DIR not found: {SCHEMAS_DIR}"


@pytest.mark.parametrize("filename", EXPECTED_PROMPTS)
def test_prompt_file_exists(filename):
    path = PROMPTS_DIR / filename
    assert path.is_file(), f"Missing prompt: {path}"


@pytest.mark.parametrize("filename", EXPECTED_SCHEMAS)
def test_schema_file_is_valid_json(filename):
    path = SCHEMAS_DIR / filename
    assert path.is_file(), f"Missing schema: {path}"
    data = json.loads(path.read_text())
    assert isinstance(data, dict), f"Schema is not a JSON object: {path}"


@pytest.mark.parametrize("filename", EXPECTED_PROMPTS)
def test_prompt_file_is_nonempty(filename):
    path = PROMPTS_DIR / filename
    assert path.read_text().strip(), f"Prompt file is empty: {path}"
