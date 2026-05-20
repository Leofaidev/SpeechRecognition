"""Global hotkey manager (T-86).

Registers system-wide hotkeys using the ``keyboard`` library.  Hotkeys work
even when the application window is not in focus.  All hotkeys are
automatically unregistered on :meth:`shutdown`.

Hotkeys are completely disabled in CLI mode (do not instantiate this class
from ``cli.parser``).
"""

from __future__ import annotations

import threading
from typing import Callable


_DEFAULT_BINDINGS: dict[str, str] = {
    "start_recording": "ctrl+shift+r",
    "stop_recording": "ctrl+shift+s",
    "copy_to_clipboard": "ctrl+shift+c",
}


class HotkeyManager:
    """Manages global hotkey registrations.

    Parameters
    ----------
    bindings:
        Mapping of ``action_name → key_combo``.  Defaults to the application
        defaults if omitted.
    """

    def __init__(self, bindings: dict[str, str] | None = None) -> None:
        self._bindings: dict[str, str] = dict(
            bindings if bindings is not None else _DEFAULT_BINDINGS
        )
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._registered: set[str] = set()
        self._lock = threading.Lock()
        self._keyboard_available = self._check_keyboard()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, action: str, callback: Callable[[], None]) -> None:
        """Bind *callback* to the key combo for *action*.

        Does nothing if *action* has no binding or the keyboard library is
        unavailable.
        """
        with self._lock:
            self._callbacks[action] = callback
            key = self._bindings.get(action)
            if key and self._keyboard_available:
                self._register_key(key, callback)

    def unregister(self, action: str) -> None:
        """Remove the hotkey for *action*."""
        with self._lock:
            key = self._bindings.get(action)
            if key and self._keyboard_available:
                self._unregister_key(key)
            self._callbacks.pop(action, None)

    def update_bindings(self, new_bindings: dict[str, str]) -> None:
        """Replace bindings with *new_bindings*, re-registering all callbacks."""
        with self._lock:
            for action, key in self._bindings.items():
                if self._keyboard_available:
                    self._unregister_key(key)
            self._bindings = dict(new_bindings)
            for action, cb in self._callbacks.items():
                key = self._bindings.get(action)
                if key and self._keyboard_available:
                    self._register_key(key, cb)

    def shutdown(self) -> None:
        """Unregister all hotkeys."""
        with self._lock:
            if self._keyboard_available:
                try:
                    import keyboard
                    keyboard.unhook_all_hotkeys()
                except Exception:
                    pass
            self._registered.clear()
            self._callbacks.clear()

    @property
    def bindings(self) -> dict[str, str]:
        return dict(self._bindings)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _check_keyboard() -> bool:
        try:
            import keyboard  # noqa: F401
            return True
        except ImportError:
            return False

    def _register_key(self, key: str, callback: Callable[[], None]) -> None:
        try:
            import keyboard
            keyboard.add_hotkey(key, callback, suppress=False)
            self._registered.add(key)
        except Exception:
            pass

    def _unregister_key(self, key: str) -> None:
        try:
            import keyboard
            keyboard.remove_hotkey(key)
            self._registered.discard(key)
        except Exception:
            pass
