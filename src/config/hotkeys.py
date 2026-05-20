"""Hotkey conflict detection (T-60).

Checks whether a proposed keybinding conflicts with common Windows shortcuts
or other registered application hotkeys.
"""

from __future__ import annotations

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


def _normalise(key: str) -> str:
    """Lowercase and sort modifier keys for consistent comparison."""
    parts = [p.strip().lower() for p in key.split("+")]
    modifiers = sorted(p for p in parts[:-1] if p in {"ctrl", "alt", "shift", "win"})
    main = parts[-1]
    return "+".join(modifiers + [main])
