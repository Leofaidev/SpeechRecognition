"""Persistent JSON configuration store with in-memory override for tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "source_language": "auto",
    "target_language": "en",
    "whisper_model": "medium",
    "bad_audio_threshold": 0.6,
    "min_profile_samples": 3,
    "translation_enabled": False,
    "translation_engine": "local",
    "auto_start": False,
    "licence_accepted": False,
    "output_folder": "",
    "output_formats": ["txt"],
    "output_fields": {
        "timestamp": True,
        "speaker": True,
        "language": True,
        "confidence": True,
        "text": True,
        "original_text": True,
    },
    "completion_sound": "chime",
    "gpu_enabled": True,
    "transcript_font_size": 12,
    "recording_mode": "regular",
    "ui_language": "en",
    "hotkeys": {
        "start_stop": "ctrl+shift+r",
        "stop_recording": "ctrl+shift+s",
        "copy_to_clipboard": "ctrl+shift+c",
        "toggle_mode": "F10",
    },
}


class ConfigStore:
    """Load/save settings from a JSON file.

    Pass *overrides* to inject values without touching the file — used in tests.
    """

    def __init__(
        self,
        config_path: Path | str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> None:
        self._data: dict[str, Any] = dict(_DEFAULTS)
        if config_path is not None:
            self._path = Path(config_path)
            self._load()
        else:
            self._path = None
        if overrides:
            self._data.update(overrides)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        if self._path is not None:
            self._save()

    def update(self, mapping: dict[str, Any]) -> None:
        self._data.update(mapping)
        if self._path is not None:
            self._save()

    def as_dict(self) -> dict[str, Any]:
        return dict(self._data)

    # ------------------------------------------------------------------
    # persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._path and self._path.exists():
            try:
                with self._path.open(encoding="utf-8") as fh:
                    stored = json.load(fh)
                self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass  # silently fall back to defaults on corrupt file

    def _save(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)
