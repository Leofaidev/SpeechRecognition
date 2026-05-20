"""Completion sound player (T-88).

Plays a short audio file when processing finishes.  Suppressed when
``sound_enabled`` is False in config, and always suppressed in CLI mode.

Uses ``winsound`` on Windows (no extra dependency).  Falls back silently
if the sound file is missing or playback fails.
"""

from __future__ import annotations

import threading
from pathlib import Path


_DEFAULT_SOUND_NAME = "complete_default.wav"


def _resolve_assets_dir() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "assets" / "sounds"
        if candidate.is_dir():
            return candidate
    return Path("assets") / "sounds"


class SoundPlayer:
    """Plays the configured completion sound in a daemon thread.

    Parameters
    ----------
    sound_file:
        Absolute path to a WAV file, or ``None`` to use the built-in default.
    enabled:
        If False, calls to :meth:`play` are no-ops.
    """

    def __init__(self, sound_file: str | Path | None = None,
                 enabled: bool = True) -> None:
        self._enabled = enabled
        self._path: Path | None = None
        self._set_sound(sound_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play(self) -> None:
        """Play the sound asynchronously.  Never raises."""
        if not self._enabled or self._path is None:
            return
        path = self._path
        t = threading.Thread(target=self._play_sync, args=(path,), daemon=True)
        t.start()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_sound_file(self, path: str | Path | None) -> None:
        self._set_sound(path)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def sound_path(self) -> Path | None:
        return self._path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_sound(self, path: str | Path | None) -> None:
        if path is None:
            default = _resolve_assets_dir() / _DEFAULT_SOUND_NAME
            self._path = default if default.exists() else None
        else:
            p = Path(path)
            self._path = p if p.exists() else None

    @staticmethod
    def _play_sync(path: Path) -> None:
        try:
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass
