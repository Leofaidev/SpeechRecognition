"""About panel — version, author, build timestamp."""

from __future__ import annotations

import customtkinter as ctk

from gui.panels.base import BasePanel

APP_VERSION = "0.5.037"
APP_AUTHOR = "Leonid F"
BUILD_TIMESTAMP = "2026-05-28  00:00"


class AboutPanel(BasePanel):
    """Displays application version, author and build date."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=t("about_title"),
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 16))

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=1, column=0, sticky="w", padx=24, pady=4)

        rows = [
            ("about_version_label", APP_VERSION),
            ("about_author_label",  APP_AUTHOR),
            ("about_build_label",   BUILD_TIMESTAMP),
        ]
        for i, (key, value) in enumerate(rows):
            ctk.CTkLabel(info_frame, text=t(key) + ":",
                         font=ctk.CTkFont(weight="bold"),
                         anchor="w", width=120).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=4)
            ctk.CTkLabel(info_frame, text=value, anchor="w").grid(
                row=i, column=1, sticky="w", pady=4)

    def update_strings(self, t) -> None:
        super().update_strings(t)
        for widget in self.winfo_children():
            widget.destroy()
        self.build()
