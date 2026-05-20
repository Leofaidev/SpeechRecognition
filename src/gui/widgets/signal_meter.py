"""Real-time signal level meter widget (T-82).

Displays the current microphone level as a horizontal bar.  The caller
updates it by calling :meth:`set_level` with a float in [0.0, 1.0].
"""

from __future__ import annotations

import customtkinter as ctk


_COLOURS = [
    (0.00, "#4caf50"),  # green
    (0.70, "#ff9800"),  # orange
    (0.90, "#f44336"),  # red
]


def _colour_for(level: float) -> str:
    colour = _COLOURS[0][1]
    for threshold, c in _COLOURS:
        if level >= threshold:
            colour = c
    return colour


class SignalMeter(ctk.CTkFrame):
    """Horizontal bar showing audio signal level.

    Parameters
    ----------
    width:
        Total widget width in pixels.
    height:
        Bar height in pixels.
    """

    def __init__(self, master, width: int = 200, height: int = 12,
                 **kwargs) -> None:
        super().__init__(master, width=width, height=height,
                         fg_color="transparent", **kwargs)
        self._bar_width = width
        self._bar_height = height
        self._level = 0.0
        self._canvas = ctk.CTkCanvas(self, width=width, height=height,
                                     highlightthickness=1,
                                     highlightbackground="#555555")
        self._canvas.pack()
        self._bg_rect = self._canvas.create_rectangle(
            0, 0, width, height, fill="#333333", outline=""
        )
        self._fill_rect = self._canvas.create_rectangle(
            0, 0, 0, height, fill="#4caf50", outline=""
        )

    # ------------------------------------------------------------------

    def set_level(self, level: float) -> None:
        """Update the displayed level.  ``level`` must be in [0.0, 1.0]."""
        self._level = max(0.0, min(1.0, level))
        fill_w = int(self._bar_width * self._level)
        colour = _colour_for(self._level)
        self._canvas.coords(self._fill_rect, 0, 0, fill_w, self._bar_height)
        self._canvas.itemconfig(self._fill_rect, fill=colour)

    def reset(self) -> None:
        self.set_level(0.0)
