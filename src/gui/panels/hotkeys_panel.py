"""Hotkey Configuration panel (T-104)."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu
from config.hotkeys import check_hotkey


_ACTIONS = ["start_recording", "stop_recording", "copy_to_clipboard"]
_DEFAULT_KEYS = {
    "start_recording": "ctrl+shift+r",
    "stop_recording": "ctrl+shift+s",
    "copy_to_clipboard": "ctrl+shift+c",
}


class HotkeysPanel(BasePanel):
    """Key capture controls per action, conflict warning, save/reset."""

    def __init__(self, master, config, t: Callable,
                 on_bindings_changed: Callable[[dict[str, str]], None] | None = None,
                 **kwargs) -> None:
        self._on_bindings_changed = on_bindings_changed or (lambda b: None)
        super().__init__(master, config, t, **kwargs)

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
            label_key = f"hotkey_{action.replace('_recording', '_label').replace('copy_to_', 'copy_')}"
            if label_key not in ["hotkey_start_label", "hotkey_stop_label",
                                   "hotkey_copy_label"]:
                label_key = f"hotkey_{action.split('_')[0]}_label"
            display_label = {
                "start_recording": t("hotkey_start_label"),
                "stop_recording": t("hotkey_stop_label"),
                "copy_to_clipboard": t("hotkey_copy_label"),
            }[action]

            ctk.CTkLabel(self, text=display_label).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            var = ctk.StringVar(value=saved_bindings.get(action,
                                                          _DEFAULT_KEYS[action]))
            self._key_vars[action] = var
            entry = ctk.CTkEntry(self, textvariable=var, width=200)
            entry.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            entry.bind("<Key>", lambda e, a=action: self._capture_key(e, a))
            bind_context_menu(entry)

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
            self._check_conflict(action, combo)
        return "break"

    def _check_conflict(self, action: str, key: str) -> None:
        other_bindings = {
            a: v.get() for a, v in self._key_vars.items() if a != action
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
            self._warn_labels[action].configure(text="")

    def _save(self) -> None:
        bindings = {a: v.get() for a, v in self._key_vars.items()}
        self._config.set("hotkeys", bindings)
        self._on_bindings_changed(bindings)
