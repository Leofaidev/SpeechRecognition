"""Backup restorer — safety-backup then restore from archive (T-65)."""

from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backup.manager import AppPaths, create_backup


@dataclass
class RestoreResult:
    safety_backup_path: Path
    restored_files: int
    success: bool
    error: str = ""


def restore(
    paths: AppPaths,
    zip_path: Path | str,
    safety_backup_dir: Path | str,
) -> RestoreResult:
    """Restore user data from a backup ZIP.

    Steps (Spec 14.3):
    1. Create a safety backup of the current state.
    2. Extract the archive, overwriting all user-data locations.

    Parameters
    ----------
    paths:
        AppPaths describing current user-data locations.
    zip_path:
        Backup ZIP to restore from.
    safety_backup_dir:
        Directory where the safety backup will be written.

    Returns
    -------
    RestoreResult with safety backup path and file count.
    """
    zip_path = Path(zip_path)
    safety_backup_dir = Path(safety_backup_dir)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safety_zip = safety_backup_dir / f"SRP_safety_{ts}.zip"

    # Step 1: safety backup of current state
    safety_backup_dir.mkdir(parents=True, exist_ok=True)
    create_backup(paths, safety_zip)

    # Step 2: extract the archive
    restored = 0
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.infolist()
            for member in members:
                # Determine destination based on archive name prefix
                dest = _resolve_dest(member.filename, paths)
                if dest is not None:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    restored += 1
    except Exception as exc:
        return RestoreResult(
            safety_backup_path=safety_zip,
            restored_files=restored,
            success=False,
            error=str(exc),
        )

    return RestoreResult(
        safety_backup_path=safety_zip,
        restored_files=restored,
        success=True,
    )


def _resolve_dest(arcname: str, paths: AppPaths) -> Path | None:
    """Map an archive path back to its absolute destination path."""
    parts = arcname.replace("\\", "/").split("/")
    if not parts:
        return None

    prefix = parts[0]
    rest = "/".join(parts[1:])

    if prefix == "config" and rest:
        return paths.config_file.parent / rest
    if prefix == "dictionary" and rest:
        return paths.dictionary_file.parent / rest
    if prefix == paths.library_root.name:
        return paths.library_root.parent / arcname
    if prefix == paths.sessions_dir.name:
        return paths.sessions_dir.parent / arcname

    return None
