"""Speaker Labelling Prompt panel (T-105)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from gui.panels.base import BasePanel


class SpeakerLabellingPanel(BasePanel):
    """Audio playback, metadata form, Skip and Confirm buttons, undo."""

    def __init__(self, master, config, t: Callable,
                 on_label_confirmed: Callable[[str, str], None] | None = None,
                 **kwargs) -> None:
        self._on_label_confirmed = on_label_confirmed or (lambda sid, name: None)
        self._pending_speakers: list[dict] = []
        self._current_index = 0
        self._undo_stack: list[tuple] = []
        super().__init__(master, config, t, **kwargs)

    def build(self) -> None:
        t = self._t
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=t("labelling_title"),
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 4))

        self._prompt_label = ctk.CTkLabel(self, text=t("labelling_no_pending"))
        self._prompt_label.grid(row=1, column=0, columnspan=3,
                                 sticky="w", padx=12, pady=4)

        # Metadata form
        self._form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._form_frame.grid(row=2, column=0, columnspan=3,
                               sticky="ew", padx=12, pady=4)
        self._form_frame.grid_columnconfigure(1, weight=1)

        self._name_vars: dict[str, ctk.StringVar] = {}
        for row, (field, label_key) in enumerate([
            ("lastname", "profile_lastname"),
            ("firstname", "profile_firstname"),
            ("middlename", "profile_middlename"),
            ("nickname", "profile_nickname"),
            ("organisation", "profile_organisation"),
            ("position", "profile_position"),
            ("note", "profile_note"),
        ]):
            ctk.CTkLabel(self._form_frame, text=t(label_key)).grid(
                row=row, column=0, sticky="w", padx=8, pady=3)
            var = ctk.StringVar()
            self._name_vars[field] = var
            ctk.CTkEntry(self._form_frame, textvariable=var).grid(
                row=row, column=1, sticky="ew", padx=8, pady=3)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="e",
                       padx=12, pady=12)
        ctk.CTkButton(btn_frame, text=t("btn_play_fragment"),
                      command=self._play_fragment).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=t("btn_undo_label"),
                      command=self._undo).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=t("btn_skip_speaker"),
                      fg_color="#555555",
                      command=self._skip).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=t("btn_confirm_label"),
                      command=self._confirm).pack(side="left", padx=4)

        self._set_form_visible(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_pending(self, pending: list[dict]) -> None:
        """Load a list of pending speakers.

        Each item must have ``speaker_id`` and optionally ``fragment_path``.
        """
        self._pending_speakers = pending
        self._current_index = 0
        self._undo_stack.clear()
        self._show_current()

    # ------------------------------------------------------------------

    def _show_current(self) -> None:
        if self._current_index >= len(self._pending_speakers):
            self._prompt_label.configure(
                text=self._t("labelling_no_pending"))
            self._set_form_visible(False)
            return
        speaker = self._pending_speakers[self._current_index]
        self._prompt_label.configure(
            text=self._t("labelling_prompt") +
            f" (ID: {speaker.get('speaker_id', '?')})")
        for var in self._name_vars.values():
            var.set("")
        self._set_form_visible(True)

    def _set_form_visible(self, visible: bool) -> None:
        if visible:
            self._form_frame.grid()
        else:
            self._form_frame.grid_remove()

    def _play_fragment(self) -> None:
        if self._current_index >= len(self._pending_speakers):
            return
        fragment_path = self._pending_speakers[self._current_index].get(
            "fragment_path")
        if fragment_path:
            try:
                import vlc
                player = vlc.MediaPlayer(fragment_path)
                player.play()
            except Exception:
                pass

    def _confirm(self) -> None:
        if self._current_index >= len(self._pending_speakers):
            return
        speaker = self._pending_speakers[self._current_index]
        name_parts = [
            self._name_vars.get("lastname", ctk.StringVar()).get(),
            self._name_vars.get("firstname", ctk.StringVar()).get(),
        ]
        display_name = " ".join(p for p in name_parts if p).strip() or "Unknown"
        self._undo_stack.append((self._current_index, speaker, {}))
        self._on_label_confirmed(speaker["speaker_id"], display_name)
        self._current_index += 1
        self._show_current()

    def _skip(self) -> None:
        if self._current_index < len(self._pending_speakers):
            self._current_index += 1
            self._show_current()

    def _undo(self) -> None:
        if not self._undo_stack:
            return
        idx, speaker, _ = self._undo_stack.pop()
        self._current_index = idx
        self._show_current()
