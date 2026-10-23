from pathlib import Path

import pytest

from cibmangotree.app.storage_migration import (
    StorageMigrationStatus,
    storage_directory_migration,
)


def make_app_dir(path: Path) -> Path:
    """Create a folder that looks like real app data."""
    (path / "projects" / "my_project").mkdir(parents=True)
    (path / "db.json").write_text('{"marker": "old"}')
    return path


def test_not_found_when_old_missing(tmp_path):
    result = storage_directory_migration(tmp_path / "old", tmp_path / "new")

    assert result is StorageMigrationStatus.NOT_FOUND
    assert not (tmp_path / "new").exists()


def test_moves_old_to_new(tmp_path):
    old = make_app_dir(tmp_path / "old")
    new = tmp_path / "new"

    result = storage_directory_migration(old, new)

    assert result is StorageMigrationStatus.MOVED
    assert not old.exists()
    assert (new / "db.json").read_text() == '{"marker": "old"}'
    assert (new / "projects" / "my_project").is_dir()


def test_conflict_leaves_both_untouched(tmp_path):
    old = make_app_dir(tmp_path / "old")
    new = tmp_path / "new"
    new.mkdir()
    (new / "db.json").write_text('{"marker": "new"}')

    result = storage_directory_migration(old, new)

    assert result is StorageMigrationStatus.CONFLICT
    assert (old / "db.json").read_text() == '{"marker": "old"}'
    assert (new / "db.json").read_text() == '{"marker": "new"}'


def test_error_keeps_old_intact(tmp_path, monkeypatch):
    old = make_app_dir(tmp_path / "old")

    def fail(*args, **kwargs):
        raise PermissionError("file in use")

    monkeypatch.setattr(Path, "rename", fail)

    result = storage_directory_migration(old, tmp_path / "new")

    assert result is StorageMigrationStatus.ERROR
    assert (old / "db.json").exists()


def test_second_run_does_nothing(tmp_path):
    old = make_app_dir(tmp_path / "old")
    new = tmp_path / "new"

    storage_directory_migration(old, new)
    result = storage_directory_migration(old, new)

    assert result is StorageMigrationStatus.NOT_FOUND
    assert (new / "db.json").exists()
