"""Hotkey Configuration panel (T-104)."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from config.hotkeys import check_hotkey


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
        ctk.CTkButton(btn_frame, text=t("btn_save_hotkeys"),
                      command=self._save).pack(side="left")

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

    def _capture_key(self, event, action: str) -> str:
        parts = []
        if event.state & 0x4:
            parts.append("ctrl")
        if event.state & 0x1:
            parts.append("shift")
        if event.state & 0x20000:
            parts.append("alt")
        key_name = event.keysym.lower()
        if key_name not in ("control_l", "control_r", "shift_l", "shift_r",
                             "alt_l", "alt_r"):
            parts.append(key_name)
        combo = "+".join(parts)
        if combo:
            self._key_vars[action].set(combo)
            self._prev_key_val[action] = combo
            self._check_conflict(action, combo)
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
                text=self._t("hotkey_conflict_warning",
                              key=key, reason=warning.reason))
        else:
            self._warn_labels[action].configure(text="")

    def _reset_defaults(self) -> None:
        for action, key in _DEFAULT_KEYS.items():
            self._key_vars[action].set(key)
            self._prev_key_val[action] = key
            self._warn_labels[action].configure(text="")

    def _save(self) -> None:
        bindings = {a: v.get() for a, v in self._key_vars.items()}
        self._config.set("hotkeys", bindings)
        self._on_bindings_changed(bindings)
