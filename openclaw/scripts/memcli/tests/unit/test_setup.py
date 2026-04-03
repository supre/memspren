"""Unit tests for memcli.setup — idempotent vault scaffold."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest

from memcli.log import make_logger
from memcli.setup import MEMORY_STUBS, SEED_FILES, VAULT_FOLDERS, run


@pytest.fixture
def tmp_vault(tmp_path: Path) -> Path:
    """Return an empty directory in /tmp to use as the vault root."""
    vault = tmp_path / "test-vault"
    vault.mkdir()
    return vault


@pytest.fixture
def log():
    return make_logger("test-setup")


# ── Folder creation ────────────────────────────────────────────────────────

def test_creates_all_vault_folders(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    for folder in VAULT_FOLDERS:
        assert (tmp_vault / folder).is_dir(), f"Missing folder: {folder}"


def test_idempotent_folder_creation(tmp_vault, log):
    """Calling run twice should not raise or duplicate anything."""
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    for folder in VAULT_FOLDERS:
        assert (tmp_vault / folder).is_dir()


# ── Seed file creation ─────────────────────────────────────────────────────

def test_creates_seed_files(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    for rel_path in SEED_FILES:
        assert (tmp_vault / rel_path).exists(), f"Missing seed file: {rel_path}"


def test_seed_files_have_frontmatter(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    for rel_path in SEED_FILES:
        content = (tmp_vault / rel_path).read_text(encoding="utf-8")
        assert content.startswith("---"), f"{rel_path} missing YAML frontmatter"


def test_does_not_overwrite_existing_seed_file(tmp_vault, log):
    """Seed files should never overwrite existing user content."""
    vision = tmp_vault / "Vision"
    vision.mkdir(parents=True)
    existing = vision / "long-term-vision.md"
    existing.write_text("My existing vision content", encoding="utf-8")

    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert existing.read_text(encoding="utf-8") == "My existing vision content"


# ── Memory stubs ───────────────────────────────────────────────────────────

def test_creates_memory_stubs(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    memory_dir = tmp_vault / ".second-brain" / "memory"
    for filename in MEMORY_STUBS:
        assert (memory_dir / filename).exists(), f"Missing memory stub: {filename}"


def test_does_not_overwrite_existing_memory_stub(tmp_vault, log):
    """Existing memory files (e.g. after first check-in) should not be overwritten."""
    sb = tmp_vault / ".second-brain"
    (sb / "memory").mkdir(parents=True)
    existing = sb / "memory" / "insights.md"
    existing.write_text("Existing insights content", encoding="utf-8")

    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert existing.read_text(encoding="utf-8") == "Existing insights content"


# ── .gitignore ─────────────────────────────────────────────────────────────

def test_creates_gitignore(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    gitignore = tmp_vault / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    assert ".DS_Store" in content


def test_does_not_overwrite_existing_gitignore(tmp_vault, log):
    existing = tmp_vault / ".gitignore"
    existing.write_text("my-custom-ignore\n", encoding="utf-8")
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert existing.read_text(encoding="utf-8") == "my-custom-ignore\n"


# ── Git init ───────────────────────────────────────────────────────────────

def test_initializes_git(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert (tmp_vault / ".git").is_dir()


def test_git_already_initialized_is_skipped(tmp_vault, log):
    """If .git already exists, run() must not reinitialize (idempotent)."""
    subprocess.run(["git", "init"], cwd=str(tmp_vault), capture_output=True)
    result = run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert result["git_initialized"] is False


# ── Return value ───────────────────────────────────────────────────────────

def test_returns_ok_true(tmp_vault, log):
    result = run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert result["ok"] is True


def test_returns_created_lists(tmp_vault, log):
    result = run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert isinstance(result["folders_created"], list)
    assert isinstance(result["files_created"], list)
    assert len(result["folders_created"]) == len(VAULT_FOLDERS)


def test_second_run_creates_nothing_new(tmp_vault, log):
    run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    result2 = run(vault_path=tmp_vault, vault_name="TestVault", log=log)
    assert result2["folders_created"] == []
    assert result2["files_created"] == []
    assert result2["git_initialized"] is False
