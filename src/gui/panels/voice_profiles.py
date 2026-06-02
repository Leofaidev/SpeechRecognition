"""Voice Profile Management panel (T-92 to T-100)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel

_SEL_COLOR = ("#3B8ED0", "#1F6AA5")


class VoiceProfilesPanel(BasePanel):
    """Three-section layout: Groups (left), Members+Speakers (right)."""

    def __init__(self, master, config, t, on_groups_changed=None, **kwargs):
        self._on_groups_changed = on_groups_changed
        super().__init__(master, config, t, **kwargs)

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ---- Right column (Members + Speakers) ------------------------------
        left = ctk.CTkFrame(self)
        left.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)   # Members
        left.grid_rowconfigure(1, weight=2)   # Speakers

        # ---- Members section (top-left) ------------------------------------
        members_frame = ctk.CTkFrame(left)
        members_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))
        members_frame.grid_columnconfigure(0, weight=1)
        members_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(members_frame, text=t("profiles_members_section"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)

        self._member_list = ctk.CTkScrollableFrame(members_frame)
        self._member_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        mem_btn_row = ctk.CTkFrame(members_frame, fg_color="transparent")
        mem_btn_row.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        ctk.CTkButton(mem_btn_row, text=t("btn_add_member"),
                      command=self._add_member).pack(side="left", padx=4)
        ctk.CTkButton(mem_btn_row, text=t("btn_remove_member"),
                      command=self._remove_member).pack(side="left", padx=4)

        # ---- Speakers section (bottom-left) ---------------------------------
        speakers_frame = ctk.CTkFrame(left)
        speakers_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        speakers_frame.grid_columnconfigure(0, weight=1)
        speakers_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(speakers_frame, text=t("profiles_speakers_section"),
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)

        self._speaker_list = ctk.CTkScrollableFrame(speakers_frame)
        self._speaker_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

        btn_row1 = ctk.CTkFrame(speakers_frame, fg_color="transparent")
        btn_row1.grid(row=2, column=0, sticky="ew", padx=4, pady=(4, 0))
        ctk.CTkButton(btn_row1, text=t("btn_add_profile"),
                      command=self._add_profile).pack(side="left", padx=4)
        ctk.CTkButton(btn_row1, text=t("btn_edit_profile"),
                      command=self._edit_profile).pack(side="left", padx=4)
        ctk.CTkButton(btn_row1, text=t("btn_delete_profile"),
                      command=self._delete_profile).pack(side="left", padx=4)

        btn_row2 = ctk.CTkFrame(speakers_frame, fg_color="transparent")
        btn_row2.grid(row=3, column=0, sticky="ew", padx=4, pady=(4, 4))
        ctk.CTkButton(btn_row2, text=t("btn_import_zip"),
                      command=self._import_profiles).pack(side="left", padx=4)
        ctk.CTkButton(btn_row2, text=t("btn_export_zip"),
                      command=self._export_profiles).pack(side="left", padx=4)
        ctk.CTkButton(btn_row2, text=t("btn_retrain_all"),
                      command=self._retrain_all).pack(side="left", padx=4)

        # ---- Left: group list -----------------------------------------------
        right = ctk.CTkFrame(self)
        right.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
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

        # State
        self._selected_profile: str | None = None
        self._selected_group: str | None = None
        self._selected_member: str | None = None
        self._speaker_rows: dict[str, tuple] = {}
        self._group_rows: dict[str, tuple] = {}
        self._member_rows: dict[str, tuple] = {}
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
        self._speaker_rows = {}
        self._selected_profile = None
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
            display = name
            row_labels: list[ctk.CTkLabel] = []
            try:
                meta = storage.read_meta(name)
                parts = [meta.last_name, meta.first_name]
                full = " ".join(p for p in parts if p).strip()
                if not full:
                    full = meta.nickname
                if full:
                    display = full
            except Exception:
                pass
            frame = ctk.CTkFrame(self._speaker_list, fg_color="transparent",
                                  corner_radius=6)
            frame.pack(fill="x", padx=4, pady=2)
            lbl = ctk.CTkLabel(frame, text=display)
            lbl.pack(side="left", padx=8, pady=4)
            row_labels.append(lbl)
            if display != name:
                lbl2 = ctk.CTkLabel(frame, text=f"  {name}",
                                    text_color="gray60",
                                    font=ctk.CTkFont(size=11))
                lbl2.pack(side="left")
                row_labels.append(lbl2)
            self._speaker_rows[name] = (frame, row_labels)
            for w in (frame, lbl):
                w.bind("<Button-1>", lambda e, n=name: self._select_profile(n))

    def _select_profile(self, name: str) -> None:
        if self._selected_profile and self._selected_profile in self._speaker_rows:
            f, lbls = self._speaker_rows[self._selected_profile]
            f.configure(fg_color="transparent")
            for lb in lbls:
                lb.configure(text_color=("gray10", "gray90"))
        self._selected_profile = name
        if name in self._speaker_rows:
            f, lbls = self._speaker_rows[name]
            f.configure(fg_color=_SEL_COLOR)
            for lb in lbls:
                lb.configure(text_color="white")

    # ------------------------------------------------------------------
    # Group list
    # ------------------------------------------------------------------

    def _refresh_groups(self) -> None:
        for w in self._group_list.winfo_children():
            w.destroy()
        self._group_rows = {}
        self._selected_group = None
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            storage = LibraryStorage(library_root)
            groups = LibraryGroups(storage)
            group_names = list(groups.list_groups())
        except Exception:
            group_names = []

        # Include config-stored group names (empty groups with no speakers yet)
        for name in self._config.get("known_groups", []):
            if name not in group_names:
                group_names.append(name)

        if not group_names:
            ctk.CTkLabel(self._group_list,
                         text=self._t("groups_empty")).pack(padx=8, pady=8)
            self._refresh_members()
            if self._on_groups_changed:
                self._on_groups_changed([])
            return

        for g in group_names:
            frame = ctk.CTkFrame(self._group_list, fg_color="transparent",
                                  corner_radius=6)
            frame.pack(fill="x", padx=4, pady=2)
            lbl = ctk.CTkLabel(frame, text=g)
            lbl.pack(side="left", padx=8, pady=4)
            self._group_rows[g] = (frame, [lbl])
            for w in (frame, lbl):
                w.bind("<Button-1>", lambda e, gn=g: self._select_group(gn))

        # Auto-select the first group
        self._select_group(group_names[0])
        if self._on_groups_changed:
            self._on_groups_changed(group_names)

    def _select_group(self, name: str) -> None:
        if self._selected_group and self._selected_group in self._group_rows:
            f, lbls = self._group_rows[self._selected_group]
            f.configure(fg_color="transparent")
            for lb in lbls:
                lb.configure(text_color=("gray10", "gray90"))
        self._selected_group = name
        if name in self._group_rows:
            f, lbls = self._group_rows[name]
            f.configure(fg_color=_SEL_COLOR)
            for lb in lbls:
                lb.configure(text_color="white")
        self._refresh_members()

    # ------------------------------------------------------------------
    # Members list
    # ------------------------------------------------------------------

    def _refresh_members(self) -> None:
        for w in self._member_list.winfo_children():
            w.destroy()
        self._member_rows = {}
        self._selected_member = None

        if not self._selected_group:
            return

        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            storage = LibraryStorage(library_root)
            groups = LibraryGroups(storage)
            folder_names = groups.members(self._selected_group)
        except Exception:
            folder_names = []

        if not folder_names:
            ctk.CTkLabel(self._member_list,
                         text=self._t("members_empty")).pack(padx=8, pady=8)
            return

        try:
            from library.storage import LibraryStorage
            storage = LibraryStorage(library_root)
        except Exception:
            storage = None

        for folder in folder_names:
            display = folder
            row_labels: list[ctk.CTkLabel] = []
            if storage:
                try:
                    meta = storage.read_meta(folder)
                    parts = [meta.last_name, meta.first_name]
                    full = " ".join(p for p in parts if p).strip()
                    if not full:
                        full = meta.nickname
                    if full:
                        display = full
                except Exception:
                    pass
            frame = ctk.CTkFrame(self._member_list, fg_color="transparent",
                                  corner_radius=6)
            frame.pack(fill="x", padx=4, pady=2)
            lbl = ctk.CTkLabel(frame, text=display)
            lbl.pack(side="left", padx=8, pady=4)
            row_labels.append(lbl)
            if display != folder:
                lbl2 = ctk.CTkLabel(frame, text=f"  {folder}",
                                    text_color="gray60",
                                    font=ctk.CTkFont(size=11))
                lbl2.pack(side="left")
                row_labels.append(lbl2)
            self._member_rows[folder] = (frame, row_labels)
            for w in (frame, lbl):
                w.bind("<Button-1>", lambda e, fn=folder: self._select_member(fn))

    def _select_member(self, folder: str) -> None:
        if self._selected_member and self._selected_member in self._member_rows:
            f, lbls = self._member_rows[self._selected_member]
            f.configure(fg_color="transparent")
            for lb in lbls:
                lb.configure(text_color=("gray10", "gray90"))
        self._selected_member = folder
        if folder in self._member_rows:
            f, lbls = self._member_rows[folder]
            f.configure(fg_color=_SEL_COLOR)
            for lb in lbls:
                lb.configure(text_color="white")

    def _add_member(self) -> None:
        if not self._selected_profile or not self._selected_group:
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            groups = LibraryGroups(LibraryStorage(library_root))
            groups.add_to_group(self._selected_profile, self._selected_group)
        except Exception:
            pass
        self._refresh_members()

    def _remove_member(self) -> None:
        if not self._selected_member or not self._selected_group:
            return
        library_root = Path(self._config.get("library_root", "library"))
        try:
            from library.storage import LibraryStorage
            from library.groups import LibraryGroups
            groups = LibraryGroups(LibraryStorage(library_root))
            groups.remove_from_group(self._selected_member, self._selected_group)
        except Exception:
            pass
        self._refresh_members()

    # ------------------------------------------------------------------
    # Button callbacks — profiles
    # ------------------------------------------------------------------

    def _add_profile(self) -> None:
        from gui.panels.profile_dialog import ProfileDialog
        ProfileDialog(self, config=self._config, t=self._t,
                      on_done=lambda fn: self._refresh_speakers())

    def _edit_profile(self) -> None:
        if not self._selected_profile:
            return
        from gui.panels.profile_dialog import ProfileDialog
        ProfileDialog(self, config=self._config, t=self._t,
                      folder_name=self._selected_profile,
                      on_done=lambda fn: self._refresh_speakers())

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
            from library.profile_creator import _pyannote_embed
            token = self._config.get("huggingface_token", None)
            embed_fn = (lambda a, sr, _t=token: _pyannote_embed(a, sr, token=_t))
            storage = LibraryStorage(library_root)
            result = LibraryRetrainer(storage, embed_fn).retrain_all()
            from tkinter import messagebox
            if result.failed:
                detail = "\n".join(
                    f"  {f}: {result.errors.get(f, '?')}"
                    for f in result.failed_profiles
                )
                messagebox.showerror(
                    self._t("error_title"),
                    self._t("profile_retrain_done",
                             retrained=result.retrained,
                             failed=result.failed) + f"\n\n{detail}")
            else:
                messagebox.showinfo(
                    "", self._t("profile_retrain_done",
                                 retrained=result.retrained,
                                 failed=result.failed))
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    # ------------------------------------------------------------------
    # Button callbacks — groups
    # ------------------------------------------------------------------

    def _add_group(self) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text=self._t("group_name_prompt")).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky="w")
        var = ctk.StringVar()
        entry = ctk.CTkEntry(dlg, textvariable=var, width=220)
        entry.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12))
        entry.focus_set()

        def _confirm():
            name = var.get().strip()
            if not name:
                return
            dlg.destroy()
            known = list(self._config.get("known_groups", []))
            if name not in known:
                known.append(name)
                self._config.set("known_groups", known)
            self._refresh_groups()

        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(0, 14))
        ctk.CTkButton(btn_frame, text=self._t("btn_confirm"),
                      command=_confirm).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=self._t("btn_cancel"),
                      command=dlg.destroy).pack(side="left", padx=8)
        entry.bind("<Return>", lambda e: _confirm())

    def _rename_group(self) -> None:
        if not self._selected_group:
            return
        from tkinter.simpledialog import askstring
        new = askstring("", self._t("group_new_name_prompt"), parent=self)
        if not new:
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.groups import LibraryGroups
        groups = LibraryGroups(LibraryStorage(library_root))
        try:
            groups.rename_group(self._selected_group, new)
        except Exception:
            pass
        # Keep config-stored names in sync
        known = list(self._config.get("known_groups", []))
        if self._selected_group in known:
            known.remove(self._selected_group)
            if new not in known:
                known.append(new)
            self._config.set("known_groups", known)
        self._refresh_groups()

    def _delete_group(self) -> None:
        if not self._selected_group:
            return
        from tkinter import messagebox
        if not messagebox.askyesno(
                self._t("delete_confirm_title"),
                self._t("delete_confirm_msg", count=1)):
            return
        library_root = Path(self._config.get("library_root", "library"))
        from library.storage import LibraryStorage
        from library.groups import LibraryGroups
        groups = LibraryGroups(LibraryStorage(library_root))
        try:
            groups.delete_group(self._selected_group)
        except Exception:
            pass
        # Remove from config-stored names
        known = list(self._config.get("known_groups", []))
        if self._selected_group in known:
            known.remove(self._selected_group)
            self._config.set("known_groups", known)
        self._refresh_groups()
