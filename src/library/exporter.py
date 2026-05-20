"""Export voice profiles to a ZIP archive (T-49)."""

from __future__ import annotations

import zipfile
from pathlib import Path

from library.storage import LibraryStorage


def export_profiles(
    storage: LibraryStorage,
    folder_names: list[str],
    zip_path: Path | str,
) -> Path:
    """Create a ZIP archive containing the selected speaker subfolders.

    The archive preserves the subfolder structure:
      Smith_John__/speaker.json
      Smith_John__/sample_001.mp3
      Smith_John__/embedding.npy
      ...

    Parameters
    ----------
    storage:
        LibraryStorage for the source library.
    folder_names:
        List of speaker subfolder names to include.
    zip_path:
        Destination ZIP file path.

    Returns
    -------
    The path to the created ZIP file.
    """
    zip_path = Path(zip_path)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for folder_name in folder_names:
            folder = storage.root / folder_name
            if not folder.exists():
                raise FileNotFoundError(f"Profile not found: {folder_name}")
            for file_path in sorted(folder.rglob("*")):
                if file_path.is_file():
                    arcname = folder_name + "/" + file_path.relative_to(folder).as_posix()
                    zf.write(file_path, arcname)

    return zip_path
