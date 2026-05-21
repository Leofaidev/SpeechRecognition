"""Substitution Dictionary panel (T-101)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu


class SubstitutionDictPanel(BasePanel):
    """Table view with add/edit/delete/undo, CSV import and export."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        ctk.CTkButton(toolbar, text=t("btn_add_entry"),
                      command=self._add_entry).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_delete_entry"),
                      command=self._delete_entry).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_undo"),
                      command=self._undo).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_import_csv"),
                      command=self._import_csv).pack(side="right", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_export_csv"),
                      command=self._export_csv).pack(side="right", padx=4)

        # Table header
        hdr = ctk.CTkFrame(self)
        hdr.grid(row=1, column=0, sticky="ew", padx=8)
        for col, key, w in [(0, "dict_col_source", 200),
                             (1, "dict_col_replacement", 200),
                             (2, "dict_col_flags", 80)]:
            ctk.CTkLabel(hdr, text=t(key), width=w,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=col, padx=4, pady=2)

        # Scrollable entry list
        self._rows_frame = ctk.CTkScrollableFrame(self)
        self._rows_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.grid_rowconfigure(2, weight=1)

        self._undo_stack: list = []
        self._selected_row: int | None = None
        self.on_show()

    def on_show(self) -> None:
        self._refresh()

    def _get_store(self):
        from dictionary.store import DictionaryStore
        path = Path(self._config.get("dictionary_file", "dictionary.json"))
        return DictionaryStore(path)

    def _refresh(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()
        try:
            store = self._get_store()
            entries = list(store._entries.values())
        except Exception:
            entries = []
        if not entries:
            ctk.CTkLabel(self._rows_frame,
                         text=self._t("dict_empty")).pack(padx=8, pady=8)
            return
        for i, entry in enumerate(entries):
            self._add_row(i, entry.source, entry.replacement, entry.flags)

    def _add_row(self, idx: int, source: str, replacement: str,
                 flags: str) -> None:
        frame = ctk.CTkFrame(self._rows_frame, fg_color="transparent")
        frame.pack(fill="x", pady=1)
        src_var = ctk.StringVar(value=source)
        rep_var = ctk.StringVar(value=replacement)
        flg_var = ctk.StringVar(value=flags)
        e_src = ctk.CTkEntry(frame, textvariable=src_var, width=196)
        e_src.grid(row=0, column=0, padx=2)
        bind_context_menu(e_src)
        e_rep = ctk.CTkEntry(frame, textvariable=rep_var, width=196)
        e_rep.grid(row=0, column=1, padx=2)
        bind_context_menu(e_rep)
        e_flg = ctk.CTkEntry(frame, textvariable=flg_var, width=76)
        e_flg.grid(row=0, column=2, padx=2)
        bind_context_menu(e_flg)
        for var, field in [(src_var, "source"), (rep_var, "replacement"),
                            (flg_var, "flags")]:
            var.trace_add("write", lambda *_, s=src_var, r=rep_var, f=flg_var,
                                           orig=source: self._on_edit(
                                               orig, s.get(), r.get(), f.get()))
        frame.bind("<Button-1>", lambda e, i=idx: setattr(self, "_selected_row", i))

    def _on_edit(self, original_source: str, new_src: str, new_rep: str,
                 new_flags: str) -> None:
        try:
            store = self._get_store()
            old = store._entries.get(original_source.lower())
            if old:
                self._undo_stack.append(("edit", original_source,
                                          old.source, old.replacement, old.flags))
                store.remove(original_source)
                store.add(new_src, new_rep, new_flags)
        except Exception:
            pass

    def _add_entry(self) -> None:
        dialog = _EntryEditDialog(self, t=self._t)
        self.wait_window(dialog)
        if dialog.result:
            try:
                store = self._get_store()
                store.add(*dialog.result)
                self._undo_stack.append(("add", dialog.result[0]))
            except Exception:
                pass
            self._refresh()

    def _delete_entry(self) -> None:
        if self._selected_row is None:
            return
        try:
            store = self._get_store()
            entries = list(store._entries.values())
            if self._selected_row < len(entries):
                entry = entries[self._selected_row]
                self._undo_stack.append(("delete", entry.source,
                                          entry.replacement, entry.flags))
                store.remove(entry.source)
        except Exception:
            pass
        self._selected_row = None
        self._refresh()

    def _undo(self) -> None:
        if not self._undo_stack:
            return
        op = self._undo_stack.pop()
        try:
            store = self._get_store()
            if op[0] == "add":
                store.remove(op[1])
            elif op[0] == "delete":
                store.add(op[1], op[2], op[3])
            elif op[0] == "edit":
                store.remove(op[1])
                store.add(op[2], op[3], op[4])
        except Exception:
            pass
        self._refresh()

    def _import_csv(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            from dictionary.importer import import_csv
            result = import_csv(Path(path), self._get_store())
            messagebox.showinfo(
                "", self._t("dict_import_result",
                             added=result.added, rejected=result.rejected))
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))
        self._refresh()

    def _export_csv(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            from dictionary.exporter import export_csv
            count = export_csv(self._get_store(), Path(path))
            messagebox.showinfo(
                "", self._t("dict_export_result", count=count))
        except Exception as exc:
            messagebox.showerror(self._t("error_title"), str(exc))


class _EntryEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, t: Callable) -> None:
        super().__init__(parent)
        self._t = t
        self.title("")
        self.geometry("400x200")
        self.grab_set()
        self.result = None
        self._build()
        self.focus_force()

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)
        for row, (label_key, attr) in enumerate([
            ("dict_col_source", "_src"),
            ("dict_col_replacement", "_rep"),
            ("dict_col_flags", "_flg"),
        ]):
            ctk.CTkLabel(self, text=t(label_key)).grid(
                row=row, column=0, sticky="w", padx=12, pady=4)
            var = ctk.StringVar()
            setattr(self, attr, var)
            _e = ctk.CTkEntry(self, textvariable=var)
            _e.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
            bind_context_menu(_e)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="e",
                       padx=12, pady=8)
        ctk.CTkButton(btn_frame, text=t("btn_cancel"),
                      fg_color="#555555",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=t("btn_confirm"),
                      command=self._confirm).pack(side="left")

    def _confirm(self) -> None:
        src = self._src.get().strip()
        if src:
            self.result = (src, self._rep.get(), self._flg.get())
        self.destroy()
