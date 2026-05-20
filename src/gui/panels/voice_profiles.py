"""Voice Profile Management panel (T-92 to T-100)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel


class VoiceProfilesPanel(BasePanel):
    """Two-column layout: speaker list on the left, group list on the right."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- Left: speaker list -------------------------------------
        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text=t("profiles_speakers_section"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=4)

        self._speaker_list = ctk.CTkScrollableFrame(left)
        self._speaker_list.grid(row=1, column=0, columnspan=2, sticky="nsew",
                                 padx=4, pady=4)

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
        ctk.CTkButton(btn_row, text=t("btn_add_profile"),
                      command=self._add_profile).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=t("btn_edit_profile"),
                      command=self._edit_profile).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=t("btn_delete_profile"),
                      command=self._delete_profile).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=t("btn_import_zip"),
                      command=self._import_profiles).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=t("btn_export_zip"),
                      command=self._export_profiles).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=t("btn_retrain_all"),
                      command=self._retrain_all).pack(side="right", padx=4)

        # ---- Right: group list --------------------------------------
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text=t("profiles_groups_section"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)

        self._group_list = ctk.CTkScrollableFrame(right)
        self._group_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        grp_btn_row = ctk.CTkFrame(right, fg_color="transparent")
        grp_btn_row.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        ctk.CTkButton(grp_btn_row, text=t("btn_add_group"),
                      command=self._add_group).pack(side="left", padx=2)
        ctk.CTkButton(grp_btn_row, text=t("btn_rename_group"),
                      command=self._rename_group).pack(side="left", padx=2)
        ctk.CTkButton(grp_btn_row, text=t("btn_delete_group"),
                      command=self._delete_group).pack(side="left", padx=2)

        self._selected_profile: str | None = None
        self.on_show()

    def on_show(self) -> None:
        self._refresh_speakers()
        self._refresh_groups()

    # ------------------------------------------------------------------
    # Speaker list
    # ------------------------------------------------------------------

    def _refresh_speakers(self) -> None:
        for w in self._speaker_list.winfo_children():
            w.destroy()
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
            profiles = storage.list_profiles()
        except Exception:
            profiles = []

        if not profiles:
            ctk.CTkLabel(self._speaker_list,
                         text=self._t("profiles_empty")).pack(padx=8, pady=8)
            return

        for profile_path in profiles:
            name = profile_path.name
            frame = ctk.CTkFrame(self._speaker_list, fg_color="transparent")
            frame.pack(fill="x", padx=4, pady=2)
            ctk.CTkLabel(frame, text=name).pack(side="left", padx=8)
            frame.bind("<Button-1>", lambda e, n=name: self._select_profile(n))

    def _select_profile(self, name: str) -> None:
        self._selected_profile = name

    # ------------------------------------------------------------------
    # Group list
    # ------------------------------------------------------------------

    def _refresh_groups(self) -> None:
        for w in self._group_list.winfo_children():
            w.destroy()
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            storage = LibraryStorage(library_root)
            groups = LibraryGroups(storage)
            group_names = groups.list_groups()
        except Exception:
            group_names = []

        if not group_names:
            ctk.CTkLabel(self._group_list,
                         text=self._t("groups_empty")).pack(padx=8, pady=8)
            return
        for g in group_names:
            ctk.CTkLabel(self._group_list, text=g).pack(
                fill="x", padx=8, pady=2, anchor="w")

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------

    def _add_profile(self) -> None:
        from gui.panels.profile_dialog import ProfileDialog
        ProfileDialog(self, config=self._config, t=self._t,
                      on_done=self._refresh_speakers)

    def _edit_profile(self) -> None:
        if not self._selected_profile:
            return
        from gui.panels.profile_dialog import ProfileDialog
        ProfileDialog(self, config=self._config, t=self._t,
                      folder_name=self._selected_profile,
                      on_done=self._refresh_speakers)

    def _delete_profile(self) -> None:
        if not self._selected_profile:
            return
        from tkinter import messagebox
        if messagebox.askyesno(
                self._t("delete_confirm_title"),
                self._t("delete_confirm_msg", count=1)):
            library_root = Path(self._config.get("library_root", "library"))
            try:
                from library.storage import LibraryStorage
                LibraryStorage(library_root).delete_profile(
                    self._selected_profile)
            except Exception:
                pass
            self._selected_profile = None
            self._refresh_speakers()
            self._refresh_groups()

    def _import_profiles(self) -> None:
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if not path:
            return
        from library.storage import LibraryStorage
        from library.importer import import_profiles
        from library.profile_creator import ConflictMode
        library_root = Path(self._config.get("library_root", "library"))
        storage = LibraryStorage(library_root)
        result = import_profiles(storage, Path(path), ConflictMode.MERGE)
        if result.retraining_required:
            from tkinter import messagebox
            if messagebox.askyesno("", self._t("profile_retrain_prompt")):
                self._retrain_all()
        self._refresh_speakers()
        self._refresh_groups()

    def _export_profiles(self) -> None:
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".zip", filetypes=[("ZIP files", "*.zip")])
        if not path:
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.exporter import export_profiles
        storage = LibraryStorage(library_root)
        profiles = [p.name for p in storage.list_profiles()]
        if profiles:
            export_profiles(storage, profiles, Path(path))

    def _retrain_all(self) -> None:
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.retrainer import LibraryRetrainer
            storage = LibraryStorage(library_root)
            result = LibraryRetrainer(storage).retrain_all()
            from tkinter import messagebox
            messagebox.showinfo(
                "", self._t("profile_retrain_done",
                             retrained=result.retrained,
                             failed=result.failed))
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    def _add_group(self) -> None:
        from tkinter.simpledialog import askstring
        name = askstring("", self._t("group_name_prompt"), parent=self)
        if not name:
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.groups import LibraryGroups
        groups = LibraryGroups(LibraryStorage(library_root))
        groups.create_group(name)
        self._refresh_groups()

    def _rename_group(self) -> None:
        from tkinter.simpledialog import askstring
        old = askstring("", self._t("group_name_prompt"), parent=self)
        if not old:
            return
        new = askstring("", self._t("group_new_name_prompt"), parent=self)
        if not new:
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.groups import LibraryGroups
        groups = LibraryGroups(LibraryStorage(library_root))
        try:
            groups.rename_group(old, new)
        except Exception:
            pass
        self._refresh_groups()

    def _delete_group(self) -> None:
        from tkinter.simpledialog import askstring
        name = askstring("", self._t("group_name_prompt"), parent=self)
        if not name:
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.groups import LibraryGroups
        groups = LibraryGroups(LibraryStorage(library_root))
        try:
            groups.delete_group(name)
        except Exception:
            pass
        self._refresh_groups()
