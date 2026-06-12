"""XDG autostart for Linux — writes a .desktop file to ~/.config/autostart/."""
from __future__ import annotations

import os
from pathlib import Path

from platforms.base.auto_start import AutoStartBase

_APP_NAME = "SpeechRecognitionProgram"
_DESKTOP_FILENAME = f"{_APP_NAME}.desktop"


def _autostart_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
    base = xdg_config if xdg_config else os.path.join(os.path.expanduser("~"), ".config")
    return Path(base) / "autostart"


class AutoStart(AutoStartBase):

    def enable(self, app_path: str) -> None:
        dest = _autostart_dir()
        dest.mkdir(parents=True, exist_ok=True)
        desktop = dest / _DESKTOP_FILENAME
        desktop.write_text(
            f"[Desktop Entry]\n"
            f"Type=Application\n"
            f"Name=Speech Recognition Program\n"
            f"Exec={app_path}\n"
            f"Hidden=false\n"
            f"NoDisplay=false\n"
            f"X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )

    def disable(self) -> None:
        desktop = _autostart_dir() / _DESKTOP_FILENAME
        try:
            desktop.unlink()
        except FileNotFoundError:
            pass

    def is_enabled(self) -> bool:
        return (_autostart_dir() / _DESKTOP_FILENAME).exists()
