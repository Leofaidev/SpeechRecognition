"""Unit tests for library.groups — CHK-62."""

import pytest
from library.storage import LibraryStorage
from library.groups import LibraryGroups


def _make_lib(tmp_path):
    storage = LibraryStorage(tmp_path)
    groups = LibraryGroups(storage)
    return storage, groups


# ---------------------------------------------------------------------------
# CHK-62: delete_group removes group from all member profiles
# ---------------------------------------------------------------------------

def test_delete_group_removes_from_all_profiles(tmp_path):
    storage, groups = _make_lib(tmp_path)

    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")

    groups.add_to_group(f1, "Team Alpha")
    groups.add_to_group(f2, "Team Alpha")

    groups.delete_group("Team Alpha")

    m1 = storage.read_meta(f1)
    m2 = storage.read_meta(f2)
    assert "Team Alpha" not in m1.groups
    assert "Team Alpha" not in m2.groups


def test_delete_group_leaves_other_groups(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    groups.add_to_group(f1, "Team Alpha")
    groups.add_to_group(f1, "Team Beta")

    groups.delete_group("Team Alpha")

    m = storage.read_meta(f1)
    assert "Team Beta" in m.groups
    assert "Team Alpha" not in m.groups


# ---------------------------------------------------------------------------
# Group basics
# ---------------------------------------------------------------------------

def test_add_to_group(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    groups.add_to_group(f1, "Research")
    m = storage.read_meta(f1)
    assert "Research" in m.groups


def test_remove_from_group(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    groups.add_to_group(f1, "Research")
    groups.remove_from_group(f1, "Research")
    m = storage.read_meta(f1)
    assert "Research" not in m.groups


def test_list_groups(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")
    groups.add_to_group(f1, "Alpha")
    groups.add_to_group(f2, "Beta")
    all_groups = groups.list_groups()
    assert "Alpha" in all_groups
    assert "Beta" in all_groups


def test_members(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    f2, _ = storage.create_profile("Bob", "B", "", "")
    groups.add_to_group(f1, "Crew")
    groups.add_to_group(f2, "Crew")
    members = groups.members("Crew")
    assert f1 in members
    assert f2 in members


def test_rename_group(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    groups.add_to_group(f1, "OldName")
    groups.rename_group("OldName", "NewName")
    m = storage.read_meta(f1)
    assert "NewName" in m.groups
    assert "OldName" not in m.groups


def test_add_to_group_no_duplicate(tmp_path):
    storage, groups = _make_lib(tmp_path)
    f1, _ = storage.create_profile("Alice", "A", "", "")
    groups.add_to_group(f1, "Team")
    groups.add_to_group(f1, "Team")
    m = storage.read_meta(f1)
    assert m.groups.count("Team") == 1
