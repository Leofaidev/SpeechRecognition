"""Unit tests for gui.lang — T-77 language loading."""

import json
import shutil
import pytest
from pathlib import Path

from gui.lang import LangManager, LangLoadError


@pytest.fixture
def lang_dir(tmp_path):
    """Create a minimal language directory with en.json."""
    en = {
        "app_title": "Test App",
        "btn_start": "Start",
        "progress_queue": "Queue: {current} of {total}",
        "lang_code": "en",
        "lang_name": "English",
    }
    (tmp_path / "en.json").write_text(json.dumps(en), encoding="utf-8")
    return tmp_path


@pytest.fixture
def lang_dir_with_fi(lang_dir):
    fi = {
        "app_title": "Testiohjelma",
        "btn_start": "Käynnistä",
        "progress_queue": "Jono: {current}/{total}",
        "lang_code": "fi",
        "lang_name": "Suomi",
    }
    (lang_dir / "fi.json").write_text(json.dumps(fi), encoding="utf-8")
    return lang_dir


# ---------------------------------------------------------------------------
# Basic loading
# ---------------------------------------------------------------------------

def test_load_english(lang_dir):
    lm = LangManager("en", lang_dir=lang_dir)
    assert lm.t("app_title") == "Test App"
    assert lm.t("btn_start") == "Start"


def test_load_finnish(lang_dir_with_fi):
    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    assert lm.t("btn_start") == "Käynnistä"


def test_code_property(lang_dir_with_fi):
    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    assert lm.code == "fi"


def test_available_lists_json_files(lang_dir_with_fi):
    lm = LangManager("en", lang_dir=lang_dir_with_fi)
    available = lm.available
    assert "en" in available
    assert "fi" in available


# ---------------------------------------------------------------------------
# Fallback to English
# ---------------------------------------------------------------------------

def test_missing_key_falls_back_to_english(lang_dir_with_fi):
    """Finnish file doesn't have 'app_title' duplicated from English."""
    fi_data = {"btn_start": "Käynnistä", "lang_code": "fi", "lang_name": "Suomi"}
    (lang_dir_with_fi / "fi.json").write_text(
        json.dumps(fi_data), encoding="utf-8")
    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    # 'app_title' only in English file — should fall back
    assert lm.t("app_title") == "Test App"


def test_unknown_key_returns_key_name(lang_dir):
    lm = LangManager("en", lang_dir=lang_dir)
    assert lm.t("nonexistent_key_xyz") == "nonexistent_key_xyz"


# ---------------------------------------------------------------------------
# Format kwargs
# ---------------------------------------------------------------------------

def test_format_kwargs(lang_dir):
    lm = LangManager("en", lang_dir=lang_dir)
    result = lm.t("progress_queue", current=3, total=10)
    assert "3" in result
    assert "10" in result


def test_format_kwargs_missing_gracefully(lang_dir):
    lm = LangManager("en", lang_dir=lang_dir)
    # Should not raise even if kwargs don't match the template
    result = lm.t("progress_queue", wrong_key=5)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Backup restore (T-77 — corrupt file restores from backup)
# ---------------------------------------------------------------------------

def test_corrupt_file_restored_from_backup(lang_dir_with_fi, tmp_path):
    # Write a good Finnish file to backup
    backup_dir = lang_dir_with_fi / "backup"
    backup_dir.mkdir()
    fi_backup = {
        "app_title": "Testiohjelma backup",
        "btn_start": "Käynnistä",
        "lang_code": "fi",
        "lang_name": "Suomi",
    }
    (backup_dir / "fi.json").write_text(
        json.dumps(fi_backup), encoding="utf-8")

    # Corrupt the main Finnish file
    (lang_dir_with_fi / "fi.json").write_text(
        "{ invalid json !!!", encoding="utf-8")

    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    assert lm.t("btn_start") == "Käynnistä"


def test_missing_file_restored_from_backup(lang_dir_with_fi):
    backup_dir = lang_dir_with_fi / "backup"
    backup_dir.mkdir()
    fi_backup = {
        "btn_start": "Käynnistä",
        "lang_code": "fi",
        "lang_name": "Suomi",
    }
    (backup_dir / "fi.json").write_text(
        json.dumps(fi_backup), encoding="utf-8")

    # Delete the main file
    (lang_dir_with_fi / "fi.json").unlink()

    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    assert lm.t("btn_start") == "Käynnistä"


def test_missing_file_no_backup_raises(lang_dir):
    # Finnish file doesn't exist and there's no backup
    with pytest.raises(LangLoadError):
        LangManager("fi", lang_dir=lang_dir)


# ---------------------------------------------------------------------------
# Live language switch
# ---------------------------------------------------------------------------

def test_load_switches_language(lang_dir_with_fi):
    lm = LangManager("en", lang_dir=lang_dir_with_fi)
    assert lm.t("btn_start") == "Start"
    lm.load("fi")
    assert lm.t("btn_start") == "Käynnistä"
    assert lm.code == "fi"


def test_reload_english_after_switch(lang_dir_with_fi):
    lm = LangManager("fi", lang_dir=lang_dir_with_fi)
    lm.load("en")
    assert lm.t("btn_start") == "Start"
    assert lm.code == "en"
