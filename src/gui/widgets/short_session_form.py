"""Short Session two-field interactive form (T-127 to T-133).

Displayed in the main window content area when Short Session mode is active
and the window is visible.

Layout:
  ┌─────────────────────────────────────────────────┐
  │ [Field 1 — editable transcription text]         │
  │                         [Translate & save btn]  │
  ├─────────────────────────────────────────────────┤
  │ [Field 2 — editable translation text]           │
  │                              [Save to clipboard]│
  └─────────────────────────────────────────────────┘

When translation is disabled, Field 2 and its button are hidden and Field 1
expands (T-128).  Both fields are cleared at the start of each new recording
(T-129).
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk
from gui.widgets.context_menu import bind_context_menu


class ShortSessionForm(ctk.CTkFrame):
    """Two-field form for Short Session mode.

    Parameters
    ----------
    master:
        Parent widget.
    on_translate_save:
        Called when "Translate and save to clipboard" / "Copy to clipboard"
        is clicked.  Receives the current text of Field 1.
    on_save_clipboard:
        Called when "Save to clipboard" (Field 2 button) is clicked.
        Receives the current text of Field 2.
    t:
        Translation callable ``t(key) → str``.
    """

    def __init__(
        self,
        master,
        on_translate_save: Callable[[str], None] | None = None,
        on_save_clipboard: Callable[[str], None] | None = None,
        t: Callable[[str], str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self._on_translate_save = on_translate_save or (lambda txt: None)
        self._on_save_clipboard = on_save_clipboard or (lambda txt: None)
        self._t = t or (lambda k: k)
        self._translation_enabled = True
        self._build()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_transcription(self, text: str) -> None:
        """Populate Field 1 with *text* (step 10 of Short Session spec)."""
        self._field1.delete("1.0", "end")
        self._field1.insert("1.0", text)

    def set_translation(self, text: str) -> None:
        """Populate Field 2 with *text* (step 10 of Short Session spec)."""
        self._field2.delete("1.0", "end")
        self._field2.insert("1.0", text)

    def clear_fields(self) -> None:
        """Clear both fields at the start of a new recording (T-129)."""
        self._field1.delete("1.0", "end")
        self._field2.delete("1.0", "end")

    def set_translation_enabled(self, enabled: bool) -> None:
        """Show/hide Field 2 and update button labels (T-128)."""
        self._translation_enabled = enabled
        btn_label = (
            self._t("btn_translate_save")
            if enabled
            else self._t("btn_copy_clipboard")
        )
        self._btn1.configure(text=btn_label)
        if enabled:
            self._frame2.grid()
        else:
            self._frame2.grid_remove()

    def get_transcription(self) -> str:
        return self._field1.get("1.0", "end-1c")

    def get_translation(self) -> str:
        return self._field2.get("1.0", "end-1c")

    def update_strings(self, t: Callable[[str], str]) -> None:
        """Re-apply language strings after a language change."""
        self._t = t
        self.set_translation_enabled(self._translation_enabled)
        self._btn2.configure(text=t("btn_save_clipboard"))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        t = self._t
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Frame 1: transcription field + button
        frame1 = ctk.CTkFrame(self, fg_color="transparent")
        frame1.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 2))
        frame1.grid_columnconfigure(0, weight=1)
        frame1.grid_rowconfigure(0, weight=1)

        self._field1 = ctk.CTkTextbox(frame1, wrap="word", undo=True)
        self._field1.grid(row=0, column=0, columnspan=2, sticky="nsew",
                          padx=4, pady=4)
        self._field1.insert("1.0", t("field_placeholder_transcription"))
        self._field1.bind("<FocusIn>", self._clear_placeholder1)
        bind_context_menu(self._field1)

        self._btn1 = ctk.CTkButton(
            frame1,
            text=t("btn_translate_save"),
            command=self._on_btn1,
        )
        self._btn1.grid(row=1, column=1, sticky="e", padx=4, pady=4)

        # Frame 2: translation field + button (T-128: hidden when disabled)
        self._frame2 = ctk.CTkFrame(self, fg_color="transparent")
        self._frame2.grid(row=1, column=0, sticky="nsew", padx=4, pady=(2, 4))
        self._frame2.grid_columnconfigure(0, weight=1)
        self._frame2.grid_rowconfigure(0, weight=1)

        self._field2 = ctk.CTkTextbox(self._frame2, wrap="word", undo=True)
        self._field2.grid(row=0, column=0, columnspan=2, sticky="nsew",
                          padx=4, pady=4)
        self._field2.insert("1.0", t("field_placeholder_translation"))
        self._field2.bind("<FocusIn>", self._clear_placeholder2)
        bind_context_menu(self._field2)

        self._btn2 = ctk.CTkButton(
            self._frame2,
            text=t("btn_save_clipboard"),
            command=self._on_btn2,
        )
        self._btn2.grid(row=1, column=1, sticky="e", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_btn1(self) -> None:
        self._on_translate_save(self.get_transcription())

    def _on_btn2(self) -> None:
        self._on_save_clipboard(self.get_translation())

    def _clear_placeholder1(self, _event=None) -> None:
        content = self._field1.get("1.0", "end-1c")
        if content == self._t("field_placeholder_transcription"):
            self._field1.delete("1.0", "end")

    def _clear_placeholder2(self, _event=None) -> None:
        content = self._field2.get("1.0", "end-1c")
        if content == self._t("field_placeholder_translation"):
            self._field2.delete("1.0", "end")
