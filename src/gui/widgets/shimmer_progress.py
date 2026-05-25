"""Shimmer-animated progress bar (Windows-Explorer-style wave).

Drop-in replacement for CTkProgressBar: same .set(value) / .get() API.
The shimmer starts automatically when 0 < value < 1 and stops otherwise.
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk


def _hex_blend(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colour strings."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


class ShimmerProgressBar(ctk.CTkFrame):
    """Progress bar with a light-wave shimmer overlay.

    Parameters match CTkProgressBar for easy substitution:
        width, height  — pixel dimensions (height defaults to 14)
    """

    _SHIMMER_WIDTH = 0.20   # stripe width as fraction of bar length
    _SHIMMER_SPEED = 0.022  # position advanced per frame (fraction)
    _SHIMMER_STEPS = 10     # gradient slices that form the soft edge
    _FRAME_MS = 33          # animation interval (~30 fps)

    # (track, fill, shimmer-highlight) per appearance mode
    _COLORS: dict[str, tuple[str, str, str]] = {
        "Dark":  ("#3d3d3d", "#1f6aa5", "#5ab4e8"),
        "Light": ("#d0d0d0", "#2B7DE9", "#80caff"),
    }

    def __init__(self, master, width: int = 200, height: int = 14, **kwargs) -> None:
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("corner_radius", 0)
        kwargs.setdefault("border_width", 0)
        super().__init__(master, width=width, height=height, **kwargs)
        # Prevent the frame from shrinking to fit canvas children
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._value: float = 0.0
        self._pos: float = -self._SHIMMER_WIDTH
        self._animating: bool = False
        self._after_id: str | None = None

        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Configure>", lambda _e: self._redraw())

    # ------------------------------------------------------------------
    # Public API (CTkProgressBar-compatible)
    # ------------------------------------------------------------------

    def set(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self._redraw()
        if 0.0 < self._value < 1.0:
            if not self._animating:
                self._start()
        else:
            self._stop()

    def get(self) -> float:
        return self._value

    # ------------------------------------------------------------------
    # Animation loop
    # ------------------------------------------------------------------

    def _start(self) -> None:
        self._animating = True
        self._pos = -self._SHIMMER_WIDTH
        self._step()

    def _stop(self) -> None:
        self._animating = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._redraw()

    def _step(self) -> None:
        if not self._animating:
            return
        self._pos += self._SHIMMER_SPEED
        if self._pos > 1.0 + self._SHIMMER_WIDTH:
            self._pos = -self._SHIMMER_WIDTH
        self._redraw()
        self._after_id = self.after(self._FRAME_MS, self._step)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _redraw(self) -> None:
        c = self._canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 2 or h < 2:
            return

        mode = ctk.get_appearance_mode()
        track_col, fill_col, shimmer_col = self._COLORS.get(mode, self._COLORS["Dark"])

        # Match canvas background to parent so rounded track corners blend in
        try:
            parent_fg = self.master.cget("fg_color")
            if isinstance(parent_fg, (list, tuple)):
                parent_bg = parent_fg[1 if mode == "Dark" else 0]
            else:
                parent_bg = parent_fg if parent_fg != "transparent" else track_col
        except Exception:
            parent_bg = track_col
        c.configure(bg=parent_bg)

        r = h // 2
        c.delete("all")

        # Track
        self._pill(c, 0, 0, w, h, r, track_col)

        # Fill
        fill_px = max(0, int(w * self._value))
        if fill_px > 0:
            self._pill(c, 0, 0, fill_px, h, min(r, fill_px // 2), fill_col)

        # Shimmer stripe (confined to the filled area)
        if self._animating and fill_px > 4:
            self._redraw_shimmer(c, fill_px, w, h, fill_col, shimmer_col)

    def _redraw_shimmer(self, c: tk.Canvas, fill_px: int, w: int, h: int,
                      fill_col: str, shimmer_col: str) -> None:
        sw = int(w * self._SHIMMER_WIDTH)
        cx = int(w * self._pos)
        x_left = cx - sw // 2
        x_right = cx + sw // 2
        n = max(1, self._SHIMMER_STEPS)
        stripe_w = max(1, (x_right - x_left) // n)

        for i in range(n):
            t_center = (i + 0.5) / n          # 0..1 across the stripe
            intensity = 1.0 - (2.0 * t_center - 1.0) ** 2  # bell curve, peak at 0.5
            col = _hex_blend(fill_col, shimmer_col, intensity)
            sx1 = max(0, min(fill_px, x_left + i * stripe_w))
            sx2 = max(0, min(fill_px, x_left + (i + 1) * stripe_w))
            if sx2 > sx1:
                c.create_rectangle(sx1, 0, sx2, h, fill=col, outline="")

    def _pill(self, canvas: tk.Canvas,
              x1: int, y1: int, x2: int, y2: int,
              r: int, color: str) -> None:
        """Filled rounded rectangle."""
        if x2 <= x1:
            return
        r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
        if r == 0:
            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            return
        # Horizontal and vertical body strips
        canvas.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="")
        canvas.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline="")
        # Four corner arcs
        canvas.create_arc(x1,     y1,     x1+2*r, y1+2*r, start=90,  extent=90, fill=color, outline=color)
        canvas.create_arc(x2-2*r, y1,     x2,     y1+2*r, start=0,   extent=90, fill=color, outline=color)
        canvas.create_arc(x1,     y2-2*r, x1+2*r, y2,     start=180, extent=90, fill=color, outline=color)
        canvas.create_arc(x2-2*r, y2-2*r, x2,     y2,     start=270, extent=90, fill=color, outline=color)
