"""Substitution Dictionary panel (T-101)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import tkinter as tk
import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu


_ALT_COLORS   = [("gray85", "gray20"), "transparent"]
_SEL_COLOR    = ("gray72", "gray35")
_ACCENT_SEL   = ("#3a7ebf", "#1f6aa5")
_ACCENT_NONE  = "transparent"
_SCROLLBAR_W  = 14


class SubstitutionDictPanel(BasePanel):
    """Table view with add/edit/delete/undo, CSV import and export."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ---- Toolbar ------------------------------------------------
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

        # ---- Header (non-scrolling, aligned via scrollbar offset) ---
        hdr = ctk.CTkFrame(self, fg_color=("gray78", "gray22"), corner_radius=6)
        hdr.grid(row=1, column=0, sticky="ew",
                 padx=(8, 8 + _SCROLLBAR_W), pady=(4, 0))
        hdr.grid_columnconfigure(0, minsize=4, weight=0)   # accent strip
        hdr.grid_columnconfigure(1, weight=2, minsize=140) # source
        hdr.grid_columnconfigure(2, weight=3)              # replacement

        # Source column header + help (label and button centred together)
        src_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        src_hdr.grid(row=0, column=1, sticky="ew", padx=(4, 2), pady=4)
        src_inner = ctk.CTkFrame(src_hdr, fg_color="transparent")
        src_inner.pack(expand=True)
        ctk.CTkLabel(src_inner, text=t("dict_col_source"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        self._info_btn(src_inner, "dict_help_source_title", "dict_help_source_text")

        # Replacement column header + help (label and button centred together)
        rep_hdr = ctk.CTkFrame(hdr, fg_color="transparent")
        rep_hdr.grid(row=0, column=2, sticky="ew", padx=(2, 6), pady=4)
        rep_inner = ctk.CTkFrame(rep_hdr, fg_color="transparent")
        rep_inner.pack(expand=True)
        ctk.CTkLabel(rep_inner, text=t("dict_col_replacement"),
                     font=ctk.CTkFont(weight="bold")).pack(side="left")
        self._info_btn(rep_inner, "dict_help_replacement_title",
                       "dict_help_replacement_text")

        # ---- Scrollable rows ----------------------------------------
        self._rows_frame = ctk.CTkScrollableFrame(self, corner_radius=6)
        self._rows_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(2, 4))

        self._undo_stack: list = []
        self._selected_row: int | None = None
        self._row_meta: list[tuple] = []   # (frame, accent_strip)
        self.on_show()

    # ------------------------------------------------------------------
    # Info (?) button
    # ------------------------------------------------------------------

    def _info_btn(self, parent, title_key: str, text_key: str) -> None:
        ctk.CTkButton(
            parent, text="?", width=22, height=22,
            fg_color=("#3a7ebf", "#1f6aa5"),
            hover_color=("#2b6aaa", "#18568a"),
            text_color="white",
            border_width=0,
            corner_radius=11,
            command=lambda: self._show_help(title_key, text_key),
        ).pack(side="left", padx=(4, 0))

    def _show_help(self, title_key: str, text_key: str) -> None:
        t = self._t
        win = ctk.CTkToplevel(self)
        win.title(t(title_key))
        win.geometry("480x300")
        win.resizable(True, True)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        txt = ctk.CTkTextbox(win, wrap="word", activate_scrollbars=True)
        txt.pack(fill="both", expand=True, padx=12, pady=(12, 4))
        txt.insert("end", t(text_key))
        txt.configure(state="disabled")
        ctk.CTkButton(win, text=t("btn_close"),
                      command=win.destroy).pack(pady=(4, 12))
        win.after(100, win.focus_force)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        self._refresh()

    def _get_store(self):
        from dictionary.store import DictionaryStore
        path = Path(self._config.get("dictionary_file", "dictionary.json"))
        return DictionaryStore(path)

    def _refresh(self) -> None:
        for w in self._rows_frame.winfo_children():
            w.destroy()
        self._row_meta.clear()
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
            self._add_row(i, entry.source, entry.replacement)

    def _add_row(self, idx: int, source: str, replacement: str) -> None:
        row_fg = _ALT_COLORS[idx % 2]

        bg = self._resolve_color(row_fg)
        frame = tk.Frame(self._rows_frame, background=bg)
        frame.pack(fill="x")
        frame.grid_columnconfigure(0, minsize=4, weight=0)   # accent strip
        frame.grid_columnconfigure(1, weight=2, minsize=140) # source
        frame.grid_columnconfigure(2, weight=3)              # replacement

        accent = tk.Frame(frame, width=4, background=bg)
        accent.grid(row=0, column=0, sticky="nsew")

        src_var = ctk.StringVar(value=source)
        rep_var = ctk.StringVar(value=replacement)

        e_src = ctk.CTkEntry(frame, textvariable=src_var, height=28,
                              border_width=0, fg_color=("gray90", "gray17"),
                              corner_radius=4)
        e_src.grid(row=0, column=1, sticky="ew", padx=(4, 2), pady=2)
        bind_context_menu(e_src, t=self._t)

        e_rep = ctk.CTkEntry(frame, textvariable=rep_var, height=28,
                              border_width=0, fg_color=("gray90", "gray17"),
                              corner_radius=4)
        e_rep.grid(row=0, column=2, sticky="ew", padx=(2, 8), pady=2)
        bind_context_menu(e_rep, t=self._t)

        for var in (src_var, rep_var):
            var.trace_add("write",
                          lambda *_, s=src_var, r=rep_var, orig=source:
                          self._on_edit(orig, s.get(), r.get()))

        for widget in (frame, accent):
            widget.bind("<Button-1>", lambda e, i=idx: self._select_row(i))
        for entry in (e_src, e_rep):
            entry.bind("<FocusIn>", lambda e, i=idx: self._select_row(i))

        self._row_meta.append((frame, accent))

    def _resolve_color(self, color) -> str:
        """Resolve a CTk color tuple or name to a hex string for tk.Frame."""
        if color == "transparent":
            mode = ctk.get_appearance_mode()
            # Match CTkScrollableFrame's default bg
            return "#2b2b2b" if mode == "Dark" else "#ebebeb"
        if isinstance(color, tuple):
            mode = ctk.get_appearance_mode()
            return color[1] if mode == "Dark" else color[0]
        return color

    def _select_row(self, idx: int) -> None:
        self._selected_row = idx
        for i, (frame, accent) in enumerate(self._row_meta):
            if i == idx:
                sel_bg = self._resolve_color(_SEL_COLOR)
                acc_bg = self._resolve_color(_ACCENT_SEL)
            else:
                sel_bg = self._resolve_color(_ALT_COLORS[i % 2])
                acc_bg = self._resolve_color(_ACCENT_NONE)
            frame.configure(background=sel_bg)
            accent.configure(background=acc_bg)

    # ------------------------------------------------------------------
    # Edit callbacks
    # ------------------------------------------------------------------

    def _on_edit(self, original_source: str, new_src: str,
                 new_rep: str) -> None:
        try:
            store = self._get_store()
            old = store._entries.get(original_source.lower())
            if old:
                self._undo_stack.append(
                    ("edit", original_source, old.source, old.replacement))
                store.remove(original_source)
                store.add(new_src, new_rep)
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
                self._undo_stack.append(
                    ("delete", entry.source, entry.replacement))
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
                store.add(op[1], op[2])
            elif op[0] == "edit":
                store.remove(op[1])
                store.add(op[2], op[3])
        except Exception:
            pass
        self._refresh()

    # ------------------------------------------------------------------
    # CSV import / export
    # ------------------------------------------------------------------

    def _import_csv(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            from dictionary.importer import import_csv
            result = import_csv(Path(path), self._get_store())
            messagebox.showinfo(
                "", self._t("dict_import_result",
                             added=result.added, rejected=result.rejected))
        except Exception as exc:
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
            messagebox.showinfo("", self._t("dict_export_result", count=count))
        except Exception as exc:
            messagebox.showerror(self._t("error_title"), str(exc))


# ---------------------------------------------------------------------------
# Add-entry dialog
# ---------------------------------------------------------------------------

class _EntryEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, t: Callable) -> None:
        super().__init__(parent)
        self._t = t
        self.title(t("btn_add_entry"))
        self.geometry("400x150")
        self.resizable(False, False)
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
        ]):
            ctk.CTkLabel(self, text=t(label_key)).grid(
                row=row, column=0, sticky="w", padx=12, pady=6)
            var = ctk.StringVar()
            setattr(self, attr, var)
            e = ctk.CTkEntry(self, textvariable=var)
            e.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
            bind_context_menu(e)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="e",
                       padx=12, pady=8)
        ctk.CTkButton(btn_frame, text=t("btn_cancel"),
                      fg_color="#555555",
                      command=self.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=t("btn_confirm"),
                      command=self._confirm).pack(side="left")

    def _confirm(self) -> None:
        src = self._src.get().strip()
        if src:
            self.result = (src, self._rep.get())
        self.destroy()
