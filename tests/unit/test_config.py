"""Unit tests for config.store and config.hotkeys — CHK-76, 77, 78, 79."""

import json
import pytest
from pathlib import Path

from config.store import ConfigStore
from config.hotkeys import check_hotkey, check_all_hotkeys, ConflictWarning


# ---------------------------------------------------------------------------
# CHK-76: Config defaults on first run; reload returns same values
# ---------------------------------------------------------------------------

def test_config_creates_with_defaults(tmp_path):
    config = ConfigStore()
    assert config.get("source_language") == "auto"
    assert config.get("whisper_model") == "medium"
    assert config.get("translation_enabled") is False


def test_config_reload_identical(tmp_path):
    path = tmp_path / "config.json"
    c1 = ConfigStore(path)
    c1.set("whisper_model", "large")

    c2 = ConfigStore(path)
    assert c2.get("whisper_model") == "large"


def test_config_default_on_missing_key():
    config = ConfigStore()
    assert config.get("nonexistent_key", "fallback") == "fallback"


def test_config_set_persists(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path)
    c.set("gpu_enabled", False)
    c2 = ConfigStore(path)
    assert c2.get("gpu_enabled") is False


def test_config_update_multiple_keys(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path)
    c.update({"source_language": "fi", "target_language": "en"})
    c2 = ConfigStore(path)
    assert c2.get("source_language") == "fi"
    assert c2.get("target_language") == "en"


def test_config_overrides_dont_persist(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path, overrides={"whisper_model": "tiny"})
    assert c.get("whisper_model") == "tiny"
    # Override should not appear in the stored file (no set() was called)
    c2 = ConfigStore(path)
    assert c2.get("whisper_model") == "medium"  # default


# ---------------------------------------------------------------------------
# CHK-77: Hotkey conflict detection
# ---------------------------------------------------------------------------

def test_ctrl_c_triggers_conflict():
    warning = check_hotkey("ctrl+c")
    assert warning is not None
    assert isinstance(warning, ConflictWarning)


def test_ctrl_shift_r_no_conflict():
    warning = check_hotkey("ctrl+shift+r")
    assert warning is None


def test_intra_app_conflict_detected():
    existing = {"stop_recording": "ctrl+shift+s"}
    warning = check_hotkey("ctrl+shift+s", existing_bindings=existing)
    assert warning is not None
    assert "stop_recording" in warning.reason


def test_no_conflict_for_unique_key():
    existing = {"action_a": "F9"}
    warning = check_hotkey("F10", existing_bindings=existing)
    assert warning is None


def test_check_all_hotkeys_finds_reserved():
    bindings = {"copy": "ctrl+c", "start": "ctrl+shift+r"}
    warnings = check_all_hotkeys(bindings)
    assert any("ctrl+c" in w.key for w in warnings)


def test_check_all_hotkeys_finds_duplicate():
    bindings = {"action_a": "ctrl+shift+r", "action_b": "ctrl+shift+r"}
    warnings = check_all_hotkeys(bindings)
    assert len(warnings) >= 1


def test_check_all_hotkeys_clean_config():
    bindings = {
        "start_stop": "ctrl+shift+r",
        "stop_recording": "ctrl+shift+s",
        "copy_to_clipboard": "ctrl+shift+c",
    }
    warnings = check_all_hotkeys(bindings)
    # ctrl+shift+c is not in Windows reserved (ctrl+c is, but not ctrl+shift+c)
    assert len(warnings) == 0


# ---------------------------------------------------------------------------
# CHK-78: Recording mode saved and restored
# ---------------------------------------------------------------------------

def test_recording_mode_default_is_regular():
    config = ConfigStore()
    assert config.get("recording_mode") == "regular"


def test_recording_mode_persists(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path)
    c.set("recording_mode", "short")

    c2 = ConfigStore(path)
    assert c2.get("recording_mode") == "short"


def test_recording_mode_restore_on_reload(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path)
    c.set("recording_mode", "short")
    del c

    c2 = ConfigStore(path)
    assert c2.get("recording_mode") == "short"


# ---------------------------------------------------------------------------
# CHK-79: UI language defaults to "en"
# ---------------------------------------------------------------------------

def test_ui_language_default_is_en():
    config = ConfigStore()
    assert config.get("ui_language") == "en"


def test_ui_language_persists(tmp_path):
    path = tmp_path / "config.json"
    c = ConfigStore(path)
    c.set("ui_language", "fi")

    c2 = ConfigStore(path)
    assert c2.get("ui_language") == "fi"
