"""AI model configuration panel — faster-whisper and pyannote.audio parameters."""

from __future__ import annotations

import threading

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu

_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]

_PYANNOTE_MODELS = (
    "pyannote/speaker-diarization-3.1",
    "pyannote/segmentation-3.0",
)
_PYANNOTE_URLS = (
    "https://huggingface.co/pyannote/speaker-diarization-3.1",
    "https://huggingface.co/pyannote/segmentation-3.0",
)


def _validate_hf_token(token: str, t_valid: str, t_invalid: str,
                        t_gated: str) -> tuple[bool, str]:
    """Validate *token* against HuggingFace — runs in a background thread."""
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        try:
            api.whoami(token=token)
        except Exception:
            return False, t_invalid
        for model_id in _PYANNOTE_MODELS:
            try:
                api.model_info(model_id, token=token)
            except Exception as exc:
                msg = str(exc)
                if "403" in msg or "gated" in msg.lower() or \
                        type(exc).__name__ in ("GatedRepoError", "RepositoryNotFoundError"):
                    return False, t_gated.format(model=model_id)
        return True, t_valid
    except ImportError:
        return True, t_valid


class AIConfigPanel(BasePanel):
    """Configure faster-whisper and pyannote.audio model parameters."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        scroll.grid_columnconfigure(3, weight=1)  # spacer — keeps button next to field

        row = 0

        # ---- HuggingFace Licence section ----------------------------------
        self._section(scroll, t("settings_licence_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_hf_token_label"), anchor="w").grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._hf_token_var = ctk.StringVar(
            value=self._config.get("huggingface_token", ""))
        hf_entry = ctk.CTkEntry(scroll, textvariable=self._hf_token_var, width=260)
        hf_entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
        hf_entry.bind("<Return>", lambda _: self._test_and_save_token())
        hf_entry.bind("<FocusOut>", lambda _: self._autosave_token())
        bind_context_menu(hf_entry, t=t)
        self._hf_test_btn = ctk.CTkButton(
            scroll, text=t("settings_hf_token_test_btn"),
            width=120, command=self._test_and_save_token)
        self._hf_test_btn.grid(row=row, column=3, padx=4, pady=4)
        row += 1
        self._hf_token_status = ctk.CTkLabel(scroll, text="", text_color="gray60")
        self._hf_token_status.grid(
            row=row, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 2))
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_hf_token_hint"),
                     text_color="gray60", wraplength=460,
                     justify="left").grid(
            row=row, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 6))
        row += 1
        accepted = self._config.get("licence_accepted", False)
        lbl_text = (t("settings_licence_accepted") if accepted
                    else t("settings_licence_not_accepted"))
        lbl_colour = "#4caf50" if accepted else "#ff9800"
        self._licence_status = ctk.CTkLabel(scroll, text=lbl_text,
                                             text_color=lbl_colour)
        self._licence_status.grid(row=row, column=0, columnspan=4,
                                   sticky="w", padx=12, pady=4)
        row += 1
        ctk.CTkButton(scroll, text=t("settings_licence_btn"),
                      command=self._open_licence_pages).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=12, pady=4)
        row += 1

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

        ctk.CTkButton(
            scroll, text=t("ai_config_reset_btn"),
            command=self._reset_defaults,
        ).grid(row=row, column=0, columnspan=4, sticky="w", padx=8, pady=(16, 8))

    # ------------------------------------------------------------------
    # Row builders
    # ------------------------------------------------------------------

    def _section(self, parent, label: str, row: int) -> None:
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=8, pady=(12, 2))

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

    # ------------------------------------------------------------------
    # HuggingFace licence callbacks
    # ------------------------------------------------------------------

    def _open_licence_pages(self) -> None:
        import webbrowser
        for url in _PYANNOTE_URLS:
            webbrowser.open(url)

    def _autosave_token(self) -> None:
        token = self._hf_token_var.get().strip()
        if token:
            self._config.set("huggingface_token", token)

    def _test_and_save_token(self) -> None:
        token = self._hf_token_var.get().strip()
        if not token:
            self._config.set("huggingface_token", None)
            self._hf_token_status.configure(text="", text_color="gray60")
            return
        self._hf_test_btn.configure(state="disabled")
        self._hf_token_status.configure(
            text=self._t("settings_hf_token_testing"), text_color="gray60")
        t_valid = self._t("settings_hf_token_valid")
        t_invalid = self._t("settings_hf_token_invalid")
        t_gated = self._t("settings_hf_token_gated")

        def _bg():
            ok, msg = _validate_hf_token(token, t_valid, t_invalid, t_gated)
            self.after(0, lambda: self._on_token_result(ok, msg, token))

        threading.Thread(target=_bg, daemon=True).start()

    def _on_token_result(self, ok: bool, msg: str, token: str) -> None:
        self._hf_test_btn.configure(state="normal")
        if ok:
            self._config.set("huggingface_token", token)
            self._config.set("licence_accepted", True)
            self._hf_token_status.configure(text=msg, text_color="#4caf50")
            self._licence_status.configure(
                text=self._t("settings_licence_accepted"),
                text_color="#4caf50",
            )
        else:
            self._hf_token_status.configure(text=msg, text_color="#f44336")

    _DEFAULTS = {
        "whisper_model":                "medium",
        "whisper_language":             "",
        "whisper_beam_size":            5,
        "bad_audio_threshold":          0.6,
        "whisper_vad_filter":           False,
        "whisper_word_timestamps":      False,
        "pyannote_clustering_threshold": 0.715,
        "pyannote_max_speakers":        0,
    }

    def _reset_defaults(self) -> None:
        for key, val in self._DEFAULTS.items():
            self._config.set(key, val)
        self.update_strings(self._t)

    def update_strings(self, t) -> None:
        super().update_strings(t)
        for w in self.winfo_children():
            w.destroy()
        self.build()
