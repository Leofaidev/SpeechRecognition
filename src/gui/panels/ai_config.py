"""AI model configuration panel — faster-whisper and pyannote.audio parameters."""

from __future__ import annotations

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu

_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]


class AIConfigPanel(BasePanel):
    """Configure faster-whisper and pyannote.audio model parameters."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # ---- faster-whisper section ----------------------------------------
        self._section(scroll, t("ai_config_whisper_section"), row)
        row += 1

        row = self._add_dropdown(scroll, row,
            t("ai_config_model_size_label"),
            "whisper_model", _WHISPER_MODELS, "medium",
            "ai_config_model_size_info", width=160)

        row = self._add_entry(scroll, row,
            t("ai_config_language_label"),
            "whisper_language", "", str,
            "ai_config_language_info")

        row = self._add_entry(scroll, row,
            t("ai_config_beam_size_label"),
            "whisper_beam_size", 5, int,
            "ai_config_beam_size_info")

        row = self._add_entry(scroll, row,
            t("ai_config_no_speech_label"),
            "bad_audio_threshold", 0.6, float,
            "ai_config_no_speech_info")

        row = self._add_bool(scroll, row,
            t("ai_config_vad_label"),
            "whisper_vad_filter", False,
            "ai_config_vad_info")

        row = self._add_bool(scroll, row,
            t("ai_config_word_ts_label"),
            "whisper_word_timestamps", False,
            "ai_config_word_ts_info")

        # ---- pyannote.audio section ----------------------------------------
        self._section(scroll, t("ai_config_pyannote_section"), row)
        row += 1

        row = self._add_entry(scroll, row,
            t("ai_config_clustering_label"),
            "pyannote_clustering_threshold", 0.715, float,
            "ai_config_clustering_info")

        row = self._add_entry(scroll, row,
            t("ai_config_max_speakers_label"),
            "pyannote_max_speakers", 0, int,
            "ai_config_max_speakers_info")

    # ------------------------------------------------------------------
    # Row builders
    # ------------------------------------------------------------------

    def _section(self, parent, label: str, row: int) -> None:
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", padx=8, pady=(12, 2))

    def _add_dropdown(self, parent, row: int, label: str,
                      config_key: str, values: list, default: str,
                      info_key: str, width: int | None = None) -> int:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        var = ctk.StringVar(value=self._config.get(config_key, default))

        def _on_change(v, k=config_key):
            self._config.set(k, v)

        kw = {"width": width} if width else {}
        ctk.CTkOptionMenu(parent, variable=var, values=values,
                          command=_on_change, **kw).grid(
            row=row, column=1,
            sticky="w" if width else "ew",
            padx=4, pady=4)
        self._info_btn(parent, row, info_key)
        return row + 1

    def _add_entry(self, parent, row: int, label: str,
                   config_key: str, default, cast: type,
                   info_key: str) -> int:
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        var = ctk.StringVar(value=str(self._config.get(config_key, default)))
        entry = ctk.CTkEntry(parent, textvariable=var, width=120)
        entry.grid(row=row, column=1, sticky="w", padx=4, pady=4)
        bind_context_menu(entry, t=self._t)

        def _save(_event=None, k=config_key, v=var, c=cast, d=default):
            raw = v.get().strip()
            try:
                val = c(raw) if raw else d
            except (ValueError, TypeError):
                val = d
                v.set(str(d))
            self._config.set(k, val)

        entry.bind("<Return>", _save)
        entry.bind("<FocusOut>", _save)
        self._info_btn(parent, row, info_key)
        return row + 1

    def _add_bool(self, parent, row: int, label: str,
                  config_key: str, default: bool, info_key: str) -> int:
        t = self._t
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        true_lbl  = t("ai_config_bool_true")
        false_lbl = t("ai_config_bool_false")
        saved = self._config.get(config_key, default)
        var = ctk.StringVar(value=true_lbl if saved else false_lbl)

        def _on_change(v, k=config_key, tl=true_lbl):
            self._config.set(k, v == tl)

        ctk.CTkOptionMenu(parent, variable=var,
                          values=[true_lbl, false_lbl],
                          width=120, command=_on_change).grid(
            row=row, column=1, sticky="w", padx=4, pady=4)
        self._info_btn(parent, row, info_key)
        return row + 1

    def _info_btn(self, parent, row: int, info_key: str) -> None:
        ctk.CTkButton(
            parent, text="?", width=28, height=28,
            fg_color=("#3a7ebf", "#1f6aa5"),
            hover_color=("#2b6aaa", "#18568a"),
            text_color="white",
            border_width=0,
            corner_radius=14,
            command=lambda k=info_key: self._show_info(k),
        ).grid(row=row, column=2, padx=(4, 8), pady=4)

    def _show_info(self, info_key: str) -> None:
        t = self._t
        win = ctk.CTkToplevel(self)
        win.title(t("ai_config_info_title"))
        win.geometry("480x260")
        win.resizable(True, True)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        txt = ctk.CTkTextbox(win, wrap="word", activate_scrollbars=True)
        txt.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        txt.insert("end", t(info_key))
        txt.configure(state="disabled")
        bind_context_menu(txt, readonly=True, t=t)

        ctk.CTkButton(win, text=t("btn_close"), command=win.destroy).pack(pady=(4, 12))
        win.after(100, win.focus_force)

    def update_strings(self, t) -> None:
        super().update_strings(t)
        for w in self.winfo_children():
            w.destroy()
        self.build()
