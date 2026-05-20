"""Import voice profiles from a ZIP archive (T-50).

Rules (Spec 5.5.b–c):
- Conflicts resolved via ConflictMode passed by caller.
- Groups that do not exist on the target are created automatically.
- After completion, sets a retraining_required flag.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from library.profile_creator import ConflictMode
from library.storage import LibraryStorage, SpeakerMeta


@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    conflicts_resolved: int = 0
    retraining_required: bool = False
    created_groups: list[str] = field(default_factory=list)


def import_profiles(
    storage: LibraryStorage,
    zip_path: Path | str,
    conflict_mode: ConflictMode = ConflictMode.REJECT,
) -> ImportResult:
    """Unpack *zip_path* and import all contained speaker profiles.

    Parameters
    ----------
    storage:
        Destination LibraryStorage.
    zip_path:
        Source ZIP file (created by ``exporter.export_profiles``).
    conflict_mode:
        How to handle profiles that already exist in the target library.

    Returns
    -------
    ImportResult summary.
    """
    zip_path = Path(zip_path)
    result = ImportResult()
    created_groups: set[str] = set()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)

        # Each top-level directory in the ZIP is a speaker subfolder
        for profile_dir in sorted(tmp_path.iterdir()):
            if not profile_dir.is_dir():
                continue
            json_path = profile_dir / "speaker.json"
            if not json_path.exists():
                continue

            folder_name = profile_dir.name
            dest_folder = storage.root / folder_name
            already_exists = dest_folder.exists() and (dest_folder / "speaker.json").exists()

            if already_exists:
                if conflict_mode == ConflictMode.REJECT:
                    result.skipped += 1
                    continue
                elif conflict_mode == ConflictMode.OVERWRITE:
                    shutil.rmtree(dest_folder)
                    result.conflicts_resolved += 1
                # MERGE: handled below by copying new samples alongside existing

            # Determine which groups don't yet exist BEFORE importing
            with json_path.open(encoding="utf-8") as fh:
                incoming_meta = json.load(fh)
            for grp in incoming_meta.get("groups", []):
                if not _group_exists(storage, grp):
                    created_groups.add(grp)

            # Copy the folder to the library root
            if not dest_folder.exists():
                shutil.copytree(profile_dir, dest_folder)
                result.imported += 1
            else:
                # Merge: copy new files only (skip existing)
                for f in profile_dir.iterdir():
                    dest_file = dest_folder / f.name
                    if not dest_file.exists():
                        shutil.copy2(f, dest_file)
                # Merge sample lists in speaker.json
                _merge_json(dest_folder / "speaker.json", json_path)
                result.conflicts_resolved += 1
                result.imported += 1

    result.retraining_required = True  # always after import (Spec 5.5.c)
    result.created_groups = sorted(created_groups)
    return result


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _group_exists(storage: LibraryStorage, group_name: str) -> bool:
    for pp in storage.list_profiles():
        meta = storage.read_meta(pp.name)
        if group_name in meta.groups:
            return True
    return False


def _merge_json(dest_json: Path, src_json: Path) -> None:
    """Merge sample list from *src_json* into *dest_json* (no duplicates)."""
    with dest_json.open(encoding="utf-8") as fh:
        dest = json.load(fh)
    with src_json.open(encoding="utf-8") as fh:
        src = json.load(fh)

    existing = set(dest.get("samples", []))
    for s in src.get("samples", []):
        if s not in existing:
            dest.setdefault("samples", []).append(s)
            existing.add(s)
    dest["sample_count"] = len(dest.get("samples", []))

    with dest_json.open("w", encoding="utf-8") as fh:
        json.dump(dest, fh, indent=2, ensure_ascii=False)
