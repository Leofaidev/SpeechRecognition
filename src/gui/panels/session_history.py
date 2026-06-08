"""Session History panel (T-106)."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk

import customtkinter as ctk

from gui.panels.base import BasePanel


# Column definition: (lang_key, min_width_px, flex_weight, text_anchor)
_COLUMNS = [
    ("history_col_date",     148, 0, "w"),
    ("history_col_source",     0, 1, "w"),
    ("history_col_duration",  76, 0, "center"),
    ("history_col_speakers", 160, 0, "w"),
]

_ALT_COLORS = [("gray85", "gray20"), "transparent"]
_SEL_COLOR  = ("gray72", "gray35")


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _fmt_date(raw: str) -> str:
    if not raw:
        return "—"
    try:
        from datetime import datetime
        return datetime.fromisoformat(raw).astimezone().strftime("%d %b %Y  %H:%M")
    except Exception:
        return raw


def _fmt_duration(secs) -> str:
    try:
        s = int(secs)
    except (TypeError, ValueError):
        s = 0
    if s <= 0:
        return "—"
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}h {m}m" if h else f"{m}m {sec:02d}s"


def _fmt_speakers(names: list) -> str:
    if not names:
        return "—"
    shown = ", ".join(names[:2])
    extra = len(names) - 2
    return f"{shown}  +{extra}" if extra > 0 else shown


def _configure_columns(widget) -> None:
    for col, (_, minsize, weight, _) in enumerate(_COLUMNS):
        widget.grid_columnconfigure(col, minsize=minsize, weight=weight)


def _theme_bg() -> str:
    return "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ebebeb"


def _theme_hdr_bg() -> str:
    return "#3c3c3c" if ctk.get_appearance_mode() == "Dark" else "#d0d0d0"


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class SessionHistoryPanel(BasePanel):
    """List of past sessions with regenerate and delete actions."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- Toolbar ------------------------------------------------
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        ctk.CTkButton(toolbar, text=t("btn_regenerate"),
                      command=self._regenerate).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_delete_session"),
                      command=self._delete_session).pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_clear_history"),
                      command=self._clear_history).pack(side="left", padx=4)

        # ---- Table container ----------------------------------------
        table = ctk.CTkFrame(self, fg_color="transparent")
        table.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        table.grid_columnconfigure(0, weight=1)
        table.grid_rowconfigure(1, weight=1)

        bg = _theme_bg()

        # Header canvas — follows x-scroll of content canvas, fixed height
        self._hdr_canvas = tk.Canvas(table, bg=_theme_hdr_bg(),
                                      highlightthickness=0)
        self._hdr_canvas.grid(row=0, column=0, sticky="ew")

        # Content canvas — scrolls both x and y
        self._content_canvas = tk.Canvas(table, bg=bg, highlightthickness=0)
        self._content_canvas.grid(row=1, column=0, sticky="nsew")

        # Vertical scrollbar only — no horizontal scroll
        vbar = ctk.CTkScrollbar(table, orientation="vertical",
                                 command=self._content_canvas.yview)
        vbar.grid(row=1, column=1, sticky="ns")

        self._content_canvas.configure(yscrollcommand=vbar.set)

        # ---- Header frame (inside header canvas) --------------------
        self._hdr_frame = ctk.CTkFrame(self._hdr_canvas,
                                        fg_color=("gray78", "gray22"),
                                        corner_radius=0)
        self._hdr_win = self._hdr_canvas.create_window(
            0, 0, anchor="nw", window=self._hdr_frame)
        _configure_columns(self._hdr_frame)
        for col, (key, _, _, anchor) in enumerate(_COLUMNS):
            ctk.CTkLabel(self._hdr_frame, text=t(key), anchor=anchor,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=0, column=col, padx=(8, 4), pady=5, sticky="ew")
        self._hdr_frame.bind("<Configure>", self._on_hdr_frame_configure)

        # ---- Content frame (inside content canvas) ------------------
        self._content_frame = ctk.CTkFrame(self._content_canvas,
                                            fg_color="transparent",
                                            corner_radius=0)
        self._content_win = self._content_canvas.create_window(
            0, 0, anchor="nw", window=self._content_frame)
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.bind("<Configure>", self._on_content_frame_configure)

        # Canvas resize: keep inner frames stretched to canvas width (or min)
        self._content_canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse-wheel scrolling anywhere inside the panel
        self._content_canvas.bind("<MouseWheel>", self._on_mousewheel)

        self._selected_id: str | None = None
        self._row_items: dict[str, tuple[ctk.CTkFrame, int]] = {}
        self.on_show()

    # ------------------------------------------------------------------
    # Scroll coordination
    # ------------------------------------------------------------------

    def _on_canvas_resize(self, event) -> None:
        """Canvas width changed — stretch both inner frames to fill it."""
        w = event.width
        self._content_canvas.itemconfigure(self._content_win, width=w)
        self._hdr_canvas.itemconfigure(self._hdr_win, width=w)

    def _on_hdr_frame_configure(self, event) -> None:
        """Header frame realised — lock header canvas height to match."""
        self._hdr_canvas.configure(height=event.height,
                                    scrollregion=(0, 0, event.width, event.height))

    def _on_content_frame_configure(self, event) -> None:
        """Content frame size changed — update scroll region."""
        self._content_canvas.configure(
            scrollregion=(0, 0, event.width, event.height))

    def _on_mousewheel(self, event) -> None:
        self._content_canvas.yview_scroll(int(-1 * event.delta / 120), "units")

    # ------------------------------------------------------------------
    # Data / selection
    # ------------------------------------------------------------------

    def on_show(self) -> None:
        self._refresh()

    def _select_row(self, sid: str) -> None:
        self._selected_id = sid
        for s_id, (frame, idx) in self._row_items.items():
            frame.configure(fg_color=_SEL_COLOR if s_id == sid
                            else _ALT_COLORS[idx % 2])

    def _refresh(self) -> None:
        for w in self._content_frame.winfo_children():
            w.destroy()
        self._row_items.clear()

        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        try:
            from session.history import list_sessions
            sessions = list_sessions(sessions_dir)
        except Exception:
            sessions = []

        if not sessions:
            ctk.CTkLabel(self._content_frame,
                         text=self._t("history_empty")).pack(padx=8, pady=8)
            return

        for i, s in enumerate(sessions):
            sid     = s.get("session_id", "")
            source  = s.get("source_path", s.get("source_type", ""))
            row_data = [
                _fmt_date(s.get("created_at", "")),
                Path(source).name if source else "—",
                _fmt_duration(s.get("duration_seconds", 0)),
                _fmt_speakers(s.get("speakers", [])),
            ]
            outdated = s.get("output_outdated", False)

            row_frame = ctk.CTkFrame(self._content_frame,
                                     fg_color=_ALT_COLORS[i % 2],
                                     corner_radius=0)
            row_frame.grid(row=i, column=0, sticky="ew")
            _configure_columns(row_frame)
            self._row_items[sid] = (row_frame, i)

            for col, text in enumerate(row_data):
                lbl = ctk.CTkLabel(row_frame, text=text,
                                   anchor=_COLUMNS[col][3])
                lbl.grid(row=0, column=col, padx=(8, 4), pady=3, sticky="ew")
                lbl.bind("<Button-1>", lambda e, k=sid: self._select_row(k))
                lbl.bind("<MouseWheel>", self._on_mousewheel)

            if outdated:
                lbl_out = ctk.CTkLabel(row_frame,
                              text=self._t("history_outdated_indicator"),
                              text_color="#ff9800")
                lbl_out.grid(row=0, column=4, padx=4)
                lbl_out.bind("<Button-1>", lambda e, k=sid: self._select_row(k))
                lbl_out.bind("<MouseWheel>", self._on_mousewheel)
            row_frame.bind("<Button-1>", lambda e, k=sid: self._select_row(k))
            row_frame.bind("<MouseWheel>", self._on_mousewheel)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _regenerate(self) -> None:
        if not self._selected_id:
            return
        sessions_dir = Path(self._config.get("sessions_dir", "sessions"))
        output_dir   = Path(self._config.get("output_folder") or ".")
        try:
            from session.history import regenerate_output
            written = regenerate_output(sessions_dir, self._selected_id, output_dir)
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
