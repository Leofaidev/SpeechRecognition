"""Settings panel (T-89, T-90, T-91)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.signal_meter import SignalMeter
from gui.widgets.context_menu import bind_context_menu


_TRANSLATION_ENGINES = ["opus-mt", "google"]


# Display name → language code (for target-language selector)
_TARGET_LANGUAGES: dict[str, str] = {
    "English":    "en",
    "Русский":    "ru",
    "Deutsch":    "de",
    "Français":   "fr",
    "Español":    "es",
    "Italiano":   "it",
    "Português":  "pt",
    "中文":        "zh",
    "日本語":      "ja",
    "한국어":      "ko",
    "العربية":    "ar",
    "Nederlands": "nl",
    "Polski":     "pl",
    "Türkçe":     "tr",
    "Українська": "uk",
    "Suomi":      "fi",
}
_CODE_TO_NAME = {v: k for k, v in _TARGET_LANGUAGES.items()}


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
        ctk.CTkLabel(scroll, text=t("settings_target_language")).grid(
            row=row, column=0, sticky="w", padx=12, pady=4)
        saved_tgt = self._config.get("target_language", "en")
        self._target_lang_var = ctk.StringVar(
            value=_CODE_TO_NAME.get(saved_tgt, "English"))
        ctk.CTkOptionMenu(
            scroll, variable=self._target_lang_var,
            values=list(_TARGET_LANGUAGES.keys()),
            command=self._on_target_lang_change,
        ).grid(row=row, column=1, sticky="w", padx=12, pady=4)
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
        self._expand_after_session = ctk.BooleanVar(
            value=self._config.get("expand_after_session", False))
        ctk.CTkCheckBox(scroll, text=t("settings_expand_after_session"),
                        variable=self._expand_after_session,
                        command=self._on_expand_after_session).grid(
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


    # ------------------------------------------------------------------
    # Mic monitor (live signal meter while Settings panel is visible)
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        self._monitor_stop = threading.Event()
        threading.Thread(target=self._mic_monitor, daemon=True).start()

    def on_hide(self) -> None:
        if hasattr(self, "_monitor_stop"):
            self._monitor_stop.set()
        self.signal_meter.reset()

    def _mic_monitor(self) -> None:
        import numpy as np
        stop = self._monitor_stop
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            device_name = self._device_var.get()
            device_index = self._find_device_index(pa, device_name)
            chunk = 1024
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk,
            )
            while not stop.is_set():
                data = stream.read(chunk, exception_on_overflow=False)
                arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = float(np.sqrt(np.mean(arr ** 2))) / 32768.0
                self.after(0, lambda r=rms: self.signal_meter.set_level(r))
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception:
            pass

    @staticmethod
    def _find_device_index(pa, name: str):
        if not name or name in ("—", "Default"):
            return None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if name.lower() in info["name"].lower():
                return i
        return None

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
        # Restart mic monitor so the new device is sampled immediately
        self.on_hide()
        self.on_show()

    def _on_trans_enabled(self) -> None:
        self._config.set("translation_enabled", self._trans_enabled.get())

    def _on_engine_change(self, value: str) -> None:
        self._config.set("translation_engine", value)
        self._update_quality_warning()

    def _on_target_lang_change(self, display_name: str) -> None:
        code = _TARGET_LANGUAGES.get(display_name, "en")
        self._config.set("target_language", code)
        self._update_quality_warning()

    def _update_quality_warning(self) -> None:
        tgt = self._config.get("target_language", "en")
        engine = self._config.get("translation_engine", "opus-mt")
        limited_targets = {"zh", "zh-cn", "ja", "ko", "ar"}
        if tgt in limited_targets and engine == "opus-mt":
            self._quality_label.grid()
        else:
            self._quality_label.grid_remove()

    def _on_sound_enabled(self) -> None:
        self._config.set("sound_enabled", self._sound_enabled.get())

    def _on_minimize_tray(self) -> None:
        self._config.set("minimize_to_tray", self._minimize_tray.get())

    def _on_expand_after_session(self) -> None:
        self._config.set("expand_after_session", self._expand_after_session.get())

    def _on_tray_notify(self) -> None:
        self._config.set("tray_notifications", self._tray_notify.get())

    def _on_auto_start(self) -> None:
        enabled = self._auto_start.get()
        self._config.set("auto_start", enabled)
        try:
            import platforms as _plat
            _mod = __import__(
                f"platforms.{_plat.get_platform_name()}.auto_start",
                fromlist=["AutoStart"],
            )
            auto_start = _mod.AutoStart()
            if enabled:
                import sys as _sys
                auto_start.enable(_sys.executable)
            else:
                auto_start.disable()
        except Exception:
            pass

