"""Backup manager — create ZIP archive of all user data (T-64)."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppPaths:
    """Paths to all user-data locations that must be included in a backup."""
    config_file: Path
    dictionary_file: Path
    library_root: Path
    sessions_dir: Path
    install_dir: Path  # used for "backup inside install folder" warning


@dataclass
class BackupResult:
    zip_path: Path
    estimated_size: int   # sum of source file sizes before compression (bytes)
    actual_size: int      # final ZIP size on disk (bytes)
    path_warning: bool    # True if zip_path is inside install_dir
    files_backed_up: int


def create_backup(paths: AppPaths, zip_path: Path | str) -> BackupResult:
    """Create a ZIP backup of all user data.

    Parameters
    ----------
    paths:
        AppPaths describing all data locations.
    zip_path:
        Destination ZIP file path.

    Returns
    -------
    BackupResult with size estimates and a warning flag if the backup
    location is inside the installation directory.
    """
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect all files to backup
    files_to_backup: list[tuple[Path, str]] = []  # (absolute_path, archive_name)

    def _add(source: Path, arcname: str) -> None:
        if source.is_file():
            files_to_backup.append((source, arcname))
        elif source.is_dir():
            for f in sorted(source.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(source.parent).as_posix()
                    files_to_backup.append((f, rel))

    _add(paths.config_file, "config/" + paths.config_file.name)
    _add(paths.dictionary_file, "dictionary/" + paths.dictionary_file.name)
    _add(paths.library_root, str(paths.library_root.name))
    _add(paths.sessions_dir, str(paths.sessions_dir.name))

    # Estimated size = sum of uncompressed sizes
    estimated = sum(f.stat().st_size for f, _ in files_to_backup if f.exists())

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path, arcname in files_to_backup:
            if file_path.exists():
                zf.write(file_path, arcname)

    actual = zip_path.stat().st_size

    # Check if zip_path is inside install_dir
    try:
        zip_path.resolve().relative_to(paths.install_dir.resolve())
        path_warning = True
    except ValueError:
        path_warning = False

    return BackupResult(
        zip_path=zip_path,
        estimated_size=estimated,
        actual_size=actual,
        path_warning=path_warning,
        files_backed_up=len(files_to_backup),
    )


def estimated_backup_size(paths: AppPaths) -> int:
    """Return the sum of source file sizes without creating the ZIP."""
    total = 0
    for source in [paths.config_file, paths.dictionary_file,
                   paths.library_root, paths.sessions_dir]:
        if source.is_file():
            total += source.stat().st_size
        elif source.is_dir():
            total += sum(f.stat().st_size for f in source.rglob("*") if f.is_file())
    return total
