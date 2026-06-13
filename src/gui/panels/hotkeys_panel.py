"""Hotkey Configuration panel (T-104)."""

from __future__ import annotations

import sys
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from config.hotkeys import check_hotkey, check_system_hotkey


# Windows VK code → keyboard-library key name (layout-independent)
_VK_TO_KEY: dict[int, str] = {
    **{65 + i: chr(97 + i) for i in range(26)},   # a–z (VK 65–90)
    **{48 + i: str(i) for i in range(10)},          # 0–9 (VK 48–57)
    **{112 + i: f'f{i + 1}' for i in range(12)},   # f1–f12 (VK 112–123)
    8: 'backspace', 9: 'tab', 13: 'enter', 27: 'escape', 32: 'space',
    33: 'page up', 34: 'page down', 35: 'end', 36: 'home',
    37: 'left', 38: 'up', 39: 'right', 40: 'down',
    45: 'insert', 46: 'delete',
}
_MODIFIER_VK = {16, 17, 18, 160, 161, 162, 163, 164, 165}

_ACTIONS = ["start_recording", "stop_recording"]
_DEFAULT_KEYS = {
    "start_recording": "ctrl+shift+r",
    "stop_recording": "ctrl+shift+s",
}


class HotkeysPanel(BasePanel):
    """Key capture controls per action, conflict warning, save/reset."""

    def __init__(self, master, config, t: Callable,
                 on_bindings_changed: Callable[[dict[str, str]], None] | None = None,
                 on_panel_show: Callable[[], None] | None = None,
                 on_panel_hide: Callable[[], None] | None = None,
                 **kwargs) -> None:
        self._on_bindings_changed = on_bindings_changed or (lambda b: None)
        self._on_panel_show = on_panel_show or (lambda: None)
        self._on_panel_hide = on_panel_hide or (lambda: None)
        self._prev_key_val: dict[str, str] = {}
        super().__init__(master, config, t, **kwargs)

    # ------------------------------------------------------------------
    # Panel lifecycle
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        self._on_panel_show()
        self.after(50, self._save_btn.focus_set)

    def on_hide(self) -> None:
        self._on_panel_hide()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=t("hotkeys_title"),
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 8))

        saved_bindings = self._config.get(
            "hotkeys", {a: _DEFAULT_KEYS[a] for a in _ACTIONS})

        self._key_vars: dict[str, ctk.StringVar] = {}
        self._warn_labels: dict[str, ctk.CTkLabel] = {}

        for row, action in enumerate(_ACTIONS, start=1):
            display_label = {
                "start_recording": t("hotkey_start_label"),
                "stop_recording": t("hotkey_stop_label"),
            }[action]

            ctk.CTkLabel(self, text=display_label).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            current_key = saved_bindings.get(action, _DEFAULT_KEYS[action])
            var = ctk.StringVar(value=current_key)
            self._key_vars[action] = var
            self._prev_key_val[action] = current_key

            entry = ctk.CTkEntry(self, textvariable=var, width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            entry.bind("<FocusIn>",
                       lambda e, a=action, v=var: self._on_entry_focus(a, v))
            entry.bind("<FocusOut>",
                       lambda e, a=action, v=var: self._on_entry_blur(a, v))
            entry.bind("<Key>", lambda e, a=action: self._capture_key(e, a))

            warn = ctk.CTkLabel(self, text="", text_color="#ff9800")
            warn.grid(row=row, column=2, sticky="w", padx=4, pady=4)
            self._warn_labels[action] = warn

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=len(_ACTIONS) + 1, column=0, columnspan=3,
                       sticky="e", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("btn_reset_hotkeys"),
                      fg_color="#555555",
                      command=self._reset_defaults).pack(side="left", padx=8)
        self._save_btn = ctk.CTkButton(btn_frame, text=t("btn_save_hotkeys"),
                                       command=self._save)
        self._save_btn.pack(side="left")

        # Limitation note
        ctk.CTkLabel(self, text=t("hotkey_system_check_note"),
                     text_color="gray60",
                     font=ctk.CTkFont(size=11),
                     wraplength=460,
                     justify="left").grid(
            row=len(_ACTIONS) + 2, column=0, columnspan=3,
            sticky="w", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------
    # Key capture
    # ------------------------------------------------------------------

    def _on_entry_focus(self, action: str, var: ctk.StringVar) -> None:
        """Store current value and clear field to signal key-capture mode."""
        self._prev_key_val[action] = var.get()
        var.set("")

    def _on_entry_blur(self, action: str, var: ctk.StringVar) -> None:
        """Restore previous binding if nothing was captured."""
        if not var.get().strip():
            var.set(self._prev_key_val.get(action, _DEFAULT_KEYS.get(action, "")))

    @staticmethod
    def _modifier_state() -> tuple[bool, bool, bool]:
        """Return (ctrl, shift, alt) using GetAsyncKeyState on Windows for
        reliability across keyboard layouts and system-key events."""
        if sys.platform == "win32":
            import ctypes
            _gaks = ctypes.windll.user32.GetAsyncKeyState
            ctrl  = bool(_gaks(0x11) & 0x8000)  # VK_CONTROL
            shift = bool(_gaks(0x10) & 0x8000)  # VK_SHIFT
            alt   = bool(_gaks(0x12) & 0x8000)  # VK_MENU (any Alt)
            return ctrl, shift, alt
        return False, False, False  # non-Windows: caller falls back to event.state

    # X11 keysyms that are modifier-only keys (Linux/macOS)
    _MODIFIER_SYMS = frozenset({
        'Control_L', 'Control_R', 'Shift_L', 'Shift_R',
        'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R', 'Super_L', 'Super_R',
        'ISO_Level3_Shift', 'Caps_Lock', 'Num_Lock',
    })

    def _capture_key(self, event, action: str) -> str:
        ctrl, shift, alt = self._modifier_state()
        # Fall back to Tkinter state bits on non-Windows
        if sys.platform != "win32":
            ctrl  = bool(event.state & 0x4)
            shift = bool(event.state & 0x1)
            alt   = bool(event.state & 0x8)   # Mod1 = Alt on X11 (not 0x20000)
        # Ctrl+Alt = AltGr: conflicts with keyboard layouts and causes stuck-modifier glitches
        if ctrl and alt:
            self._warn_labels[action].configure(
                text_color="#ff4444",
                text=self._t("hotkey_ctrl_alt_blocked"))
            return "break"
        parts = []
        if ctrl:
            parts.append("ctrl")
        if shift:
            parts.append("shift")
        if alt:
            parts.append("alt")
        if sys.platform == "win32":
            # Windows: use VK code table for layout-independent key names
            keycode = event.keycode
            if keycode not in _MODIFIER_VK:
                key_name = _VK_TO_KEY.get(keycode) or event.keysym.lower()
                parts.append(key_name)
        else:
            # Linux/macOS: X11 keycodes differ from Windows VK codes — use keysym directly
            if event.keysym not in self._MODIFIER_SYMS:
                parts.append(event.keysym.lower())
        combo = "+".join(parts)
        if combo and parts and parts[-1] not in ("ctrl", "shift", "alt"):
            self._key_vars[action].set(combo)
            self._prev_key_val[action] = combo
            self._check_conflict(action, combo)
            self.after(10, self._save_btn.focus_set)
        return "break"

    _TOGGLE_PAIR = {"start_recording", "stop_recording"}

    def _check_conflict(self, action: str, key: str) -> None:
        # start_recording and stop_recording may share a key (toggle mode — allowed)
        other_bindings = {
            a: v.get() for a, v in self._key_vars.items()
            if a != action
            and not (action in self._TOGGLE_PAIR and a in self._TOGGLE_PAIR)
        }
        warning = check_hotkey(key, existing_bindings=other_bindings)
        if warning:
            self._warn_labels[action].configure(
                text_color="#ff9800",
                text=self._t("hotkey_conflict_warning",
                              key=key, reason=warning.reason))
            return
        sys_warning = check_system_hotkey(key)
        if sys_warning:
            self._warn_labels[action].configure(
                text_color="#ff4444",
                text=self._t("hotkey_system_conflict", key=key))
            return
        self._warn_labels[action].configure(text_color="#ff9800", text="")

    def _reset_defaults(self) -> None:
        for action, key in _DEFAULT_KEYS.items():
            self._key_vars[action].set(key)
            self._prev_key_val[action] = key
            self._warn_labels[action].configure(text="")

    def _save(self) -> None:
        bindings = {a: v.get() for a, v in self._key_vars.items()}
        for action, key in bindings.items():
            if check_system_hotkey(key):
                self._warn_labels[action].configure(
                    text_color="#ff4444",
                    text=self._t("hotkey_system_conflict", key=key))
                return
        self._config.set("hotkeys", bindings)
        self._on_bindings_changed(bindings)
