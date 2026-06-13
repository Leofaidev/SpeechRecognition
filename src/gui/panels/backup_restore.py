"""Backup and Restore panel (T-107)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel
from gui.widgets.context_menu import bind_context_menu


class BackupRestorePanel(BasePanel):
    """Backup creation, restore with safety backup, folder picker."""

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=t("backup_title"),
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        # Backup folder selection
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        folder_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(folder_frame, text=t("backup_folder_label")).grid(
            row=0, column=0, sticky="w", padx=4)
        self._folder_var = ctk.StringVar(
            value=self._config.get("backup_folder", ""))
        _e = ctk.CTkEntry(folder_frame, textvariable=self._folder_var)
        _e.grid(row=0, column=1, sticky="ew", padx=4)
        bind_context_menu(_e)
        ctk.CTkButton(folder_frame, text=t("btn_browse"), width=80,
                      command=self._browse_folder).grid(row=0, column=2, padx=4)

        self._size_label = ctk.CTkLabel(self, text="")
        self._size_label.grid(row=2, column=0, sticky="w", padx=12, pady=2)

        self._warn_label = ctk.CTkLabel(self, text="", text_color="#ff9800")
        self._warn_label.grid(row=3, column=0, sticky="w", padx=12, pady=2)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="w", padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("btn_create_backup"),
                      command=self._create_backup).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=t("btn_restore_backup"),
                      command=self._restore_backup).pack(side="left", padx=8)

        self._status_label = ctk.CTkLabel(self, text="", wraplength=500)
        self._status_label.grid(row=5, column=0, sticky="w", padx=12, pady=4)

        self._update_size_estimate()

    def on_show(self) -> None:
        self._update_size_estimate()

    def _browse_folder(self) -> None:
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self._folder_var.set(folder)
            self._config.set("backup_folder", folder)
            self._update_size_estimate()

    def _update_size_estimate(self) -> None:
        try:
            from backup.manager import AppPaths, estimated_backup_size
            paths = self._build_app_paths()
            size = estimated_backup_size(paths)
            self._size_label.configure(
                text=self._t("backup_size_estimate",
                              size=f"{size:,} bytes"))
        except Exception:
            self._size_label.configure(text="")

    def _build_app_paths(self):
        import sys, os
        from backup.manager import AppPaths
        c = self._config
        config_file = c.path
        if config_file is None:
            if sys.platform == "win32":
                base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            else:
                xdg = os.environ.get("XDG_DATA_HOME", "")
                base = xdg if xdg else os.path.join(os.path.expanduser("~"), ".local", "share")
            config_file = Path(base) / "SpeechRecognition" / "config.json"
        return AppPaths(
            config_file=config_file,
            dictionary_file=Path(c.get("dictionary_file", "dictionary.json")),
            library_root=Path(c.get("library_root", "library")),
            sessions_dir=Path(c.get("sessions_dir", "sessions")),
            install_dir=Path(c.get("install_dir", ".")),
        )

    def _create_backup(self) -> None:
        from tkinter import filedialog
        folder = self._folder_var.get() or "."
        path = filedialog.asksaveasfilename(
            initialdir=folder,
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")])
        if not path:
            return
        try:
            from backup.manager import create_backup
            result = create_backup(self._build_app_paths(), Path(path))
            if result.path_warning:
                self._warn_label.configure(
                    text=self._t("backup_inside_warning"))
            else:
                self._warn_label.configure(text="")
            self._status_label.configure(
                text=self._t("backup_created",
                              path=result.zip_path,
                              size=result.actual_size))
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    def _restore_backup(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if not path:
            return
        if not messagebox.askyesno(
                self._t("restore_confirm_title"),
                self._t("restore_confirm_msg")):
            return
        try:
            from backup.restorer import restore
            safety_dir = Path(
                self._config.get("install_dir", ".")) / "backups"
            result = restore(self._build_app_paths(), Path(path), safety_dir)
            if result.success:
                self._restart_app()
            else:
                self._status_label.configure(
                    text=self._t("restore_safety_msg",
                                  path=result.safety_backup_path) +
                    "\n" + self._t("restore_failed", error=result.error))
        except Exception as exc:
            from tkinter import messagebox
            messagebox.showerror(self._t("error_title"), str(exc))

    def _restart_app(self) -> None:
        import os, subprocess, sys
        from pathlib import Path
        launcher = Path(sys.executable)
        if sys.platform == "win32":
            w = launcher.parent / "pythonw.exe"
            if w.exists():
                launcher = w
        # src/ holds the gui package (3 levels up from panels/)
        src_dir = Path(__file__).resolve().parent.parent.parent
        repo_root = src_dir.parent
        # Use absolute PYTHONPATH so it's correct regardless of cwd
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "platforms") + os.pathsep + str(src_dir)
        kwargs: dict = {"cwd": str(src_dir), "env": env}
        if sys.platform != "win32":
            # Detach from the screen session so the child survives parent exit
            kwargs["start_new_session"] = True
        subprocess.Popen([str(launcher), "-m", "gui.app"], **kwargs)
        self.winfo_toplevel()._shutdown(save_config=False)
