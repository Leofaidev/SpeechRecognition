"""Unit tests for library.exporter/importer — CHK-66, 67."""

import numpy as np
import pytest
from pathlib import Path

from library.exporter import export_profiles
from library.importer import import_profiles
from library.profile_creator import ProfileCreator, ConflictMode
from library.storage import LibraryStorage
from library.groups import LibraryGroups


_SR = 16_000


def _fake_embed(audio: np.ndarray, sr: int) -> np.ndarray:
    return np.ones(192, dtype=np.float32)


def _make_audio(seconds: float = 10.0) -> np.ndarray:
    return np.zeros(int(seconds * _SR), dtype=np.float32)


def _create_profile(storage, last, first, groups=None):
    creator = ProfileCreator(storage, embedding_fn=_fake_embed, model_checksum="v1")
    f, meta = creator.create(_make_audio(), _SR, last=last, first=first)
    if groups:
        lib_groups = LibraryGroups(storage)
        for g in groups:
            lib_groups.add_to_group(f, g)
    return f


# ---------------------------------------------------------------------------
# CHK-66: Import triggers retraining_required flag
# ---------------------------------------------------------------------------

def test_import_sets_retraining_required(tmp_path):
    src_lib = tmp_path / "source"
    dst_lib = tmp_path / "dest"

    src_storage = LibraryStorage(src_lib)
    dst_storage = LibraryStorage(dst_lib)

    f1 = _create_profile(src_storage, "Alice", "A")
    zip_path = tmp_path / "export.zip"
    export_profiles(src_storage, [f1], zip_path)

    result = import_profiles(dst_storage, zip_path)
    assert result.retraining_required is True


def test_import_exports_basic_profile(tmp_path):
    src_storage = LibraryStorage(tmp_path / "src")
    dst_storage = LibraryStorage(tmp_path / "dst")

    f1 = _create_profile(src_storage, "Alice", "A")
    zip_path = tmp_path / "export.zip"
    export_profiles(src_storage, [f1], zip_path)

    result = import_profiles(dst_storage, zip_path)
    assert result.imported == 1
    assert (tmp_path / "dst" / f1).exists()


# ---------------------------------------------------------------------------
# CHK-67: Imported profile with unknown group → group created automatically
# ---------------------------------------------------------------------------

def test_import_creates_missing_groups(tmp_path):
    src_storage = LibraryStorage(tmp_path / "src")
    dst_storage = LibraryStorage(tmp_path / "dst")

    # Create profile in source library that belongs to "SpecialTeam"
    f1 = _create_profile(src_storage, "Bob", "B", groups=["SpecialTeam"])
    zip_path = tmp_path / "export.zip"
    export_profiles(src_storage, [f1], zip_path)

    result = import_profiles(dst_storage, zip_path)

    # "SpecialTeam" didn't exist in dst; should be listed in created_groups
    assert "SpecialTeam" in result.created_groups


def test_import_group_not_duplicated_if_exists(tmp_path):
    src_storage = LibraryStorage(tmp_path / "src")
    dst_storage = LibraryStorage(tmp_path / "dst")

    # Create an existing profile in dest that already has "ExistingGroup"
    dst_creator = ProfileCreator(dst_storage, embedding_fn=_fake_embed)
    f_dst, _ = dst_creator.create(_make_audio(), _SR, last="Carol", first="C")
    LibraryGroups(dst_storage).add_to_group(f_dst, "ExistingGroup")

    # Source also has a profile in "ExistingGroup"
    f_src = _create_profile(src_storage, "Dave", "D", groups=["ExistingGroup"])
    zip_path = tmp_path / "export.zip"
    export_profiles(src_storage, [f_src], zip_path)

    result = import_profiles(dst_storage, zip_path)
    # ExistingGroup already exists — should NOT be in created_groups
    assert "ExistingGroup" not in result.created_groups


# ---------------------------------------------------------------------------
# Export basics
# ---------------------------------------------------------------------------

def test_export_creates_zip(tmp_path):
    storage = LibraryStorage(tmp_path / "lib")
    f1 = _create_profile(storage, "Alice", "A")
    zip_path = tmp_path / "out.zip"
    export_profiles(storage, [f1], zip_path)
    assert zip_path.exists()


def test_export_zip_contains_speaker_json(tmp_path):
    import zipfile
    storage = LibraryStorage(tmp_path / "lib")
    f1 = _create_profile(storage, "Alice", "A")
    zip_path = tmp_path / "out.zip"
    export_profiles(storage, [f1], zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert any("speaker.json" in n for n in names)


def test_export_missing_profile_raises(tmp_path):
    storage = LibraryStorage(tmp_path / "lib")
    zip_path = tmp_path / "out.zip"
    with pytest.raises(FileNotFoundError):
        export_profiles(storage, ["NonExistent_A__"], zip_path)


# ---------------------------------------------------------------------------
# Import conflict modes
# ---------------------------------------------------------------------------

def test_import_reject_skips_existing(tmp_path):
    storage = LibraryStorage(tmp_path / "lib")
    f1 = _create_profile(storage, "Alice", "A")

    zip_path = tmp_path / "out.zip"
    export_profiles(storage, [f1], zip_path)

    result = import_profiles(storage, zip_path, conflict_mode=ConflictMode.REJECT)
    assert result.skipped == 1
    assert result.imported == 0
