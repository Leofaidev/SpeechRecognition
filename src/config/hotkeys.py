"""Hotkey conflict detection (T-60).

Checks whether a proposed keybinding conflicts with common Windows shortcuts
or other registered application hotkeys.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

# Common Windows system shortcuts that should not be overridden
_WINDOWS_RESERVED: set[str] = {
    "ctrl+c",
    "ctrl+v",
    "ctrl+x",
    "ctrl+z",
    "ctrl+y",
    "ctrl+a",
    "ctrl+s",
    "ctrl+p",
    "ctrl+o",
    "ctrl+n",
    "ctrl+w",
    "ctrl+f",
    "ctrl+h",
    "ctrl+t",
    "ctrl+tab",
    "alt+f4",
    "alt+tab",
    "win+d",
    "win+l",
    "win+e",
    "ctrl+alt+del",
    "ctrl+esc",
}


@dataclass
class ConflictWarning:
    key: str
    reason: str


def check_hotkey(key: str, existing_bindings: dict[str, str] | None = None) -> ConflictWarning | None:
    """Check if *key* conflicts with Windows system shortcuts or other bindings.

    Parameters
    ----------
    key:
        Normalised keybinding string, e.g. "ctrl+shift+r" or "F9".
    existing_bindings:
        Dict of ``{action_name: key}`` for already-registered application hotkeys.
        Used to detect intra-app conflicts.

    Returns
    -------
    ConflictWarning if there is a conflict, otherwise None.
    """
    normalised = _normalise(key)

    if normalised in _WINDOWS_RESERVED:
        return ConflictWarning(
            key=key,
            reason=f"'{key}' is a reserved Windows system shortcut.",
        )

    if existing_bindings:
        for action, bound_key in existing_bindings.items():
            if _normalise(bound_key) == normalised:
                return ConflictWarning(
                    key=key,
                    reason=f"'{key}' is already bound to '{action}'.",
                )

    return None


def check_all_hotkeys(bindings: dict[str, str]) -> list[ConflictWarning]:
    """Check an entire hotkey dict for system conflicts and intra-app duplicates.

    Returns a (possibly empty) list of ConflictWarnings.
    """
    warnings: list[ConflictWarning] = []
    seen: dict[str, str] = {}

    for action, key in bindings.items():
        normalised = _normalise(key)
        if normalised in _WINDOWS_RESERVED:
            warnings.append(ConflictWarning(key=key, reason=f"'{key}' is a reserved Windows system shortcut."))
        elif normalised in seen:
            warnings.append(ConflictWarning(key=key, reason=f"'{key}' is already used by '{seen[normalised]}'."))
        else:
            seen[normalised] = action

    return warnings


def check_system_hotkey(combo: str) -> ConflictWarning | None:
    """Probe whether *combo* is already registered globally by another application.

    Uses ``RegisterHotKey`` / ``UnregisterHotKey`` on Windows.  Returns None on
    non-Windows platforms or when the key name cannot be mapped to a VK code.
    """
    if sys.platform != "win32":
        return None
    modifiers, vk = _combo_to_win32(combo)
    if vk is None:
        return None
    try:
        import ctypes
        user32 = ctypes.windll.user32
        _ID = 0xACE1  # arbitrary per-thread probe ID
        MOD_NOREPEAT = 0x4000
        if user32.RegisterHotKey(None, _ID, modifiers | MOD_NOREPEAT, vk):
            user32.UnregisterHotKey(None, _ID)
            return None
        return ConflictWarning(
            key=combo,
            reason=f"'{combo}' is already in use by another application.",
        )
    except Exception:
        return None


# Key name (as produced by hotkeys_panel capture) → Windows Virtual Key code
_KEY_TO_VK: dict[str, int] = {
    **{chr(97 + i): 65 + i for i in range(26)},   # a-z → VK 65-90
    **{str(i): 48 + i for i in range(10)},          # 0-9 → VK 48-57
    **{f'f{i + 1}': 112 + i for i in range(12)},   # f1-f12 → VK 112-123
    'backspace': 8, 'tab': 9, 'enter': 13, 'escape': 27, 'space': 32,
    'page up': 33, 'page down': 34, 'end': 35, 'home': 36,
    'left': 37, 'up': 38, 'right': 39, 'down': 40,
    'insert': 45, 'delete': 46,
}


def _combo_to_win32(combo: str) -> tuple[int, int | None]:
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    parts = [p.strip().lower() for p in combo.split("+")]
    modifiers = 0
    for p in parts[:-1]:
        if p == "ctrl":
            modifiers |= MOD_CONTROL
        elif p == "alt":
            modifiers |= MOD_ALT
        elif p == "shift":
            modifiers |= MOD_SHIFT
        elif p in ("win", "windows"):
            modifiers |= MOD_WIN
    vk = _KEY_TO_VK.get(parts[-1]) if parts else None
    return modifiers, vk


def _normalise(key: str) -> str:
    """Lowercase and sort modifier keys for consistent comparison."""
    parts = [p.strip().lower() for p in key.split("+")]
    modifiers = sorted(p for p in parts[:-1] if p in {"ctrl", "alt", "shift", "win"})
    main = parts[-1]
    return "+".join(modifiers + [main])
