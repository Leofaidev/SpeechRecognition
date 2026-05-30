"""Create/Edit voice profile dialog (T-93, T-94, T-95, T-96)."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from gui.widgets.context_menu import bind_context_menu


class ProfileDialog(ctk.CTkToplevel):
    """Create or edit a voice profile.

    If *folder_name* is given, the dialog loads existing metadata for editing
    and shows the sample management section (play / add / remove).
    Otherwise a new profile is created from a selected audio file.
    """

    def __init__(self, parent, config, t: Callable,
                 folder_name: str | None = None,
                 on_done: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._t = t
        self._folder_name = folder_name
        self._on_done = on_done or (lambda: None)
        self._player = None
        self._active_play_btn = None
        title_key = "dialog_edit_profile" if folder_name else "dialog_create_profile"
        self.title(t(title_key))
        self.geometry("520x740" if folder_name else "520x600")
        self.grab_set()
        self._build()
        self._load_existing()
        self.focus_force()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)
        row = 0

        # Audio file + marker (create mode only)
        if not self._folder_name:
            ctk.CTkLabel(self, text=t("profile_audio_label")).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            self._audio_var = ctk.StringVar()
            _e = ctk.CTkEntry(self, textvariable=self._audio_var)
            _e.grid(row=row, column=1, sticky="ew", padx=4, pady=4)
            bind_context_menu(_e)
            ctk.CTkButton(self, text=t("btn_browse"), width=80,
                          command=self._browse_audio).grid(
                row=row, column=2, padx=4, pady=4)
            row += 1

            ctk.CTkLabel(self, text=t("profile_marker_label")).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            self._marker_var = ctk.StringVar(value="0")
            _e2 = ctk.CTkEntry(self, textvariable=self._marker_var, width=80)
            _e2.grid(row=row, column=1, sticky="w", padx=4, pady=4)
            bind_context_menu(_e2)
            ctk.CTkButton(self, text=t("profile_preview_btn"), width=120,
                          command=self._preview).grid(
                row=row, column=2, padx=4, pady=4)
            row += 1

        # Samples section (edit mode only)
        if self._folder_name:
            ctk.CTkLabel(self, text=t("profile_samples_section"),
                         font=ctk.CTkFont(weight="bold")).grid(
                row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 2))
            row += 1

            self._samples_frame = ctk.CTkScrollableFrame(self, height=130)
            self._samples_frame.grid(row=row, column=0, columnspan=3,
                                      sticky="ew", padx=12, pady=(0, 4))
            self._samples_frame.grid_columnconfigure(0, weight=1)
            row += 1

            add_row = ctk.CTkFrame(self, fg_color="transparent")
            add_row.grid(row=row, column=0, columnspan=3, sticky="w",
                         padx=12, pady=(0, 6))
            ctk.CTkButton(add_row, text=t("btn_add_sample"), width=120,
                          command=self._add_sample).pack(side="left")
            self._retrain_status = ctk.CTkLabel(add_row, text="",
                                                 text_color="gray60")
            self._retrain_status.pack(side="left", padx=12)
            row += 1

        # Metadata fields
        self._name_vars: dict[str, ctk.StringVar] = {}
        for key, label_key in [
            ("lastname", "profile_lastname"),
            ("firstname", "profile_firstname"),
            ("middlename", "profile_middlename"),
            ("nickname", "profile_nickname"),
            ("organisation", "profile_organisation"),
            ("position", "profile_position"),
            ("note", "profile_note"),
        ]:
            ctk.CTkLabel(self, text=t(label_key)).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            var = ctk.StringVar()
            self._name_vars[key] = var
            _em = ctk.CTkEntry(self, textvariable=var)
            _em.grid(row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
            bind_context_menu(_em)
            row += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="e",
                       padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("btn_cancel"),
                      fg_color="#555555",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=t("btn_confirm"),
                      command=self._confirm).pack(side="left")

    # ------------------------------------------------------------------
    # Load existing data
    # ------------------------------------------------------------------

    def _load_existing(self) -> None:
        if not self._folder_name:
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            self._name_vars["lastname"].set(meta.last_name)
            self._name_vars["firstname"].set(meta.first_name)
            self._name_vars["middlename"].set(meta.middle_name)
            self._name_vars["nickname"].set(meta.nickname)
            self._name_vars["organisation"].set(meta.organisation)
            self._name_vars["position"].set(meta.position)
            self._name_vars["note"].set(meta.note)
        except Exception:
            pass
        self._build_samples_list()

    # ------------------------------------------------------------------
    # Samples list
    # ------------------------------------------------------------------

    def _build_samples_list(self) -> None:
        if not hasattr(self, "_samples_frame"):
            return
        for w in self._samples_frame.winfo_children():
            w.destroy()
        library_root = Path(self._config.get("library_root", "library"))
        samples: list[str] = []
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            samples = meta.samples or []
        except Exception:
            pass

        if not samples:
            ctk.CTkLabel(self._samples_frame,
                         text=self._t("profile_no_samples"),
                         text_color="gray60").pack(padx=8, pady=6)
            return

        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        storage = LibraryStorage(library_root)
        for sample_name in samples:
            sample_path = storage.sample_path(self._folder_name, sample_name)
            row = ctk.CTkFrame(self._samples_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(row, text=sample_name).pack(side="left", padx=6)
            play_btn = ctk.CTkButton(row, text=self._t("btn_play"), width=60)
            play_btn.configure(
                command=lambda p=str(sample_path), b=play_btn:
                    self._toggle_sample_playback(p, b))
            play_btn.pack(side="right", padx=2)
            ctk.CTkButton(row, text=self._t("btn_remove_sample"), width=70,
                          fg_color="#8B1A1A", hover_color="#6B1010",
                          command=lambda sn=sample_name: self._remove_sample(sn)
                          ).pack(side="right", padx=2)

    def _toggle_sample_playback(self, path: str, btn) -> None:
        prev_btn = self._active_play_btn
        self._stop_sample_playback()
        if prev_btn is btn:
            return
        try:
            import vlc
            self._player = vlc.MediaPlayer(path)
            em = self._player.event_manager()
            em.event_attach(vlc.EventType.MediaPlayerEndReached,
                            lambda e: self.after(0, self._on_sample_playback_ended))
            em.event_attach(vlc.EventType.MediaPlayerEncounteredError,
                            lambda e: self.after(0, self._on_sample_playback_ended))
            self._player.play()
            self._active_play_btn = btn
            btn.configure(text=self._t("btn_stop"))
        except Exception:
            self._player = None
            self._active_play_btn = None

    def _stop_sample_playback(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player = None
        if self._active_play_btn is not None:
            try:
                self._active_play_btn.configure(text=self._t("btn_play"))
            except Exception:
                pass
            self._active_play_btn = None

    def _on_sample_playback_ended(self) -> None:
        self._player = None
        if self._active_play_btn is not None:
            try:
                self._active_play_btn.configure(text=self._t("btn_play"))
            except Exception:
                pass
            self._active_play_btn = None

    def _remove_sample(self, sample_name: str) -> None:
        from tkinter import messagebox
        if not messagebox.askyesno(
                self._t("delete_confirm_title"),
                f"{sample_name}"):
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            sample_path = storage.sample_path(self._folder_name, sample_name)
            if sample_path.exists():
                sample_path.unlink()
            meta.samples = [s for s in meta.samples if s != sample_name]
            meta.sample_count = len(meta.samples)
            storage.write_meta(self._folder_name, meta)
            self._set_retrain_status(self._t("profile_retraining"))
            def _bg():
                try:
                    self._retrain_profile()
                    self.after(0, lambda: self._set_retrain_status(
                        self._t("profile_retrain_single_done")))
                except Exception as exc:
                    self.after(0, lambda e=str(exc): self._set_retrain_status(
                        f"{self._t('error_title')}: {e}"))
                finally:
                    self.after(0, self._build_samples_list)
            threading.Thread(target=_bg, daemon=True).start()
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    def _add_sample(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.mp4 *.avi")])
        if not path:
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            import wave
            import numpy as np
            from audio.ingest import load
            from library.storage import LibraryStorage
            audio, sr = load(path)
            storage = LibraryStorage(library_root)
            sample_name = storage.next_sample_name(self._folder_name)
            sample_path = storage.sample_path(self._folder_name, sample_name)
            pcm = (audio * 32767).clip(-32768, 32767).astype(np.int16)
            with wave.open(str(sample_path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(pcm.tobytes())
            meta = storage.read_meta(self._folder_name)
            meta.samples.append(sample_name)
            meta.sample_count = len(meta.samples)
            storage.write_meta(self._folder_name, meta)
            self._set_retrain_status(self._t("profile_retraining"))
            def _bg():
                try:
                    self._retrain_profile()
                    self.after(0, lambda: self._set_retrain_status(
                        self._t("profile_retrain_single_done")))
                except Exception as exc:
                    self.after(0, lambda e=str(exc): self._set_retrain_status(
                        f"{self._t('error_title')}: {e}"))
                finally:
                    self.after(0, self._build_samples_list)
            threading.Thread(target=_bg, daemon=True).start()
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    def _retrain_profile(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.retrainer import LibraryRetrainer
        from library.profile_creator import _pyannote_embed
        storage = LibraryStorage(library_root)
        meta = storage.read_meta(self._folder_name)
        if not meta.samples:
            return
        LibraryRetrainer(storage, _pyannote_embed)._retrain_one(self._folder_name)

    def _set_retrain_status(self, msg: str) -> None:
        if hasattr(self, "_retrain_status"):
            self._retrain_status.configure(text=msg)

    # ------------------------------------------------------------------
    # Create mode helpers
    # ------------------------------------------------------------------

    def _browse_audio(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("Audio", "*.mp3 *.wav *.mp4 *.avi")])
        if path:
            self._audio_var.set(path)

    def _preview(self) -> None:
        audio_path = self._audio_var.get()
        if not audio_path:
            return
        try:
            marker = float(self._marker_var.get() or "0")
        except ValueError:
            marker = 0.0
        try:
            import vlc
            player = vlc.MediaPlayer(audio_path)
            player.play()
            player.set_time(int(marker * 1000))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Confirm (save metadata / create profile)
    # ------------------------------------------------------------------

    def _confirm(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        kwargs = {
            "last": self._name_vars["lastname"].get(),
            "first": self._name_vars["firstname"].get(),
            "middle": self._name_vars["middlename"].get(),
            "nickname": self._name_vars["nickname"].get(),
            "organisation": self._name_vars["organisation"].get(),
            "position": self._name_vars["position"].get(),
            "note": self._name_vars["note"].get(),
        }
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            if self._folder_name:
                meta = storage.read_meta(self._folder_name)
                meta.last_name = kwargs["last"]
                meta.first_name = kwargs["first"]
                meta.middle_name = kwargs["middle"]
                meta.nickname = kwargs["nickname"]
                meta.organisation = kwargs["organisation"]
                meta.position = kwargs["position"]
                meta.note = kwargs["note"]
                storage.write_meta(self._folder_name, meta)
            else:
                from audio.ingest import load
                from library.profile_creator import ProfileCreator, _pyannote_embed
                _hf_token = self._config.get("huggingface_token", None)
                _embed_fn = (lambda a, sr, _t=_hf_token: _pyannote_embed(a, sr, token=_t))
                audio, sr = load(self._audio_var.get())
                creator = ProfileCreator(storage, embedding_fn=_embed_fn)
                creator.create(audio, sr, **kwargs)
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))
            return
        self._on_done()
        self.destroy()
