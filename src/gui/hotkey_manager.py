"""Global hotkey manager (T-86).

Registers system-wide hotkeys using the ``keyboard`` library on Windows,
raw /dev/input/ reads on Linux, and ``pynput`` on macOS.  Hotkeys work even
when the application window is not in focus.  All hotkeys are automatically
unregistered on :meth:`shutdown`.

Hotkeys are completely disabled in CLI mode (do not instantiate this class
from ``cli.parser``).
"""

from __future__ import annotations

import glob
import os
import select
import struct
import sys
import threading
from typing import Callable


def _hklog(msg: str) -> None:
    try:
        with open("/tmp/hotkeys.log", "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


# ── pynput helper (macOS / fallback) ─────────────────────────────────────────

def _keyboard_to_pynput(combo: str) -> str:
    """Convert 'ctrl+shift+r' -> '<ctrl>+<shift>+r' for pynput GlobalHotKeys."""
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


# ── Linux /dev/input evdev tables ────────────────────────────────────────────

_EV_KEY = 1
_EVENT_FMT = "QQHHi"           # timeval(2×u64) + type(u16) + code(u16) + value(s32)
_EVENT_SIZE = struct.calcsize(_EVENT_FMT)  # 24 bytes on 64-bit Linux

_LINUX_KEY_NAMES: dict[str, int] = {
    # F1-F10: codes 59-68
    **{f"f{n}": 58 + n for n in range(1, 11)},
    "f11": 87, "f12": 88,
    # Letters (US QWERTY)
    "q": 16, "w": 17, "e": 18, "r": 19, "t": 20,
    "y": 21, "u": 22, "i": 23, "o": 24, "p": 25,
    "a": 30, "s": 31, "d": 32, "f": 33, "g": 34,
    "h": 35, "j": 36, "k": 37, "l": 38,
    "z": 44, "x": 45, "c": 46, "v": 47,
    "b": 48, "n": 49, "m": 50,
    # Digits
    "1": 2, "2": 3, "3": 4, "4": 5, "5": 6,
    "6": 7, "7": 8, "8": 9, "9": 10, "0": 11,
}

_LINUX_MODS: dict[str, frozenset[int]] = {
    "ctrl":  frozenset({29, 97}),    # KEY_LEFTCTRL, KEY_RIGHTCTRL
    "shift": frozenset({42, 54}),    # KEY_LEFTSHIFT, KEY_RIGHTSHIFT
    "alt":   frozenset({56, 100}),   # KEY_LEFTALT, KEY_RIGHTALT
}

# Reverse map: keycode -> modifier name (for quick modifier state updates)
_CODE_TO_MOD: dict[int, str] = {}
for _mod, _codes in _LINUX_MODS.items():
    for _c in _codes:
        _CODE_TO_MOD[_c] = _mod


def _parse_linux_combo(combo: str) -> tuple[frozenset[str], int] | None:
    """Parse 'ctrl+shift+f12' → (frozenset({'ctrl','shift'}), 88). Returns None on error."""
    parts = [p.strip().lower() for p in combo.split("+")]
    mods: set[str] = set()
    main_code: int | None = None
    for p in parts:
        if p in _LINUX_MODS:
            mods.add(p)
        elif p in _LINUX_KEY_NAMES:
            main_code = _LINUX_KEY_NAMES[p]
        else:
            return None
    if main_code is None:
        return None
    return frozenset(mods), main_code


class _EvdevListener:
    """Background daemon thread reading kernel input events for global hotkeys.

    Works regardless of which application has focus (X11, Wayland, or neither).
    Requires the process user to be in the 'input' group (or root).
    """

    def __init__(self) -> None:
        self._combos: list[tuple[frozenset[str], int, Callable]] = []
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def set_combos(self, combos: list[tuple[frozenset[str], int, Callable]]) -> None:
        """Replace active combos and restart the reader thread."""
        self._combos = combos
        self._restart()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

    def _restart(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._stop_event.clear()
        if not self._combos:
            return
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="wsp-evdev")
        self._thread.start()

    @staticmethod
    def _find_keyboards() -> list[str]:
        devices: list[str] = []
        for path in sorted(glob.glob("/sys/class/input/event*/device/name")):
            try:
                name = open(path).read().strip().lower()
                if "keyboard" in name:
                    node = path.split("/")[-3]   # e.g. "event1"
                    dev = f"/dev/input/{node}"
                    if os.access(dev, os.R_OK):
                        devices.append(dev)
            except Exception:
                pass
        return devices

    def _run(self) -> None:
        devices = self._find_keyboards()
        if not devices:
            _hklog("evdev: no accessible keyboard devices found")
            return
        _hklog(f"evdev: listening on {devices}")

        fds: list = []
        for dev in devices:
            try:
                fds.append(open(dev, "rb", buffering=0))
            except Exception as exc:
                _hklog(f"evdev: open {dev} failed: {exc}")
        if not fds:
            return

        mod_state: dict[str, bool] = {m: False for m in _LINUX_MODS}
        combos = list(self._combos)   # snapshot

        try:
            while not self._stop_event.is_set():
                ready, _, _ = select.select(fds, [], [], 0.05)
                for f in ready:
                    data = f.read(_EVENT_SIZE)
                    if len(data) < _EVENT_SIZE:
                        continue
                    _, _, etype, code, value = struct.unpack(_EVENT_FMT, data)
                    if etype != _EV_KEY:
                        continue
                    # Track modifier state
                    mod_name = _CODE_TO_MOD.get(code)
                    if mod_name is not None:
                        mod_state[mod_name] = (value == 1)
                    # On key press only
                    if value == 1:
                        active_mods = frozenset(
                            m for m, v in mod_state.items() if v)
                        for req_mods, req_code, cb in combos:
                            if code == req_code and active_mods == req_mods:
                                try:
                                    cb()
                                except Exception:
                                    pass
        finally:
            for f in fds:
                try:
                    f.close()
                except Exception:
                    pass


# ── Default bindings ──────────────────────────────────────────────────────────

_DEFAULT_BINDINGS: dict[str, str] = {
    "start_recording": "ctrl+shift+r",
    "stop_recording": "ctrl+shift+s",
}


# ── Manager ───────────────────────────────────────────────────────────────────

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

        # Linux: evdev listener + stored combos (key_str -> (mods, code, cb))
        self._evdev_listener: _EvdevListener | None = None
        self._evdev_entries: dict[str, tuple[frozenset[str], int, Callable]] = {}

        # macOS / other: pynput GlobalHotKeys listener + active map
        self._pynput_listener: object | None = None
        self._pynput_map: dict[str, Callable[[], None]] = {}

        self._keyboard_available = self._check_keyboard()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, action: str, callback: Callable[[], None]) -> None:
        """Bind *callback* to the key combo for *action*."""
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
        """Replace bindings, re-registering all callbacks."""
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
        elif sys.platform == "linux":
            # evdev approach: check that at least one keyboard device is readable
            for path in glob.glob("/sys/class/input/event*/device/name"):
                try:
                    name = open(path).read().strip().lower()
                    if "keyboard" in name:
                        node = path.split("/")[-3]
                        if os.access(f"/dev/input/{node}", os.R_OK):
                            return True
                except Exception:
                    pass
            _hklog("evdev: no readable keyboard device — hotkeys disabled")
            return False
        else:
            try:
                from pynput.keyboard import GlobalHotKeys  # noqa: F401
                return True
            except ImportError:
                return False

    def _clear_all_keyboard_hooks(self) -> None:
        if sys.platform == "win32":
            if self._keyboard_available:
                try:
                    import keyboard
                    keyboard.unhook_all_hotkeys()
                except Exception:
                    pass
            self._handlers.clear()
        elif sys.platform == "linux":
            if self._evdev_listener is not None:
                self._evdev_listener.stop()
                self._evdev_listener = None
            self._evdev_entries.clear()
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
        elif sys.platform == "linux":
            parsed = _parse_linux_combo(key)
            if parsed is None:
                _hklog(f"evdev: unrecognised combo {key!r} — skipped")
                return
            mods, code = parsed
            self._evdev_entries[key] = (mods, code, callback)
            self._registered.add(key)
            self._push_evdev_combos()
            _hklog(f"evdev: registered {key!r} mods={set(mods)} code={code}")
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
        elif sys.platform == "linux":
            self._evdev_entries.pop(key, None)
            self._push_evdev_combos()
        else:
            pkey = _keyboard_to_pynput(key)
            self._pynput_map.pop(pkey, None)
            self._restart_pynput_listener()
        self._registered.discard(key)

    def _push_evdev_combos(self) -> None:
        """Sync the evdev listener with current _evdev_entries."""
        combos = [(m, c, cb) for m, c, cb in self._evdev_entries.values()]
        if self._evdev_listener is None:
            self._evdev_listener = _EvdevListener()
        self._evdev_listener.set_combos(combos)

    def _stop_pynput_listener(self) -> None:
        if self._pynput_listener is not None:
            try:
                self._pynput_listener.stop()  # type: ignore[union-attr]
            except Exception:
                pass
            self._pynput_listener = None

    def _restart_pynput_listener(self) -> None:
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
