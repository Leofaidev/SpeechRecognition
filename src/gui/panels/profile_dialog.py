"""Edit voice profile dialog (T-93, T-94, T-95, T-96)."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from gui.widgets.context_menu import bind_context_menu


class ProfileDialog(ctk.CTkToplevel):
    """Edit an existing voice profile (metadata + audio samples).

    *on_done* is called with *folder_name* on Confirm, or ``None`` on Cancel.
    """

    def __init__(self, parent, config, t: Callable,
                 folder_name: str,
                 on_done: Callable[[str | None], None] | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._t = t
        self._folder_name = folder_name
        self._on_done = on_done or (lambda fn: None)
        self._player = None
        self._active_play_btn = None
        self._pa_proc: subprocess.Popen | None = None
        self._pa_stop_flag: threading.Event | None = None
        self._initial_values: dict[str, str] = {}
        self.title(t("dialog_edit_profile"))
        self.geometry("520x740")
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._build()
        self._load_existing()
        self.update_idletasks()
        self.transient(parent.winfo_toplevel())
        self.lift()
        self.grab_set()
        self.focus_force()
        # XWayland/Wayland sometimes re-stacks windows after initial map
        self.after(150, lambda: self.lift() if self.winfo_exists() else None)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)
        row = 0

        # Samples section
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
        self._name_entries: dict[str, ctk.CTkEntry] = {}
        for key, label_key in [
            ("lastname",     "profile_lastname"),
            ("firstname",    "profile_firstname"),
            ("middlename",   "profile_middlename"),
            ("nickname",     "profile_nickname"),
            ("organisation", "profile_organisation"),
            ("position",     "profile_position"),
            ("note",         "profile_note"),
        ]:
            ctk.CTkLabel(self, text=t(label_key)).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            var = ctk.StringVar()
            self._name_vars[key] = var
            _em = ctk.CTkEntry(self, textvariable=var)
            _em.grid(row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
            self._name_entries[key] = _em
            bind_context_menu(_em)
            _em._entry.bind(
                "<Control-z>",
                lambda e, v=var, k=key: self._revert_field(v, k),
                add=True,
            )
            # Non-English layouts don't generate <Control-z> (keysym differs per
            # layout); '\x1a' is the Ctrl+Z control char and is layout-independent.
            _em._entry.bind(
                "<Control-KeyPress>",
                lambda e, v=var, k=key: (
                    self._revert_field(v, k) if e.char == "\x1a" else None
                ),
                add=True,
            )
            row += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=3, sticky="e",
                       padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("btn_cancel"),
                      fg_color="#555555",
                      command=self._cancel).pack(side="left", padx=8)
        self._confirm_btn = ctk.CTkButton(btn_frame, text=t("btn_confirm"),
                                          command=self._confirm)
        self._confirm_btn.pack(side="left")

        self._build_samples_list()

    # ------------------------------------------------------------------
    # Load existing metadata
    # ------------------------------------------------------------------

    def _revert_field(self, var: ctk.StringVar, key: str) -> str:
        """Ctrl+Z handler: revert this field to its value when the dialog opened."""
        var.set(self._initial_values.get(key, ""))
        return "break"

    def _load_existing(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            vals = {
                "lastname":     meta.last_name,
                "firstname":    meta.first_name,
                "middlename":   meta.middle_name,
                "nickname":     meta.nickname,
                "organisation": meta.organisation,
                "position":     meta.position,
                "note":         meta.note,
            }
            for k, v in vals.items():
                self._name_vars[k].set(v)
            self._initial_values = dict(vals)
        except Exception:
            pass

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
            if hasattr(self, "_confirm_btn"):
                self._confirm_btn.configure(state="disabled")
            return

        if hasattr(self, "_confirm_btn"):
            self._confirm_btn.configure(state="normal")

        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        storage = LibraryStorage(library_root)
        for sample_name in samples:
            sample_path = storage.sample_path(self._folder_name, sample_name)
            row_frame = ctk.CTkFrame(self._samples_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(row_frame, text=sample_name).pack(side="left", padx=6)

            play_btn = ctk.CTkButton(row_frame, text=self._t("btn_play"), width=60)
            play_btn.configure(
                command=lambda p=str(sample_path), b=play_btn:
                    self._toggle_sample_playback(p, b))
            play_btn.pack(side="right", padx=2)

            ctk.CTkButton(
                row_frame, text=self._t("btn_remove_sample"), width=70,
                fg_color="#8B1A1A", hover_color="#6B1010",
                command=lambda sn=sample_name: self._remove_sample(sn),
                state="disabled" if len(samples) <= 1 else "normal",
            ).pack(side="right", padx=2)

    def _remove_sample(self, sample_name: str) -> None:
        from tkinter import messagebox
        self.grab_release()
        confirmed = messagebox.askyesno(
            self._t("delete_confirm_title"), f"{sample_name}", parent=self)
        self.lift()
        self.grab_set()
        if not confirmed:
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
            self.grab_release()
            messagebox.showerror(self._t("error_title"), str(exc), parent=self)
            self.lift()
            self.grab_set()

    def _add_sample(self) -> None:
        from tkinter import filedialog
        self.grab_release()
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Audio", "*.mp3 *.wav *.mp4 *.avi")])
        self.lift()
        self.grab_set()
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
            self.grab_release()
            messagebox.showerror(self._t("error_title"), str(exc), parent=self)
            self.lift()
            self.grab_set()

    # ------------------------------------------------------------------
    # Sample playback (toggle Play / Stop)
    # ------------------------------------------------------------------

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
            # VLC not available — fall back to subprocess player (ffplay / aplay)
            self._start_subprocess_playback(path, btn)

    def _start_subprocess_playback(self, path: str, btn) -> None:
        """Play *path* via ffplay or aplay when python-vlc is unavailable."""
        self._active_play_btn = btn
        btn.configure(text=self._t("btn_stop"))
        stop_flag = threading.Event()
        self._pa_stop_flag = stop_flag

        def _thread() -> None:
            proc: subprocess.Popen | None = None
            try:
                for cmd in (
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                    ["aplay", "--quiet", path],
                ):
                    try:
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        self._pa_proc = proc
                        break
                    except FileNotFoundError:
                        continue
                if proc is None:
                    return
                while proc.poll() is None:
                    if stop_flag.is_set():
                        proc.terminate()
                        break
                    stop_flag.wait(0.05)
            except Exception:
                if proc is not None:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
            finally:
                if proc is not None:
                    try:
                        proc.wait(timeout=2)
                    except Exception:
                        pass
                self._pa_proc = None
                self.after(0, self._on_sample_playback_ended)

        threading.Thread(target=_thread, daemon=True).start()

    def _stop_sample_playback(self) -> None:
        if self._player is not None:
            self._player.stop()
            self._player = None
        if self._pa_stop_flag is not None:
            self._pa_stop_flag.set()
            self._pa_stop_flag = None
        if self._pa_proc is not None:
            try:
                self._pa_proc.terminate()
            except Exception:
                pass
            self._pa_proc = None
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

    # ------------------------------------------------------------------
    # Retrain helper
    # ------------------------------------------------------------------

    def _retrain_profile(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.retrainer import LibraryRetrainer
        from library.profile_creator import _pyannote_embed
        storage = LibraryStorage(library_root)
        meta = storage.read_meta(self._folder_name)
        if not meta.samples:
            return
        _tok = self._config.get("huggingface_token", None)
        _embed_fn = lambda a, sr, _t=_tok: _pyannote_embed(a, sr, token=_t)
        LibraryRetrainer(storage, _embed_fn)._retrain_one(self._folder_name)

    def _set_retrain_status(self, msg: str) -> None:
        if hasattr(self, "_retrain_status"):
            self._retrain_status.configure(text=msg)

    # ------------------------------------------------------------------
    # Cancel / Confirm
    # ------------------------------------------------------------------

    def _cancel(self) -> None:
        self._stop_sample_playback()
        self._on_done(None)
        self.grab_release()
        self.withdraw()
        self.destroy()

    def _confirm(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            meta.last_name    = self._name_vars["lastname"].get()
            meta.first_name   = self._name_vars["firstname"].get()
            meta.middle_name  = self._name_vars["middlename"].get()
            meta.nickname     = self._name_vars["nickname"].get()
            meta.organisation = self._name_vars["organisation"].get()
            meta.position     = self._name_vars["position"].get()
            meta.note         = self._name_vars["note"].get()
            storage.write_meta(self._folder_name, meta)
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))
            return
        self._stop_sample_playback()
        self._on_done(self._folder_name)
        self.grab_release()
        self.withdraw()
        self.destroy()
