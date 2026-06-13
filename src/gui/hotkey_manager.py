"""Global hotkey manager (T-86).

Registers system-wide hotkeys using the ``keyboard`` library on Windows and
``pynput`` on Linux/macOS.  Hotkeys work even when the application window is
not in focus.  All hotkeys are automatically unregistered on :meth:`shutdown`.

Hotkeys are completely disabled in CLI mode (do not instantiate this class
from ``cli.parser``).
"""

from __future__ import annotations

import sys
import threading
from typing import Callable


def _hklog(msg: str) -> None:
    try:
        with open("/tmp/hotkeys.log", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _keyboard_to_pynput(combo: str) -> str:
    """Convert keyboard-library combo format to pynput GlobalHotKeys format.

    Example: 'ctrl+shift+r' -> '<ctrl>+<shift>+r'
             'f11'          -> '<f11>'
    """
    _WRAP = {
        "ctrl", "shift", "alt", "altgr", "meta", "super", "cmd",
        "backspace", "delete", "end", "esc", "escape", "home",
        "insert", "page_down", "page_up", "pause", "print_screen",
        "space", "tab", "up", "down", "left", "right",
        "caps_lock", "num_lock", "scroll_lock", "windows",
    }
    parts = combo.lower().split("+")
    converted = []
    for part in parts:
        if part in _WRAP or (part.startswith("f") and part[1:].isdigit()):
            converted.append(f"<{part}>")
        else:
            converted.append(part)
    return "+".join(converted)


_DEFAULT_BINDINGS: dict[str, str] = {
    "start_recording": "ctrl+shift+r",
    "stop_recording": "ctrl+shift+s",
}


class HotkeyManager:
    """Manages global hotkey registrations.

    Parameters
    ----------
    bindings:
        Mapping of ``action_name -> key_combo``.  Defaults to the application
        defaults if omitted.
    """

    def __init__(self, bindings: dict[str, str] | None = None) -> None:
        self._bindings: dict[str, str] = dict(
            bindings if bindings is not None else _DEFAULT_BINDINGS
        )
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._registered: set[str] = set()
        self._suspended: bool = False
        self._lock = threading.Lock()

        # Windows: keyboard library handlers keyed by key string
        self._handlers: dict[str, list] = {}

        # Linux/macOS: pynput GlobalHotKeys listener + active map
        self._pynput_listener: object | None = None
        self._pynput_map: dict[str, Callable[[], None]] = {}

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
            if self._suspended:
                return
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
        """Replace bindings with *new_bindings*, re-registering all callbacks.

        When the manager is suspended (hotkeys panel open), only the binding
        table is updated; actual re-registration is deferred to resume_callbacks.
        """
        with self._lock:
            if not self._suspended:
                for key in list(self._registered):
                    self._unregister_key(key)
            self._bindings = dict(new_bindings)
            if not self._suspended:
                for action, cb in self._callbacks.items():
                    key = self._bindings.get(action)
                    if key and self._keyboard_available:
                        self._register_key(key, cb)

    def suspend_callbacks(self) -> None:
        """Unregister all hotkeys (called when hotkeys panel opens)."""
        with self._lock:
            self._suspended = True
            self._clear_all_keyboard_hooks()

    def resume_callbacks(self) -> None:
        """Re-register all hotkeys (called when hotkeys panel closes)."""
        with self._lock:
            self._suspended = False
            self._clear_all_keyboard_hooks()
            for action, cb in self._callbacks.items():
                key = self._bindings.get(action)
                if key and self._keyboard_available:
                    self._register_key(key, cb)

    def shutdown(self) -> None:
        """Unregister all hotkeys."""
        with self._lock:
            self._clear_all_keyboard_hooks()
            self._callbacks.clear()

    @property
    def bindings(self) -> dict[str, str]:
        return dict(self._bindings)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _check_keyboard() -> bool:
        if sys.platform == "win32":
            try:
                import keyboard  # noqa: F401
                return True
            except ImportError:
                return False
        else:
            try:
                from pynput.keyboard import GlobalHotKeys  # noqa: F401
                return True
            except ImportError:
                return False

    def _clear_all_keyboard_hooks(self) -> None:
        """Remove every hotkey from the active backend."""
        if sys.platform == "win32":
            if self._keyboard_available:
                try:
                    import keyboard
                    keyboard.unhook_all_hotkeys()
                except Exception:
                    pass
            self._handlers.clear()
        else:
            self._stop_pynput_listener()
            self._pynput_map.clear()
        self._registered.clear()

    def _register_key(self, key: str, callback: Callable[[], None]) -> None:
        if sys.platform == "win32":
            try:
                import keyboard
                handler = keyboard.add_hotkey(key, callback, suppress=False)
                self._handlers.setdefault(key, []).append(handler)
                self._registered.add(key)
                _hklog(f"OK: {key}")
            except Exception as exc:
                _hklog(f"FAIL: {key} -> {exc}")
        else:
            pkey = _keyboard_to_pynput(key)
            self._pynput_map[pkey] = callback
            self._registered.add(key)
            self._restart_pynput_listener()
            _hklog(f"pynput registered: {key} -> {pkey}")

    def _unregister_key(self, key: str) -> None:
        if sys.platform == "win32":
            try:
                import keyboard
                for h in self._handlers.pop(key, []):
                    try:
                        keyboard.remove_hotkey(h)
                    except Exception:
                        pass
            except Exception:
                pass
        else:
            pkey = _keyboard_to_pynput(key)
            self._pynput_map.pop(pkey, None)
            self._restart_pynput_listener()
        self._registered.discard(key)

    def _stop_pynput_listener(self) -> None:
        if self._pynput_listener is not None:
            try:
                self._pynput_listener.stop()  # type: ignore[union-attr]
            except Exception:
                pass
            self._pynput_listener = None

    def _restart_pynput_listener(self) -> None:
        """Stop the existing pynput listener and start a fresh one."""
        self._stop_pynput_listener()
        if not self._pynput_map:
            return
        try:
            from pynput.keyboard import GlobalHotKeys
            self._pynput_listener = GlobalHotKeys(dict(self._pynput_map))
            self._pynput_listener.start()  # type: ignore[union-attr]
            _hklog(f"pynput listener started with: {list(self._pynput_map.keys())}")
        except Exception as exc:
            _hklog(f"pynput listener FAIL: {exc}")
