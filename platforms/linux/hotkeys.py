"""Linux global hotkeys via the `keyboard` library.

Requires root or membership in the `input` group:
    sudo usermod -aG input $USER   (then log out / back in)
"""
from __future__ import annotations

from typing import Callable

from platforms.base.hotkeys import HotkeysBase

# Common Linux/desktop shortcuts to warn about
_SYSTEM_SHORTCUTS = {
    "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z", "ctrl+y",
    "ctrl+a", "ctrl+s", "ctrl+q", "ctrl+w",
    "super+d", "super+l",
}


class Hotkeys(HotkeysBase):

    def __init__(self) -> None:
        self._registered: dict[str, object] = {}

    def register(self, combination: str, callback: Callable[[], None]) -> None:
        try:
            import keyboard
            handler = keyboard.add_hotkey(combination, callback, suppress=False)
            self._registered[combination] = handler
        except Exception:
            pass

    def unregister(self, combination: str) -> None:
        try:
            import keyboard
            handler = self._registered.pop(combination, None)
            if handler is not None:
                keyboard.remove_hotkey(handler)
        except Exception:
            pass

    def unregister_all(self) -> None:
        try:
            import keyboard
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        self._registered.clear()

    def is_conflict(self, combination: str) -> bool:
        return combination.lower() in _SYSTEM_SHORTCUTS
