"""Create/Edit voice profile dialog (T-93, T-94, T-95, T-96)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk


class ProfileDialog(ctk.CTkToplevel):
    """Create or edit a voice profile.

    If *folder_name* is given, the dialog loads existing metadata for editing.
    Otherwise a new profile is created.
    """

    def __init__(self, parent, config, t: Callable,
                 folder_name: str | None = None,
                 on_done: Callable[[], None] | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._t = t
        self._folder_name = folder_name
        self._on_done = on_done or (lambda: None)
        title_key = "dialog_edit_profile" if folder_name else "dialog_create_profile"
        self.title(t(title_key))
        self.geometry("520x600")
        self.grab_set()
        self._build()
        self._load_existing()
        self.focus_force()

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)
        row = 0

        # Audio file (only shown on create)
        if not self._folder_name:
            ctk.CTkLabel(self, text=t("profile_audio_label")).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            self._audio_var = ctk.StringVar()
            ctk.CTkEntry(self, textvariable=self._audio_var).grid(
                row=row, column=1, sticky="ew", padx=4, pady=4)
            ctk.CTkButton(self, text=t("btn_browse"), width=80,
                          command=self._browse_audio).grid(
                row=row, column=2, padx=4, pady=4)
            row += 1

            ctk.CTkLabel(self, text=t("profile_marker_label")).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            self._marker_var = ctk.StringVar(value="0")
            ctk.CTkEntry(self, textvariable=self._marker_var, width=80).grid(
                row=row, column=1, sticky="w", padx=4, pady=4)
            ctk.CTkButton(self, text=t("profile_preview_btn"), width=120,
                          command=self._preview).grid(
                row=row, column=2, padx=4, pady=4)
            row += 1

        # Metadata fields
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
            setattr(self, f"_var_{key}", var)
            ctk.CTkEntry(self, textvariable=var).grid(
                row=row, column=1, columnspan=2, sticky="ew", padx=4, pady=4)
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

    def _load_existing(self) -> None:
        if not self._folder_name:
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            meta = storage.read_meta(self._folder_name)
            self._var_lastname.set(meta.last_name)
            self._var_firstname.set(meta.first_name)
            self._var_middlename.set(meta.middle_name)
            self._var_nickname.set(meta.nickname)
            self._var_organisation.set(meta.organisation)
            self._var_position.set(meta.position)
            self._var_note.set(meta.note)
        except Exception:
            pass

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

    def _confirm(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        kwargs = {
            "last": self._var_lastname.get(),
            "first": self._var_firstname.get(),
            "middle": self._var_middlename.get(),
            "nickname": self._var_nickname.get(),
            "organisation": self._var_organisation.get(),
            "position": self._var_position.get(),
            "note": self._var_note.get(),
        }
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            if self._folder_name:
                # Edit: update metadata
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
                # Create
                from audio.ingest import load
                from library.profile_creator import ProfileCreator
                audio, sr = load(self._audio_var.get())
                creator = ProfileCreator(storage)
                creator.create(audio, sr, **kwargs)
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))
            return
        self._on_done()
        self.destroy()
