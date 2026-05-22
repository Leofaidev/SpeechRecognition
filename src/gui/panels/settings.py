"""Settings panel (T-89, T-90, T-91)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.signal_meter import SignalMeter
from gui.widgets.context_menu import bind_context_menu


_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
_TRANSLATION_ENGINES = ["opus-mt", "google"]
_PYANNOTE_MODELS = (
    "pyannote/speaker-diarization-3.1",
    "pyannote/segmentation-3.0",
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


class SettingsPanel(BasePanel):
    """All persistent configuration options."""

    def __init__(self, master, config, t: Callable,
                 on_language_change: Callable[[str], None] | None = None,
                 available_languages: list[str] | None = None,
                 available_devices: list[str] | None = None,
                 **kwargs) -> None:
        self._on_language_change = on_language_change or (lambda c: None)
        self._available_languages = available_languages or ["en"]
        self._available_devices = available_devices or []
        super().__init__(master, config, t, **kwargs)

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.grid_rowconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # ---- Audio section -------------------------------------------
        self._section(scroll, t("settings_audio_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("label_device")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._device_var = ctk.StringVar(
            value=self._config.get("input_device", ""))
        self._device_menu = ctk.CTkOptionMenu(
            scroll, variable=self._device_var,
            values=self._available_devices or ["—"],
            command=self._on_device_change)
        self._device_menu.grid(row=row, column=1, sticky="ew", padx=12, pady=4)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_signal_label")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self.signal_meter = SignalMeter(scroll)
        self.signal_meter.grid(row=row, column=1, sticky="w", padx=12, pady=4)
        row += 1

        # ---- Language section ----------------------------------------
        self._section(scroll, t("settings_language_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_language_label")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._lang_var = ctk.StringVar(
            value=self._config.get("ui_language", "en"))
        self._lang_menu = ctk.CTkOptionMenu(
            scroll, variable=self._lang_var,
            values=self._available_languages,
            command=self._on_language_change)
        self._lang_menu.grid(row=row, column=1, sticky="w", padx=4, pady=4)
        ctk.CTkLabel(scroll, text=t("lang_name"),
                     text_color="gray60").grid(
            row=row, column=2, sticky="w", padx=4, pady=4)
        row += 1

        # ---- Translation section -------------------------------------
        self._section(scroll, t("settings_translation_section"), row)
        row += 1
        self._trans_enabled = ctk.BooleanVar(
            value=self._config.get("translation_enabled", False))
        ctk.CTkCheckBox(scroll, text=t("settings_translation_enabled"),
                        variable=self._trans_enabled,
                        command=self._on_trans_enabled).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_translation_engine")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._engine_var = ctk.StringVar(
            value=self._config.get("translation_engine", "opus-mt"))
        ctk.CTkOptionMenu(scroll, variable=self._engine_var,
                          values=_TRANSLATION_ENGINES,
                          command=self._on_engine_change).grid(
            row=row, column=1, sticky="ew", padx=12, pady=4)
        row += 1
        self._quality_label = ctk.CTkLabel(
            scroll, text=t("settings_opus_quality_warning"),
            text_color="#ff9800")
        self._quality_label.grid(row=row, column=0, columnspan=2,
                                  sticky="w", padx=12, pady=2)
        self._quality_label.grid_remove()
        row += 1

        # ---- Output section ------------------------------------------
        self._section(scroll, t("settings_output_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_output_folder")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._output_folder_var = ctk.StringVar(
            value=self._config.get("output_folder", ""))
        output_entry = ctk.CTkEntry(scroll, textvariable=self._output_folder_var)
        output_entry.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        bind_context_menu(output_entry, t=t)
        ctk.CTkButton(scroll, text=t("btn_browse"), width=80,
                      command=self._browse_output).grid(
            row=row, column=2, padx=4, pady=4)
        row += 1

        # ---- Sound section -------------------------------------------
        self._section(scroll, t("settings_sound_section"), row)
        row += 1
        self._sound_enabled = ctk.BooleanVar(
            value=self._config.get("sound_enabled", True))
        ctk.CTkCheckBox(scroll, text=t("settings_sound_enabled"),
                        variable=self._sound_enabled,
                        command=self._on_sound_enabled).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1

        # ---- Whisper model -------------------------------------------
        self._section(scroll, t("settings_model_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_model_label")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._model_var = ctk.StringVar(
            value=self._config.get("whisper_model", "medium"))
        ctk.CTkOptionMenu(scroll, variable=self._model_var,
                          values=_WHISPER_MODELS,
                          command=self._on_model_change).grid(
            row=row, column=1, sticky="ew", padx=12, pady=4)
        row += 1

        # ---- Tray section -------------------------------------------
        self._section(scroll, t("settings_tray_section"), row)
        row += 1
        self._minimize_tray = ctk.BooleanVar(
            value=self._config.get("minimize_to_tray", False))
        ctk.CTkCheckBox(scroll, text=t("settings_minimize_tray"),
                        variable=self._minimize_tray,
                        command=self._on_minimize_tray).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1
        self._tray_notify = ctk.BooleanVar(
            value=self._config.get("tray_notifications", True))
        ctk.CTkCheckBox(scroll, text=t("settings_tray_notify"),
                        variable=self._tray_notify,
                        command=self._on_tray_notify).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1
        self._auto_start = ctk.BooleanVar(
            value=self._config.get("auto_start", False))
        ctk.CTkCheckBox(scroll, text=t("settings_auto_start"),
                        variable=self._auto_start,
                        command=self._on_auto_start).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1

        # ---- HuggingFace licence -------------------------------------
        self._section(scroll, t("settings_licence_section"), row)
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_hf_token_label")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        self._hf_token_var = ctk.StringVar(
            value=self._config.get("huggingface_token", ""))
        hf_entry = ctk.CTkEntry(scroll, textvariable=self._hf_token_var,
                                width=300)
        hf_entry.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
        hf_entry.bind("<Return>", lambda _: self._test_and_save_token())
        bind_context_menu(hf_entry, t=t)
        self._hf_test_btn = ctk.CTkButton(
            scroll, text=t("settings_hf_token_test_btn"),
            width=120, command=self._test_and_save_token)
        self._hf_test_btn.grid(row=row, column=2, padx=4, pady=4)
        row += 1
        self._hf_token_status = ctk.CTkLabel(scroll, text="", text_color="gray60")
        self._hf_token_status.grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 2))
        row += 1
        ctk.CTkLabel(scroll, text=t("settings_hf_token_hint"),
                     text_color="gray60", wraplength=420,
                     justify="left").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 6))
        row += 1
        accepted = self._config.get("licence_accepted", False)
        lbl_text = (t("settings_licence_accepted") if accepted
                    else t("settings_licence_not_accepted"))
        lbl_colour = "#4caf50" if accepted else "#ff9800"
        self._licence_status = ctk.CTkLabel(scroll, text=lbl_text,
                                             text_color=lbl_colour)
        self._licence_status.grid(row=row, column=0, columnspan=2,
                                   sticky="w", padx=12, pady=4)
        row += 1
        ctk.CTkButton(scroll, text=t("settings_licence_btn"),
                      command=self._show_licence_dialog).grid(
            row=row, column=0, columnspan=2, sticky="w", padx=12, pady=4)
        row += 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section(self, parent, label: str, row: int) -> None:
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", padx=8, pady=(12, 2))

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_device_change(self, value: str) -> None:
        self._config.set("input_device", value)

    def _on_trans_enabled(self) -> None:
        self._config.set("translation_enabled", self._trans_enabled.get())

    def _on_engine_change(self, value: str) -> None:
        self._config.set("translation_engine", value)
        pairs_with_warnings = {("en", "zh"), ("en", "zh-cn")}
        src = self._config.get("source_language", "auto")
        tgt = self._config.get("target_language", "en")
        if (src, tgt) in pairs_with_warnings and value == "opus-mt":
            self._quality_label.grid()
        else:
            self._quality_label.grid_remove()

    def _on_sound_enabled(self) -> None:
        self._config.set("sound_enabled", self._sound_enabled.get())

    def _on_model_change(self, value: str) -> None:
        if value != self._config.get("whisper_model", "medium"):
            if ctk.messagebox and ctk.messagebox.askyesno(
                    "Whisper Model",
                    self._t("model_change_confirm")):
                self._config.set("whisper_model", value)

    def _on_minimize_tray(self) -> None:
        self._config.set("minimize_to_tray", self._minimize_tray.get())

    def _on_tray_notify(self) -> None:
        self._config.set("tray_notifications", self._tray_notify.get())

    def _on_auto_start(self) -> None:
        enabled = self._auto_start.get()
        self._config.set("auto_start", enabled)
        try:
            from platforms.windows.autostart import set_autostart
            set_autostart(enabled)
        except Exception:
            pass

    def _browse_output(self) -> None:
        try:
            from tkinter import filedialog
            folder = filedialog.askdirectory()
            if folder:
                self._output_folder_var.set(folder)
                self._config.set("output_folder", folder)
        except Exception:
            pass

    def _show_licence_dialog(self) -> None:
        from gui.panels.licence_dialog import LicenceDialog
        LicenceDialog(self, config=self._config, t=self._t,
                      on_accepted=self._on_licence_accepted)

    def _test_and_save_token(self) -> None:
        import threading
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
            # Token valid + model access confirmed → licence implicitly accepted
            self._config.set("licence_accepted", True)
            self._hf_token_status.configure(text=msg, text_color="#4caf50")
            self._licence_status.configure(
                text=self._t("settings_licence_accepted"),
                text_color="#4caf50",
            )
        else:
            self._hf_token_status.configure(text=msg, text_color="#f44336")

    def _on_licence_accepted(self) -> None:
        self._config.set("licence_accepted", True)
        self._licence_status.configure(
            text=self._t("settings_licence_accepted"),
            text_color="#4caf50",
        )
