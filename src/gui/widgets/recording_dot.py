"""Pulsing recording indicator widget (T-79).

Displays a small coloured circle that pulses when recording is active (red)
and stays solid grey when idle.
"""

from __future__ import annotations

import customtkinter as ctk


_DOT_SIZE = 16
_PULSE_INTERVAL_MS = 600


class RecordingDot(ctk.CTkCanvas):
    """A small animated dot: grey when idle, pulsing red when recording."""

    def __init__(self, master, **kwargs) -> None:
        kwargs.setdefault("width", _DOT_SIZE)
        kwargs.setdefault("height", _DOT_SIZE)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self._recording = False
        self._pulse_bright = True
        self._after_id: str | None = None
        self._oval = self.create_oval(2, 2, _DOT_SIZE - 2, _DOT_SIZE - 2,
                                      fill="#6b6b6b", outline="")
        self.configure(bg=self._get_bg())

    # ------------------------------------------------------------------

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if recording:
            self._pulse_bright = True
            self._animate()
        else:
            self._stop_animation()
            self.itemconfig(self._oval, fill="#6b6b6b")

    # ------------------------------------------------------------------

    def _animate(self) -> None:
        if not self._recording:
            return
        colour = "#e03030" if self._pulse_bright else "#802020"
        self.itemconfig(self._oval, fill=colour)
        self._pulse_bright = not self._pulse_bright
        self._after_id = self.after(_PULSE_INTERVAL_MS, self._animate)

    def _stop_animation(self) -> None:
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _get_bg(self) -> str:
        try:
            return self.winfo_rgb(
                self.tk.call("ttk::style", "lookup", "TFrame", "-background")
            )
        except Exception:
            return "#2b2b2b"
