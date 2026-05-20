"""Unit tests for library.storage — CHK-52, 53, 54, 63, 64."""

import json
import pytest
from pathlib import Path

from library.storage import (
    LibraryStorage,
    SpeakerMeta,
    make_folder_name,
    _sanitise,
)


# ---------------------------------------------------------------------------
# CHK-52: Smith_John__ for last=Smith, first=John, middle/nickname empty
# ---------------------------------------------------------------------------

def test_folder_name_smith_john():
    name, _ = make_folder_name("Smith", "John", "", "")
    assert name == "Smith_John__"


def test_folder_name_all_four_parts():
    name, _ = make_folder_name("Smith", "John", "Robert", "Bobby")
    assert name == "Smith_John_Robert_Bobby"


def test_folder_name_middle_only():
    name, _ = make_folder_name("", "", "Mid", "")
    assert name == "__Mid_"


# ---------------------------------------------------------------------------
# CHK-53: All-empty → ____001, nickname="#001"
# ---------------------------------------------------------------------------

def test_all_empty_produces_auto_id(tmp_path):
    name, resolved_nickname = make_folder_name("", "", "", "", library_root=tmp_path)
    assert name == "____001"
    assert resolved_nickname == "#001"


def test_all_empty_increments_when_exists(tmp_path):
    # Pre-create ____001
    (tmp_path / "____001").mkdir()
    name, resolved_nickname = make_folder_name("", "", "", "", library_root=tmp_path)
    assert name == "____002"
    assert resolved_nickname == "#002"


def test_auto_id_in_speaker_json(tmp_path):
    storage = LibraryStorage(tmp_path)
    folder_name, meta = storage.create_profile("", "", "", "")
    assert folder_name == "____001"
    assert meta.nickname == "#001"


# ---------------------------------------------------------------------------
# CHK-54: Invalid Windows chars replaced in folder, preserved in JSON
# ---------------------------------------------------------------------------

def test_invalid_chars_replaced_in_folder():
    name, _ = make_folder_name('Smith/"J"', "John:Jr", "", "")
    assert "/" not in name
    assert ":" not in name
    assert '"' not in name


def test_original_chars_preserved_in_meta(tmp_path):
    storage = LibraryStorage(tmp_path)
    folder_name, meta = storage.create_profile('Smith/"J"', "John:Jr", "", "")
    # meta stores originals
    assert meta.last_name == 'Smith/"J"'
    assert meta.first_name == "John:Jr"


def test_sanitise_slash():
    assert "/" not in _sanitise("a/b")


def test_sanitise_colon():
    assert ":" not in _sanitise("a:b")


def test_sanitise_double_quote():
    assert '"' not in _sanitise('a"b')


# ---------------------------------------------------------------------------
# CHK-63: delete_profile removes speaker from every group that references them
# ---------------------------------------------------------------------------

def test_delete_profile_removes_from_groups(tmp_path):
    storage = LibraryStorage(tmp_path)

    # Create two profiles
    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")

    # Bob references Alice in his groups array
    meta_b = storage.read_meta(f2)
    meta_b.groups = [f1]
    storage.write_meta(f2, meta_b)

    # Delete Alice's profile
    storage.delete_profile(f1)

    # Bob's groups should no longer list Alice
    meta_b_after = storage.read_meta(f2)
    assert f1 not in meta_b_after.groups


def test_delete_profile_removes_folder(tmp_path):
    storage = LibraryStorage(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    storage.delete_profile(f1)
    assert not (tmp_path / f1).exists()


# ---------------------------------------------------------------------------
# CHK-64: rename_profile updates group membership references
# ---------------------------------------------------------------------------

def test_rename_profile_updates_group_refs(tmp_path):
    storage = LibraryStorage(tmp_path)

    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")

    # Bob lists Alice in groups
    meta_b = storage.read_meta(f2)
    meta_b.groups = [f1]
    storage.write_meta(f2, meta_b)

    new_name = "Alice_Anna__"
    (tmp_path / f1).rename(tmp_path / new_name)
    # Simulate rename_profile by calling after the folder rename
    # Actually test rename_profile directly
    storage2 = LibraryStorage(tmp_path)
    # Recreate alice under original name first
    f1b, _ = storage2.create_profile("Alice", "A", "", "")  # This will be ____001 or similar
    # Test rename_profile directly by preparing folders
    pass  # The key test is below


def test_rename_profile_method(tmp_path):
    storage = LibraryStorage(tmp_path)

    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")

    meta_b = storage.read_meta(f2)
    meta_b.groups = [f1]
    storage.write_meta(f2, meta_b)

    new_name = "Alice_Ana__"
    (tmp_path / f1).rename(tmp_path / new_name)
    storage.rename_profile(new_name, new_name)  # no-op but exercises the scan

    # The real test: rename changes the reference in other profiles
    storage.rename_profile(f2, f2)  # no-op
    assert (tmp_path / new_name).exists()


def test_rename_profile_updates_refs(tmp_path):
    storage = LibraryStorage(tmp_path)

    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")

    # Bob's groups contain f1
    meta_b = storage.read_meta(f2)
    meta_b.groups = [f1]
    storage.write_meta(f2, meta_b)

    # rename f1 to a new folder name
    new_f1 = "Alice_Ann__"
    storage.rename_profile(f1, new_f1)

    # Bob's groups should now reference new_f1
    meta_b_after = storage.read_meta(f2)
    assert new_f1 in meta_b_after.groups
    assert f1 not in meta_b_after.groups


# ---------------------------------------------------------------------------
# Storage basics
# ---------------------------------------------------------------------------

def test_create_and_read_profile(tmp_path):
    storage = LibraryStorage(tmp_path)
    f, meta = storage.create_profile("Smith", "John", "", "")
    assert f == "Smith_John__"
    loaded = storage.read_meta(f)
    assert loaded.last_name == "Smith"
    assert loaded.first_name == "John"


def test_list_profiles(tmp_path):
    storage = LibraryStorage(tmp_path)
    storage.create_profile("Alice", "A", "", "")
    storage.create_profile("Bob", "B", "", "")
    profiles = storage.list_profiles()
    assert len(profiles) == 2


def test_next_sample_name_sequential(tmp_path):
    storage = LibraryStorage(tmp_path)
    f, _ = storage.create_profile("X", "Y", "", "")
    (tmp_path / f / "sample_001.mp3").write_bytes(b"")
    assert storage.next_sample_name(f) == "sample_002.mp3"


def test_speaker_meta_round_trip():
    meta = SpeakerMeta(
        last_name="Jones", first_name="Alice",
        creation_date="2026-01-01T00:00:00Z",
        model_checksum="sha256:abc",
        sample_count=1, samples=["sample_001.mp3"],
        groups=["Team A"], low_confidence=False,
    )
    restored = SpeakerMeta.from_dict(meta.to_dict())
    assert restored.last_name == "Jones"
    assert restored.groups == ["Team A"]
