"""Main application window (T-76 to T-88, T-127 to T-133).

Entry point: call ``run()`` to launch the GUI.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Callable

# platforms/ lives at the repo root (parent of src/); add it to sys.path so
# that "from platforms.xxx import ..." works when running via -m gui.app.
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import customtkinter as ctk

from config.store import ConfigStore
from gui.lang import LangManager
from gui.sound import SoundPlayer
from gui.hotkey_manager import HotkeyManager
from gui.pipeline import PipelineRunner
from gui.widgets.recording_dot import RecordingDot
from gui.widgets.signal_meter import SignalMeter
from gui.widgets.short_session_form import ShortSessionForm
from gui.panels.settings import SettingsPanel
from gui.panels.voice_profiles import VoiceProfilesPanel
from gui.panels.substitution_dict import SubstitutionDictPanel
from gui.panels.batch_queue import BatchQueuePanel
from gui.panels.output_config import OutputConfigPanel
from gui.panels.hotkeys_panel import HotkeysPanel
from gui.panels.speaker_labelling import SpeakerLabellingPanel
from gui.panels.session_history import SessionHistoryPanel
from gui.panels.backup_restore import BackupRestorePanel
from gui.panels.about import AboutPanel
from gui.widgets.context_menu import bind_context_menu


# Nav item order: key in lang file → panel class
_NAV_ITEMS = [
    ("nav_home", "home"),
    ("nav_settings", "settings"),
    ("nav_profiles", "profiles"),
    ("nav_dictionary", "dictionary"),
    ("nav_batch", "batch"),
    ("nav_output", "output"),
    ("nav_hotkeys", "hotkeys"),
    ("nav_labelling", "labelling"),
    ("nav_history", "history"),
    ("nav_backup", "backup"),
    ("nav_about", "about"),
]

_SIDEBAR_WIDTH = 170
_MIN_WINDOW_SIZE = (980, 620)


def _save_fragment_wav(audio, sample_rate: int,
                        start_sec: float, end_sec: float) -> str:
    """Slice *audio* and write to a temp WAV file. Returns the file path."""
    import wave, tempfile, os
    import numpy as np
    start_s = max(0, int(start_sec * sample_rate))
    end_s = min(len(audio), int(end_sec * sample_rate))
    fragment = audio[start_s:end_s]
    fragment_i16 = (fragment * 32767).clip(-32768, 32767).astype(np.int16)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(fragment_i16.tobytes())
    return path


class App(ctk.CTk):
    """Root application window."""

    def __init__(self, config: ConfigStore | None = None,
                 lang_dir: Path | None = None) -> None:
        super().__init__()

        # Services
        self._config = config or ConfigStore()
        lang_code = self._config.get("ui_language", "en")
        self._lang = LangManager(lang_code, lang_dir=lang_dir)
        self._sound = SoundPlayer(enabled=self._config.get("sound_enabled", True))
        self._hotkeys = HotkeyManager(
            self._config.get("hotkeys", None))

        # State
        self._recording = False
        self._mode = self._config.get("recording_mode", "regular")
        self._capture_audio = None   # np.ndarray filled by capture module
        self._capture_sr = 16000
        self._capture_thread: threading.Thread | None = None
        self._capture_stop = threading.Event()
        self._minimized_to_tray = False
        self._pending_result = None          # PipelineResult awaiting labelling
        self._pending_fragment_paths: dict = {}  # speaker_id → temp WAV path

        self._pipeline = PipelineRunner(
            self._config,
            on_progress=self._on_pipeline_progress,
            on_done=self._on_pipeline_done,
            on_error=self._on_pipeline_error,
        )

        # Tray (lazy — only started if minimize_to_tray is on)
        self._tray = None

        # Window setup
        self.title(self._lang.t("app_title"))
        self.minsize(*_MIN_WINDOW_SIZE)
        self.geometry(f"{_MIN_WINDOW_SIZE[0]}x{_MIN_WINDOW_SIZE[1]}")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_layout()
        self._register_hotkeys()

        # Start signal meter polling
        self._meter_after: str | None = None
        self._poll_signal_level()

        # Minimize-to-tray intercept
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        t = self._lang.t

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Sidebar ------------------------------------------------
        self._sidebar = ctk.CTkFrame(self, width=_SIDEBAR_WIDTH,
                                      corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)

        ctk.CTkLabel(self._sidebar, text="WSP",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(16, 4), padx=12)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for lang_key, panel_id in _NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar,
                text=t(lang_key),
                width=_SIDEBAR_WIDTH - 20,
                height=34,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda pid=panel_id: self._show_panel(pid),
            )
            btn.pack(pady=2, padx=10)
            self._nav_buttons[panel_id] = btn

        # ---- Right: main area ---------------------------------------
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        # Control bar (top)
        self._build_control_bar(right)

        # Status bar
        self._build_status_bar(right)

        # Content area (panel / main view) — row 2
        self._content = ctk.CTkFrame(right, fg_color="transparent")
        self._content.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        # Build all panels (hidden initially)
        self._panels: dict[str, ctk.CTkFrame] = {}
        self._build_panels()

        # Main view (output text / short-session form)
        self._build_main_view()

        # Playback bar (bottom)
        self._build_playback_bar(right)

        # Show main view by default
        self._active_panel: str | None = None
        self._show_main_view()

    def _build_control_bar(self, parent) -> None:
        t = self._lang.t
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

        self._devices = self._get_device_names()

        # Group selector
        self._lbl_group = ctk.CTkLabel(bar, text=t("label_group"))
        self._lbl_group.pack(side="left", padx=(8, 2))
        self._group_var = ctk.StringVar(
            value=self._config.get("active_speaker_group", ""))
        self._group_menu = ctk.CTkOptionMenu(
            bar, variable=self._group_var,
            values=self._get_group_names() or ["—"],
            width=140,
            command=self._on_group_change)
        self._group_menu.pack(side="left", padx=4)

        # Mode toggle
        self._lbl_mode = ctk.CTkLabel(bar, text=t("label_mode"))
        self._lbl_mode.pack(side="left", padx=(12, 2))
        self._mode_var = ctk.StringVar(
            value=t("mode_regular") if self._mode == "regular"
            else t("mode_short"))
        self._mode_toggle = ctk.CTkSegmentedButton(
            bar,
            values=[t("mode_regular"), t("mode_short")],
            variable=self._mode_var,
            command=self._on_mode_change,
        )
        self._mode_toggle.pack(side="left", padx=8)

        # Single Start/Stop toggle button
        self._btn_record = ctk.CTkButton(
            bar, text=t("btn_start"), width=80, command=self._start_recording)
        self._btn_record.pack(side="left", padx=4)

    def _build_status_bar(self, parent) -> None:
        t = self._lang.t
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=4, pady=2)

        self._rec_dot = RecordingDot(bar)
        self._rec_dot.pack(side="left", padx=(4, 8))

        self._status_label = ctk.CTkLabel(bar, text=t("status_idle"))
        self._status_label.pack(side="left", padx=4)

        # Signal meter
        ctk.CTkLabel(bar, text="").pack(side="left", padx=8)
        self._signal_meter = SignalMeter(bar, width=140)
        self._signal_meter.pack(side="left", padx=4)

        # File progress bar
        self._file_progress = ctk.CTkProgressBar(bar, width=200)
        self._file_progress.set(0)
        self._file_progress.pack(side="left", padx=8)

        # Queue progress bar (hidden outside batch)
        self._queue_progress = ctk.CTkProgressBar(bar, width=160)
        self._queue_progress.set(0)
        self._queue_label = ctk.CTkLabel(bar, text="")
        # Hidden by default (T-80)
        self._hide_queue_progress()

    def _build_main_view(self) -> None:
        t = self._lang.t
        self._main_view = ctk.CTkFrame(
            self._content, fg_color="transparent")

        # Regular mode: single text area
        self._output_text = ctk.CTkTextbox(self._main_view, wrap="word",
                                            state="disabled")
        self._output_text.grid(row=0, column=0, sticky="nsew")
        bind_context_menu(self._output_text, readonly=True, t=self._lang.t)
        self._main_view.grid_columnconfigure(0, weight=1)
        self._main_view.grid_rowconfigure(0, weight=1)

        # Short Session form (T-127)
        self._short_form = ShortSessionForm(
            self._main_view,
            on_translate_save=self._on_translate_save,
            on_save_clipboard=self._on_save_clipboard,
            t=t,
        )
        # Start hidden; shown when mode is short session
        self._short_form.grid(row=0, column=0, sticky="nsew")
        self._short_form.grid_remove()

        # Speaker profile cards row (hidden until a session completes)
        self._speaker_cards_frame = ctk.CTkScrollableFrame(
            self._main_view, height=110, fg_color="transparent",
            orientation="horizontal")
        self._speaker_cards_frame.grid(row=1, column=0, sticky="ew",
                                       padx=4, pady=(4, 0))
        self._speaker_cards_frame.grid_remove()

        # Apply initial mode layout
        self._apply_mode_layout()

    def _build_playback_bar(self, parent) -> None:
        t = self._lang.t
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", padx=4, pady=4)

        self._btn_play = ctk.CTkButton(
            bar, text=t("btn_play"), width=60, command=self._toggle_playback)
        self._btn_play.pack(side="left", padx=4)

        self._seek_slider = ctk.CTkSlider(
            bar, from_=0, to=100, command=self._on_seek)
        self._seek_slider.pack(side="left", fill="x", expand=True, padx=8)
        self._seek_slider.set(0)

        self._vlc_player = None
        self._vlc_instance = None
        self._playback_path: str | None = None

    # ------------------------------------------------------------------
    # Panels
    # ------------------------------------------------------------------

    def _build_panels(self) -> None:
        t = self._lang.t
        avail_devices = self._devices
        avail_langs = self._lang.available

        panels_config = {
            "settings": lambda: SettingsPanel(
                self._content, self._config, t,
                on_language_change=self._on_language_change,
                available_languages=avail_langs,
                available_devices=avail_devices,
            ),
            "profiles": lambda: VoiceProfilesPanel(
                self._content, self._config, t,
                on_groups_changed=self._refresh_group_menu),
            "dictionary": lambda: SubstitutionDictPanel(
                self._content, self._config, t),
            "batch": lambda: BatchQueuePanel(
                self._content, self._config, t,
                pipeline_runner=self._pipeline),
            "output": lambda: OutputConfigPanel(
                self._content, self._config, t),
            "hotkeys": lambda: HotkeysPanel(
                self._content, self._config, t,
                on_bindings_changed=self._hotkeys.update_bindings),
            "labelling": lambda: SpeakerLabellingPanel(
                self._content, self._config, t,
                on_label_confirmed=self._on_label_confirmed,
                on_all_done=self._finish_labelling),
            "history": lambda: SessionHistoryPanel(
                self._content, self._config, t),
            "backup": lambda: BackupRestorePanel(
                self._content, self._config, t),
            "about": lambda: AboutPanel(
                self._content, self._config, t),
        }
        for panel_id, factory in panels_config.items():
            panel = factory()
            panel.grid(row=0, column=0, sticky="nsew")
            panel.grid_remove()
            self._panels[panel_id] = panel

    def _show_panel(self, panel_id: str) -> None:
        """Show a side panel, hiding the main view."""
        if panel_id == "home":
            self._show_main_view()
            return

        # Hide previous
        if self._active_panel is not None:
            self._panels[self._active_panel].on_hide()
            self._panels[self._active_panel].grid_remove()
        else:
            self._main_view.grid_remove()

        panel = self._panels[panel_id]
        panel.grid()
        panel.on_show()
        self._active_panel = panel_id

        # Highlight active nav button
        for pid, btn in self._nav_buttons.items():
            if pid == panel_id:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")

    def _show_main_view(self) -> None:
        if self._active_panel is not None:
            self._panels[self._active_panel].on_hide()
            self._panels[self._active_panel].grid_remove()
            self._active_panel = None
        for pid, btn in self._nav_buttons.items():
            btn.configure(fg_color=("gray75", "gray25") if pid == "home" else "transparent")
        self._main_view.grid(row=0, column=0, sticky="nsew")
        self._apply_mode_layout()

    # ------------------------------------------------------------------
    # Mode toggle (T-78, T-83)
    # ------------------------------------------------------------------

    def _apply_mode_layout(self) -> None:
        if self._mode == "short":
            self._output_text.grid_remove()
            self._short_form.grid()
        else:
            self._short_form.grid_remove()
            self._output_text.grid()

    def _on_mode_change(self, value: str) -> None:
        t = self._lang.t
        self._mode = "regular" if value == t("mode_regular") else "short"
        self._config.set("recording_mode", self._mode)
        self._apply_mode_layout()

    # ------------------------------------------------------------------
    # Recording (T-84, T-85)
    # ------------------------------------------------------------------

    def _start_recording(self) -> None:
        if self._recording:
            return
        if self._mode == "short":
            self._short_form.clear_fields()  # T-129
        self._set_recording(True)
        self._start_capture()

    def _stop_recording(self) -> None:
        if not self._recording:
            return
        self._set_recording(False)
        self._stop_capture()

    def _set_recording(self, recording: bool) -> None:
        self._recording = recording
        self._rec_dot.set_recording(recording)
        t = self._lang.t
        if recording:
            self._status_label.configure(text=t("status_recording"))
            self._btn_record.configure(
                text=t("btn_stop"), state="normal", command=self._stop_recording)
            self._btn_play.configure(state="disabled")
        else:
            self._status_label.configure(text=t("status_processing"))
            self._btn_record.configure(state="disabled")
        if self._tray:
            self._tray.set_recording(recording)

    def _start_capture(self) -> None:
        import numpy as np
        self._capture_buffer: list = []
        self._capture_stop.clear()
        self._capture_sr = 16000

        def capture_thread():
            try:
                import pyaudio
                pa = pyaudio.PyAudio()
                device_name = self._config.get("input_device", "") or ""
                device_index = self._find_device_index(pa, device_name)
                chunk = 1024
                stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self._capture_sr,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=chunk,
                )
                while not self._capture_stop.is_set():
                    data = stream.read(chunk, exception_on_overflow=False)
                    arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    self._capture_buffer.extend(arr.tolist())
                    rms = float(np.sqrt(np.mean(arr ** 2))) / 32768.0
                    self.after(0, lambda r=rms: self._signal_meter.set_level(r))
                stream.stop_stream()
                stream.close()
                pa.terminate()
            except Exception:
                pass

        self._capture_thread = threading.Thread(
            target=capture_thread, daemon=True)
        self._capture_thread.start()

    def _stop_capture(self) -> None:
        self._capture_stop.set()
        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
        self._signal_meter.reset()

        import numpy as np
        if hasattr(self, "_capture_buffer") and self._capture_buffer:
            audio = np.array(self._capture_buffer, dtype=np.float32) / 32768.0
        else:
            audio = np.zeros(1600, dtype=np.float32)

        if self._mode == "short":
            self._pipeline.start_short_session(
                audio, self._capture_sr,
                speaker_group=self._group_var.get())
        else:
            self._pipeline.start_microphone(
                audio, self._capture_sr,
                output_dir=Path(self._config.get("output_folder") or "."),
                speaker_group=self._group_var.get(),
            )

    @staticmethod
    def _find_device_index(pa, name: str) -> int | None:
        if not name or name in ("—", "Default"):
            return None
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if name.lower() in info["name"].lower():
                return i
        return None

    # ------------------------------------------------------------------
    # Pipeline callbacks (called from background thread — use after())
    # ------------------------------------------------------------------

    def _on_pipeline_progress(self, progress: float, status: str) -> None:
        self.after(0, lambda p=progress, s=status:
                   self._update_progress(p, s))

    def _on_pipeline_done(self, result) -> None:
        self.after(0, lambda r=result: self._handle_done(r))

    def _on_pipeline_error(self, error: str) -> None:
        self.after(0, lambda e=error: self._handle_error(e))

    def _update_progress(self, progress: float, status: str) -> None:
        self._file_progress.set(progress)
        if status:
            self._status_label.configure(text=status)

    def _handle_done(self, result) -> None:
        if result.ok and result.write_output_fn is not None:
            # Unidentified speakers present — show labelling panel before writing
            self._status_label.configure(
                text=self._lang.t("status_labelling"))
            self._start_labelling(result)
            return

        t = self._lang.t
        self._file_progress.set(0)
        self._status_label.configure(text=t("status_done"))
        self._btn_record.configure(
            text=t("btn_start"), state="normal", command=self._start_recording)
        self._btn_play.configure(state="normal")

        if result.ok and result.segments:
            if self._mode == "short":
                # Populate both fields (T-127 / spec step 10)
                raw_text = " ".join(
                    s.text for s in result.segments if not s.bad_audio)
                trans_text = " ".join(
                    (s.translated_text or s.text)
                    for s in result.segments if not s.bad_audio)
                self._short_form.set_transcription(raw_text)
                if self._config.get("translation_enabled", False):
                    self._short_form.set_translation(trans_text)
                # Show the main view if minimised
                if self._minimized_to_tray:
                    self._restore_from_tray()
            else:
                # Append to output text
                self._output_text.configure(state="normal")
                self._output_text.delete("1.0", "end")
                for seg in result.segments:
                    self._output_text.insert(
                        "end",
                        f"[{seg.start:.1f}s] {seg.speaker_id}: {seg.text}\n")
                self._output_text.configure(state="disabled")
                if result.output_paths:
                    self._playback_path = result.source_path

        if result.ok and result.segments:
            self._update_speaker_cards(result.segments)

        # Navigate home so the user sees the output
        self._show_main_view()

        # Completion sound + tray notify
        self._sound.play()
        if self._tray and self._config.get("tray_notifications", True):
            self._tray.notify(t("tray_notify_done"))

    def _handle_error(self, error: str) -> None:
        t = self._lang.t
        self._status_label.configure(text=t("error_title"))
        self._btn_record.configure(
            text=t("btn_start"), state="normal", command=self._start_recording)
        self._show_error_dialog(error)

    # ------------------------------------------------------------------
    # Post-session speaker labelling (Spec 4.3)
    # ------------------------------------------------------------------

    def _start_labelling(self, result) -> None:
        """Navigate to the Speaker Labelling panel for unidentified speakers."""
        import re, os
        self._pending_result = result
        self._pending_fragment_paths = {}

        # Collect unique Speaker N IDs, pick the best (longest non-bad) segment
        best: dict[str, object] = {}
        for seg in result.segments:
            if not re.match(r'^Speaker \d+$', seg.speaker_id):
                continue
            sid = seg.speaker_id
            dur = seg.end - seg.start
            prev = best.get(sid)
            if prev is None or (not seg.bad_audio and (prev.bad_audio or dur > prev.end - prev.start)):
                best[sid] = seg

        if not best:
            self._finish_labelling()
            return

        sorted_ids = sorted(best, key=lambda s: int(re.search(r'\d+', s).group()))
        pending = []
        for sid in sorted_ids:
            seg = best[sid]
            fpath = None
            if result.audio is not None:
                try:
                    fpath = _save_fragment_wav(
                        result.audio, result.sample_rate, seg.start, seg.end)
                    self._pending_fragment_paths[sid] = fpath
                except Exception:
                    pass
            pending.append({"speaker_id": sid, "fragment_path": fpath})

        panel = self._panels.get("labelling")
        if panel and hasattr(panel, "load_pending"):
            panel.load_pending(pending)
            self._show_panel("labelling")
        else:
            self._finish_labelling()

    def _on_label_confirmed(self, speaker_id: str, display_name: str,
                            meta: dict) -> None:
        """Relabel all segments and create a voice profile for the confirmed speaker."""
        if self._pending_result is None:
            return
        for seg in self._pending_result.segments:
            if seg.speaker_id == speaker_id:
                seg.speaker_id = display_name
        if any(v.strip() for v in meta.values()):
            fpath = self._pending_fragment_paths.get(speaker_id)
            try:
                from library.storage import LibraryStorage
                from library.profile_creator import ProfileCreator, ConflictMode
                library_root = Path(self._config.get("library_root", "library"))
                storage = LibraryStorage(library_root)
                if fpath:
                    from audio.ingest import load as _audio_load
                    audio, sr = _audio_load(fpath)
                    ProfileCreator(storage).create(
                        audio, sr,
                        last=meta.get("lastname", ""),
                        first=meta.get("firstname", ""),
                        middle=meta.get("middlename", ""),
                        nickname=meta.get("nickname", ""),
                        organisation=meta.get("organisation", ""),
                        position=meta.get("position", ""),
                        note=meta.get("note", ""),
                        conflict_mode=ConflictMode.MERGE,
                    )
                else:
                    storage.create_profile(
                        last=meta.get("lastname", ""),
                        first=meta.get("firstname", ""),
                        middle=meta.get("middlename", ""),
                        nickname=meta.get("nickname", ""),
                        organisation=meta.get("organisation", ""),
                        position=meta.get("position", ""),
                        note=meta.get("note", ""),
                    )
            except Exception:
                pass

    def _finish_labelling(self) -> None:
        """Called when all pending speakers are confirmed or skipped."""
        result = self._pending_result
        self._pending_result = None
        for path in self._pending_fragment_paths.values():
            try:
                import os
                os.unlink(path)
            except Exception:
                pass
        self._pending_fragment_paths = {}

        if result is None:
            return

        if result.write_output_fn:
            import threading
            def _bg():
                try:
                    written = result.write_output_fn()
                    result.output_paths = written
                    self.after(0, lambda: self._after_labelling_write(result))
                except Exception as exc:
                    self.after(0, lambda e=str(exc): self._handle_error(e))
            threading.Thread(target=_bg, daemon=True).start()
        else:
            self._after_labelling_write(result)

    def _after_labelling_write(self, result) -> None:
        """Finish UI reset and display output after deferred write completes."""
        t = self._lang.t
        self._file_progress.set(0)
        self._status_label.configure(text=t("status_done"))
        self._btn_record.configure(
            text=t("btn_start"), state="normal", command=self._start_recording)
        self._btn_play.configure(state="normal")
        self._show_main_view()

        if result.ok and result.segments:
            if self._mode == "short":
                raw_text = " ".join(
                    s.text for s in result.segments if not s.bad_audio)
                self._short_form.set_transcription(raw_text)
            else:
                self._output_text.configure(state="normal")
                self._output_text.delete("1.0", "end")
                for seg in result.segments:
                    self._output_text.insert(
                        "end",
                        f"[{seg.start:.1f}s] {seg.speaker_id}: {seg.text}\n")
                self._output_text.configure(state="disabled")
                if result.output_paths:
                    self._playback_path = result.source_path

        if result.ok and result.segments:
            self._update_speaker_cards(result.segments)

        self._sound.play()
        if self._tray and self._config.get("tray_notifications", True):
            self._tray.notify(t("tray_notify_done"))

    def _update_speaker_cards(self, segments) -> None:
        """Rebuild the speaker profile cards row from session segments."""
        frame = self._speaker_cards_frame
        for w in frame.winfo_children():
            w.destroy()

        # Collect unique named speakers (exclude generic "Speaker N")
        import re
        from pathlib import Path
        seen: list[str] = []
        for seg in segments:
            sid = seg.speaker_id
            if sid and sid not in seen and not re.match(r'^Speaker \d+$', sid):
                seen.append(sid)

        if not seen:
            frame.grid_remove()
            return

        # Look up each speaker in the library
        library_root = Path(self._config.get("library_root", "library"))
        profiles: dict[str, object] = {}
        if library_root.exists():
            try:
                from library.storage import LibraryStorage
                storage = LibraryStorage(library_root)
                for folder in library_root.iterdir():
                    if not (folder / "speaker.json").exists():
                        continue
                    meta = storage.read_meta(folder.name)
                    full = f"{meta.last_name} {meta.first_name}".strip()
                    nick = meta.nickname or ""
                    for sid in seen:
                        if sid in (full, nick, folder.name):
                            profiles[sid] = meta
            except Exception:
                pass

        # Build one card per speaker
        for sid in seen:
            meta = profiles.get(sid)
            card = ctk.CTkFrame(frame, corner_radius=8,
                                border_width=1, border_color=("gray70", "gray30"))
            card.pack(side="left", padx=6, pady=4, ipadx=8, ipady=6)

            name_text = sid
            if meta and (meta.last_name or meta.first_name):
                parts = [p for p in (meta.last_name, meta.first_name,
                                     meta.middle_name) if p]
                name_text = " ".join(parts)
            ctk.CTkLabel(card, text=name_text,
                         font=ctk.CTkFont(weight="bold"),
                         anchor="w").pack(anchor="w")

            if meta:
                for val in (meta.organisation, meta.position, meta.note):
                    if val:
                        ctk.CTkLabel(card, text=val,
                                     text_color=("gray40", "gray70"),
                                     font=ctk.CTkFont(size=11),
                                     anchor="w").pack(anchor="w")

        frame.grid()

    def _show_error_dialog(self, error: str) -> None:
        t = self._lang.t
        dialog = ctk.CTkToplevel(self)
        dialog.title(t("error_title"))
        dialog.geometry("640x220")
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()

        txt = ctk.CTkTextbox(dialog, wrap="word")
        txt.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        txt.insert("end", error)
        txt.configure(state="disabled")
        bind_context_menu(txt, readonly=True, t=t)

        ctk.CTkButton(dialog, text=t("btn_close"), command=dialog.destroy).pack(pady=(4, 12))
        dialog.after(100, dialog.focus_force)

    # ------------------------------------------------------------------
    # Short Session form button callbacks (T-130, T-131)
    # ------------------------------------------------------------------

    def _on_translate_save(self, text: str) -> None:
        if self._config.get("translation_enabled", False):
            try:
                from translation.engine import TranslationEngine
                translator = TranslationEngine(self._config)
                # Build a fake segment for translation
                from transcription.engine import TranscribedSegment
                seg = TranscribedSegment(
                    speaker_id="Unknown", start=0, end=0,
                    text=text, language="auto", language_code="auto",
                    confidence=1.0, no_speech_prob=0.0,
                )
                result = translator.translate([seg])
                translated = result[0].translated_text or text
                self._short_form.set_translation(translated)
                self._copy_to_clipboard(translated)
            except Exception:
                self._copy_to_clipboard(text)
        else:
            self._copy_to_clipboard(text)
        self._update_session_clipboard(text)

    def _on_save_clipboard(self, text: str) -> None:
        self._copy_to_clipboard(text)
        self._update_session_clipboard(text)

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.OpenClipboard(0)
                ctypes.windll.user32.EmptyClipboard()
                h = ctypes.windll.kernel32.GlobalAlloc(0x42, len(text.encode()) + 2)
                p = ctypes.windll.kernel32.GlobalLock(h)
                ctypes.memmove(p, text.encode("utf-8") + b"\x00", len(text.encode()) + 1)
                ctypes.windll.kernel32.GlobalUnlock(h)
                ctypes.windll.user32.SetClipboardData(13, h)
                ctypes.windll.user32.CloseClipboard()
            except Exception:
                pass

    def _update_session_clipboard(self, text: str) -> None:
        pass  # Session history update: T-132 (no active session ID tracked here)

    # ------------------------------------------------------------------
    # Playback (T-87)
    # ------------------------------------------------------------------

    def _toggle_playback(self) -> None:
        if self._recording:
            return
        if self._vlc_player and self._vlc_player.is_playing():
            self._vlc_player.pause()
            self._btn_play.configure(text=self._lang.t("btn_play"))
        else:
            self._start_playback()

    def _start_playback(self) -> None:
        if not self._playback_path:
            return
        try:
            import vlc
            if self._vlc_instance is None:
                self._vlc_instance = vlc.Instance()
            if self._vlc_player is None:
                self._vlc_player = self._vlc_instance.media_player_new()
            media = self._vlc_instance.media_new(self._playback_path)
            self._vlc_player.set_media(media)
            self._vlc_player.play()
            self._btn_play.configure(text=self._lang.t("btn_pause"))
            self._poll_playback()
        except Exception:
            pass

    def _on_seek(self, value: float) -> None:
        if self._vlc_player:
            try:
                self._vlc_player.set_position(value / 100.0)
            except Exception:
                pass

    def _poll_playback(self) -> None:
        if self._vlc_player and self._vlc_player.is_playing():
            try:
                pos = self._vlc_player.get_position() * 100
                self._seek_slider.set(pos)
            except Exception:
                pass
            self.after(500, self._poll_playback)
        else:
            self._btn_play.configure(text=self._lang.t("btn_play"))

    # ------------------------------------------------------------------
    # Signal meter polling
    # ------------------------------------------------------------------

    def _poll_signal_level(self) -> None:
        # When not recording, keep meter at 0
        if not self._recording:
            self._signal_meter.reset()
        self._meter_after = self.after(100, self._poll_signal_level)

    # ------------------------------------------------------------------
    # Progress bar helpers
    # ------------------------------------------------------------------

    def _hide_queue_progress(self) -> None:
        self._queue_progress.pack_forget()
        self._queue_label.pack_forget()

    def _show_queue_progress(self, current: int, total: int) -> None:
        self._queue_label.configure(
            text=self._lang.t("progress_queue",
                               current=current, total=total))
        self._queue_label.pack(side="left", padx=4)
        self._queue_progress.pack(side="left", padx=4)

    # ------------------------------------------------------------------
    # Language change (T-77)
    # ------------------------------------------------------------------

    def _on_language_change(self, lang_code: str) -> None:
        self._lang.load(lang_code)
        self._config.set("ui_language", lang_code)
        t = self._lang.t
        self.title(t("app_title"))

        # Preserve batch queue file list across rebuild
        batch_files: list[str] = []
        if "batch" in self._panels and hasattr(self._panels["batch"], "_files"):
            batch_files = list(self._panels["batch"]._files)

        # Remember which panel was open
        active_panel = self._active_panel

        # Destroy all panels and recreate them with the new language
        for panel in self._panels.values():
            panel.destroy()
        self._panels.clear()
        self._active_panel = None
        self._build_panels()

        # Restore batch queue
        if batch_files and "batch" in self._panels:
            bp = self._panels["batch"]
            if hasattr(bp, "_files") and hasattr(bp, "_refresh"):
                bp._files = batch_files
                bp._refresh()

        # Restore the view that was open before the rebuild
        if active_panel:
            self._show_panel(active_panel)
        else:
            self._show_main_view()

        self._update_all_strings(t)

    def _update_all_strings(self, t: Callable) -> None:
        # Nav buttons
        for lang_key, panel_id in _NAV_ITEMS:
            self._nav_buttons[panel_id].configure(text=t(lang_key))
        # Control bar labels
        self._lbl_group.configure(text=t("label_group"))
        self._lbl_mode.configure(text=t("label_mode"))
        # Control bar interactive widgets
        self._mode_toggle.configure(values=[t("mode_regular"), t("mode_short")])
        self._mode_var.set(
            t("mode_regular") if self._mode == "regular" else t("mode_short"))
        if self._recording:
            self._btn_record.configure(text=t("btn_stop"))
        else:
            self._btn_record.configure(text=t("btn_start"))
        if not (self._vlc_player and self._vlc_player.is_playing()):
            self._btn_play.configure(text=t("btn_play"))
        # Short session form (lives in main view, not in panels dict)
        self._short_form.update_strings(t)
        # Status bar — only overwrite if idle
        if not self._recording and not self._pipeline.running:
            self._status_label.configure(text=t("status_idle"))

    # ------------------------------------------------------------------
    # Device / group helpers
    # ------------------------------------------------------------------

    def _get_device_names(self) -> list[str]:
        try:
            from audio.device import list_devices
            return ["Default"] + [d.name for d in list_devices()]
        except Exception:
            return ["Default"]

    def _get_group_names(self) -> list[str]:
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            names = list(LibraryGroups(LibraryStorage(library_root)).list_groups())
        except Exception:
            names = []
        for name in self._config.get("known_groups", []):
            if name not in names:
                names.append(name)
        return names

    def _refresh_group_menu(self, names: list[str] | None = None) -> None:
        if names is None:
            names = self._get_group_names()
        values = names if names else ["—"]
        self._group_menu.configure(values=values)
        if self._group_var.get() not in values:
            self._group_var.set(values[0])
            self._config.set("active_speaker_group", values[0])

    def _on_group_change(self, value: str) -> None:
        self._config.set("active_speaker_group", value)

    # ------------------------------------------------------------------
    # Hotkeys (T-86)
    # ------------------------------------------------------------------

    def _register_hotkeys(self) -> None:
        self._hotkeys.register("start_recording",
                                lambda: self.after(0, self._start_recording))
        self._hotkeys.register("stop_recording",
                                lambda: self.after(0, self._stop_recording))

    # ------------------------------------------------------------------
    # Tray (T-108 to T-112)
    # ------------------------------------------------------------------

    def _init_tray(self) -> None:
        from gui.tray import TrayIcon
        self._tray = TrayIcon(
            app_title=self._lang.t("app_title"),
            on_open=lambda: self.after(0, self._restore_from_tray),
            on_start_recording=lambda: self.after(0, self._start_recording),
            on_stop_recording=lambda: self.after(0, self._stop_recording),
            on_exit=lambda: self.after(0, self._on_exit_from_tray),
            t=self._lang.t,
        )
        self._tray.set_mode(
            self._lang.t("mode_regular") if self._mode == "regular"
            else self._lang.t("mode_short"))
        self._tray.start()

    def _minimize_to_tray(self) -> None:
        if self._tray is None:
            self._init_tray()
        self._minimized_to_tray = True
        self.withdraw()

    def _restore_from_tray(self) -> None:
        self._minimized_to_tray = False
        self.deiconify()
        self.lift()
        self.focus_force()

    def _on_exit_from_tray(self) -> None:
        if self._recording or self._pipeline.running:
            from tkinter import messagebox
            if not messagebox.askyesno(
                    self._lang.t("tray_exit_confirm_title"),
                    self._lang.t("tray_exit_confirm_msg"),
                    parent=self):
                return
        self._shutdown()

    def _on_close(self) -> None:
        if self._config.get("minimize_to_tray", False):
            self._minimize_to_tray()
        else:
            self._shutdown()

    def _shutdown(self) -> None:
        self._hotkeys.shutdown()
        if self._tray:
            self._tray.stop()
        if self._meter_after:
            try:
                self.after_cancel(self._meter_after)
            except Exception:
                pass
        self.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(config: ConfigStore | None = None) -> None:
    """Launch the GUI application."""
    if config is None:
        import os
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        config_path = Path(local_app_data) / "SpeechRecognition" / "config.json"
        config = ConfigStore(config_path)

    app = App(config=config)

    if config.get("auto_start", False) and config.get("minimize_to_tray", False):
        app.after(100, app._minimize_to_tray)

    app.mainloop()


if __name__ == "__main__":
    import sys, os
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    run()
