from enum import Enum
from pathlib import Path


class StorageMigrationStatus(Enum):
    NOT_FOUND = "not_found"
    MOVED = "moved"
    CONFLICT = "conflict"
    ERROR = "error"


def storage_directory_migration(old: Path, new: Path) -> StorageMigrationStatus:
    if not old.exists():
        return StorageMigrationStatus.NOT_FOUND

    # Move to new storage
    try:
        if new.exists():
            if any(new.iterdir()):
                return StorageMigrationStatus.CONFLICT
            new.rmdir()

        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)

    except OSError:
        return StorageMigrationStatus.ERROR

    return StorageMigrationStatus.MOVED
