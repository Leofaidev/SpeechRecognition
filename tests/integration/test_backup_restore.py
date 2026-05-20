"""CHK-145 — Backup and restore round-trip.

Creates a full backup, modifies settings/dictionary/profiles, restores the
backup, and verifies all three changes are reverted.  No ML models required.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backup.manager import AppPaths, create_backup
from backup.restorer import restore


def _make_paths(base: Path) -> AppPaths:
    library = base / "library"
    sessions = base / "sessions"
    library.mkdir(parents=True, exist_ok=True)
    sessions.mkdir(parents=True, exist_ok=True)
    return AppPaths(
        config_file=base / "config.json",
        dictionary_file=base / "dictionary.json",
        library_root=library,
        sessions_dir=sessions,
        install_dir=base,
    )


@pytest.mark.integration
def test_backup_restore_round_trip(tmp_path):
    """Full backup → modify state → restore → verify state reverted."""
    paths = _make_paths(tmp_path)

    # --- initial state ---
    config_data = {"whisper_model": "medium", "gpu_enabled": True}
    dict_data = {"entries": []}
    paths.config_file.write_text(json.dumps(config_data), encoding="utf-8")
    paths.dictionary_file.write_text(json.dumps(dict_data), encoding="utf-8")

    profile_dir = paths.library_root / "Alice"
    profile_dir.mkdir()
    (profile_dir / "speaker.json").write_text(
        json.dumps({"first": "Alice", "last": ""}), encoding="utf-8"
    )

    # --- create backup ---
    backup_zip = tmp_path / "backup.zip"
    result = create_backup(paths, backup_zip)
    assert backup_zip.exists(), "Backup ZIP was not created"
    assert result.files_backed_up >= 3  # config + dict + speaker.json

    # --- modify state ---
    config_data["whisper_model"] = "large-v3"
    paths.config_file.write_text(json.dumps(config_data), encoding="utf-8")

    dict_data["entries"].append({"source": "foo", "target": "bar"})
    paths.dictionary_file.write_text(json.dumps(dict_data), encoding="utf-8")

    new_profile = paths.library_root / "Bob"
    new_profile.mkdir()
    (new_profile / "speaker.json").write_text(
        json.dumps({"first": "Bob", "last": ""}), encoding="utf-8"
    )

    # --- restore ---
    safety_dir = tmp_path / "safety"
    restore_result = restore(paths, backup_zip, safety_dir)
    assert restore_result.success, f"Restore failed: {restore_result.error}"
    assert restore_result.safety_backup_path.exists(), "Safety backup not created"

    # --- verify reverted ---
    restored_config = json.loads(paths.config_file.read_text(encoding="utf-8"))
    assert restored_config["whisper_model"] == "medium", (
        "Config was not reverted: whisper_model should be 'medium'"
    )

    restored_dict = json.loads(paths.dictionary_file.read_text(encoding="utf-8"))
    assert restored_dict["entries"] == [], "Dictionary was not reverted to empty"

    # Alice profile restored; Bob profile (added after backup) not present
    assert (paths.library_root / "Alice" / "speaker.json").exists(), (
        "Alice profile missing after restore"
    )
    assert not (paths.library_root / "Bob").exists(), (
        "Bob profile should have been removed by restore"
    )


@pytest.mark.integration
def test_backup_path_warning_inside_install_dir(tmp_path):
    """Backup ZIP inside the installation directory triggers path_warning."""
    paths = _make_paths(tmp_path)
    paths.config_file.write_text("{}", encoding="utf-8")
    paths.dictionary_file.write_text('{"entries": []}', encoding="utf-8")

    backup_zip = tmp_path / "nested" / "backup.zip"
    result = create_backup(paths, backup_zip)
    # install_dir == tmp_path; backup is under tmp_path → warning expected
    assert result.path_warning is True
