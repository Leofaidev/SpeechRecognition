"""HuggingFace licence acceptance dialog (T-90)."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk


_LICENCE_TEXT = """\
pyannote.audio — Speaker Diarization Library
Copyright (c) 2020-present HerveBredin

This software requires acceptance of the following conditions:

1. You agree to use pyannote.audio for non-commercial research only, unless
   you have obtained a separate commercial licence from the copyright holder.

2. You agree not to redistribute pyannote.audio or any models derived from it
   without prior written permission.

3. Any academic publication using pyannote.audio must cite the relevant papers.

Full licence text is available at:
https://huggingface.co/pyannote/speaker-diarization-3.1

By clicking "I Accept the Licence", you confirm that you have read, understood,
and agree to the above conditions.
"""


class LicenceDialog(ctk.CTkToplevel):
    """Modal dialogue for viewing and accepting the HuggingFace licence."""

    def __init__(self, parent, config, t: Callable,
                 on_accepted: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._t = t
        self._on_accepted = on_accepted or (lambda: None)
        self.title(t("licence_title"))
        self.geometry("600x480")
        self.resizable(True, True)
        self.grab_set()
        self._build()
        self.focus_force()

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text=t("licence_intro"),
                     wraplength=560).grid(row=0, column=0, sticky="ew",
                                          padx=12, pady=(12, 4))

        text_box = ctk.CTkTextbox(self, wrap="word")
        text_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        text_box.insert("1.0", _LICENCE_TEXT)
        text_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="e", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("licence_decline_btn"),
                      fg_color="#555555",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=t("licence_accept_btn"),
                      command=self._accept).pack(side="left")

    def _accept(self) -> None:
        self._on_accepted()
        self.destroy()
        try:
            from tkinter import messagebox
            from tkinter import Tk
            root = self.nametowidget(".")
            if messagebox.askyesno(self._t("licence_title"),
                                   self._t("licence_accepted_msg") + "\n" +
                                   self._t("licence_restart_btn") + "?",
                                   parent=root):
                import sys, os
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            pass
