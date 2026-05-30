"""Batch Queue panel (T-102)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel


class BatchQueuePanel(BasePanel):
    """File list with add/remove, start button, and error pop-up on completion."""

    def __init__(self, master, config, t: Callable,
                 pipeline_runner=None, sound_player=None,
                 on_display_result=None, on_labelling_needed=None, **kwargs) -> None:
        self._runner = pipeline_runner
        self._sound = sound_player
        self._on_display_result = on_display_result
        self._on_labelling_needed = on_labelling_needed
        super().__init__(master, config, t, **kwargs)

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        self._btn_add = ctk.CTkButton(
            toolbar, text=t("btn_add_files"), command=self._add_files)
        self._btn_add.pack(side="left", padx=4)
        self._btn_remove = ctk.CTkButton(
            toolbar, text=t("btn_remove_file"), command=self._remove_file)
        self._btn_remove.pack(side="left", padx=4)
        ctk.CTkButton(toolbar, text=t("btn_clear_queue"),
                      command=self._clear_queue).pack(side="left", padx=4)
        self._btn_start = ctk.CTkButton(
            toolbar, text=t("btn_start_batch"), command=self._start_batch)
        self._btn_start.pack(side="right", padx=4)

        self._file_list = ctk.CTkScrollableFrame(self)
        self._file_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        self._status_label = ctk.CTkLabel(self, text="")
        self._status_label.grid(row=2, column=0, sticky="w", padx=8, pady=4)

        self._files: list[str] = []
        self._selected: str | None = None
        self._locked = False
        self._refresh()

    def _refresh(self) -> None:
        for w in self._file_list.winfo_children():
            w.destroy()
        if not self._files:
            ctk.CTkLabel(self._file_list,
                         text=self._t("batch_empty")).pack(padx=8, pady=8)
            return
        for path in self._files:
            frame = ctk.CTkFrame(self._file_list, fg_color="transparent")
            frame.pack(fill="x", pady=1)
            ctk.CTkLabel(frame, text=Path(path).name).pack(
                side="left", padx=8)
            frame.bind("<Button-1>",
                       lambda e, p=path: setattr(self, "_selected", p))

    def _add_files(self) -> None:
        if self._locked:
            return
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            filetypes=[("Audio/Video", "*.mp3 *.wav *.mp4 *.avi")])
        for p in paths:
            if p not in self._files:
                self._files.append(p)
        self._refresh()

    def _remove_file(self) -> None:
        if self._locked or not self._selected:
            return
        self._files = [f for f in self._files if f != self._selected]
        self._selected = None
        self._refresh()

    def _clear_queue(self) -> None:
        if self._locked:
            return
        self._files.clear()
        self._refresh()

    def _start_batch(self) -> None:
        if not self._files or self._locked or not self._runner:
            return
        self._locked = True
        self._btn_add.configure(state="disabled")
        self._btn_remove.configure(state="disabled")
        self._btn_start.configure(state="disabled")
        self._status_label.configure(text=self._t("batch_processing"))

        failed: list[str] = []

        def on_file_done(path, result):
            if not result.ok:
                failed.append(path)
            if self._on_display_result:
                self.after(0, lambda r=result: self._on_display_result(r))

        def on_batch_done(failed_files):
            self.after(0, lambda: self._on_batch_complete(failed_files))

        output_dir = Path(self._config.get("output_folder") or ".")
        formats = self._config.get("output_formats", ["txt"])

        def labelling_needed(result, done_event):
            if self._on_labelling_needed:
                self.after(0, lambda r=result, e=done_event:
                           self._on_labelling_needed(r, e))
            else:
                if result.write_output_fn:
                    result.write_output_fn()
                done_event.set()

        self._runner.start_batch(
            self._files,
            output_dir=output_dir,
            formats=formats,
            on_file_done=on_file_done,
            on_batch_done=on_batch_done,
            on_labelling_needed=labelling_needed,
        )

    def _on_batch_complete(self, failed: list[str]) -> None:
        self._locked = False
        self._btn_add.configure(state="normal")
        self._btn_remove.configure(state="normal")
        self._btn_start.configure(state="normal")
        self._status_label.configure(text=self._t("batch_done"))
        if self._sound:
            self._sound.play()
        if failed:
            from tkinter import messagebox
            messagebox.showerror(
                self._t("batch_errors_title"),
                self._t("batch_errors_msg", files="\n".join(failed)))
