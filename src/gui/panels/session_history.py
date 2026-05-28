"""Session History panel (T-106)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel


class SessionHistoryPanel(BasePanel):
    """List of past sessions with regenerate and delete actions."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        ctk.CTkButton(toolbar, text=t("btn_regenerate"),
                      command=self._regenerate).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_delete_session"),
                      command=self._delete_session).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_clear_history"),
                      command=self._clear_history).pack(side="left", padx=4)

        # Header
        hdr = ctk.CTkFrame(self)
        hdr.grid(row=1, column=0, sticky="ew", padx=8)
        for col, key, w in [
            (0, "history_col_date", 160),
            (1, "history_col_source", 220),
            (2, "history_col_duration", 80),
            (3, "history_col_speakers", 80),
        ]:
            ctk.CTkLabel(hdr, text=t(key), width=w,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=col, padx=4, pady=2)

        self._list_frame = ctk.CTkScrollableFrame(self)
        self._list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=4)
        self.grid_rowconfigure(2, weight=1)

        self._selected_id: str | None = None
        self._row_frames: dict[str, ctk.CTkFrame] = {}
        self.on_show()

    def on_show(self) -> None:
        self._refresh()

    def _select_row(self, sid: str) -> None:
        self._selected_id = sid
        for s_id, frame in self._row_frames.items():
            frame.configure(
                fg_color=("gray75", "gray25") if s_id == sid else "transparent")

    def _refresh(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_frames.clear()
        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        try:
            from session.history import list_sessions
            sessions = list_sessions(sessions_dir)
        except Exception:
            sessions = []

        if not sessions:
            ctk.CTkLabel(self._list_frame,
                         text=self._t("history_empty")).pack(padx=8, pady=8)
            return

        for s in sessions:
            sid = s.get("session_id", "")
            date = s.get("date", "")
            source = s.get("source_path", s.get("source_type", ""))
            duration = s.get("duration_seconds", 0)
            dur_str = f"{int(duration // 60)}m {int(duration % 60)}s"
            speakers = ", ".join(s.get("speakers", []))
            outdated = s.get("output_outdated", False)

            row_frame = ctk.CTkFrame(self._list_frame, fg_color="transparent",
                                     corner_radius=4)
            row_frame.pack(fill="x", pady=1)
            self._row_frames[sid] = row_frame
            for col, text, width in [
                (0, date, 156),
                (1, Path(source).name if source else "", 216),
                (2, dur_str, 76),
                (3, speakers[:20], 76),
            ]:
                lbl = ctk.CTkLabel(row_frame, text=text, width=width)
                lbl.grid(row=0, column=col, padx=4)
                lbl.bind("<Button-1>", lambda e, i=sid: self._select_row(i))
            if outdated:
                lbl_out = ctk.CTkLabel(row_frame,
                              text=self._t("history_outdated_indicator"),
                              text_color="#ff9800")
                lbl_out.grid(row=0, column=4, padx=4)
                lbl_out.bind("<Button-1>", lambda e, i=sid: self._select_row(i))
            row_frame.bind("<Button-1>", lambda e, i=sid: self._select_row(i))

    def _regenerate(self) -> None:
        if not self._selected_id:
            return
        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        output_dir = Path(self._config.get("output_folder") or ".")
        try:
            from session.history import regenerate_output
            written = regenerate_output(sessions_dir, self._selected_id,
                                         output_dir)
            from tkinter import messagebox
            messagebox.showinfo(
                "", self._t("history_regenerated",
                             path="\n".join(str(p) for p in written)))
        except FileNotFoundError:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"),
                                  f"Session not found: {self._selected_id}")

    def _delete_session(self) -> None:
        if not self._selected_id:
            return
        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        try:
            from session.history import delete
            delete(sessions_dir, self._selected_id)
        except Exception:
            pass
        self._selected_id = None
        self._refresh()

    def _clear_history(self) -> None:
        from tkinter import messagebox
        if not messagebox.askyesno(
                self._t("btn_clear_history"),
                self._t("history_clear_confirm")):
            return
        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        try:
            from session.history import list_sessions, delete
            for s in list_sessions(sessions_dir):
                try:
                    delete(sessions_dir, s["session_id"])
                except Exception:
                    pass
        except Exception:
            pass
        self._selected_id = None
        self._refresh()
