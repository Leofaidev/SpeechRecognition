"""Output Content Configuration panel (T-103)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel


_FIELDS = ["timestamp", "speaker", "language", "confidence", "text", "translation"]
_FORMATS = ["txt", "docx", "srt", "json"]


class OutputConfigPanel(BasePanel):
    """Six field toggles, format checkboxes, destinations, folder picker."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.grid_rowconfigure(0, weight=1)

        row = 0

        # ---- Output fields ------------------------------------------
        self._section(scroll, t("output_fields_section"), row); row += 1
        self._field_vars: dict[str, ctk.BooleanVar] = {}
        saved_fields = self._config.get("output_fields", {f: True for f in _FIELDS})
        for field in _FIELDS:
            var = ctk.BooleanVar(value=saved_fields.get(field, True))
            self._field_vars[field] = var
            key = f"output_field_{field}"
            ctk.CTkCheckBox(scroll, text=t(key), variable=var,
                             command=lambda f=field, v=var: self._save_field(f, v.get())
                             ).grid(row=row, column=0, sticky="w", padx=12, pady=2)
            row += 1

        # ---- Formats ------------------------------------------------
        self._section(scroll, t("output_formats_section"), row); row += 1
        self._format_vars: dict[str, ctk.BooleanVar] = {}
        saved_formats = self._config.get("output_formats", ["txt"])
        for fmt in _FORMATS:
            var = ctk.BooleanVar(value=fmt in saved_formats)
            self._format_vars[fmt] = var
            ctk.CTkCheckBox(scroll, text=fmt.upper(), variable=var,
                             command=self._save_formats).grid(
                row=row, column=0, sticky="w", padx=12, pady=2)
            row += 1

        # ---- Destinations -------------------------------------------
        self._section(scroll, t("output_dest_section"), row); row += 1
        self._dest_file = ctk.BooleanVar(
            value=self._config.get("output_to_file", True))
        ctk.CTkCheckBox(scroll, text=t("output_dest_file"),
                        variable=self._dest_file,
                        command=lambda: self._config.set(
                            "output_to_file", self._dest_file.get())).grid(
            row=row, column=0, sticky="w", padx=12, pady=2); row += 1

        self._dest_display = ctk.BooleanVar(
            value=self._config.get("output_to_display", True))
        ctk.CTkCheckBox(scroll, text=t("output_dest_display"),
                        variable=self._dest_display,
                        command=lambda: self._config.set(
                            "output_to_display", self._dest_display.get())).grid(
            row=row, column=0, sticky="w", padx=12, pady=2); row += 1

        self._dest_clipboard = ctk.BooleanVar(
            value=self._config.get("output_to_clipboard", False))
        ctk.CTkCheckBox(scroll, text=t("output_dest_clipboard"),
                        variable=self._dest_clipboard,
                        command=self._on_clipboard_dest).grid(
            row=row, column=0, sticky="w", padx=12, pady=2); row += 1

        self._clipboard_warn = ctk.CTkLabel(
            scroll, text=t("output_clipboard_file_warning"),
            text_color="#ff9800")
        self._clipboard_warn.grid(row=row, column=0, sticky="w",
                                   padx=12, pady=2)
        self._clipboard_warn.grid_remove()
        row += 1

        # ---- Output folder ------------------------------------------
        self._section(scroll, t("output_folder_label"), row); row += 1
        folder_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        folder_frame.grid(row=row, column=0, sticky="ew", padx=12, pady=4)
        folder_frame.grid_columnconfigure(0, weight=1)
        self._folder_var = ctk.StringVar(
            value=self._config.get("output_folder", ""))
        ctk.CTkEntry(folder_frame, textvariable=self._folder_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(folder_frame, text=t("btn_browse"), width=80,
                      command=self._browse_folder).grid(row=0, column=1)

    def _section(self, parent, label: str, row: int) -> None:
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=8, pady=(12, 2))

    def _save_field(self, field: str, value: bool) -> None:
        current = self._config.get("output_fields",
                                    {f: True for f in _FIELDS})
        current[field] = value
        self._config.set("output_fields", current)

    def _save_formats(self) -> None:
        active = [f for f, v in self._format_vars.items() if v.get()]
        self._config.set("output_formats", active)

    def _on_clipboard_dest(self) -> None:
        self._config.set("output_to_clipboard", self._dest_clipboard.get())

    def _browse_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self._folder_var.set(folder)
            self._config.set("output_folder", folder)
