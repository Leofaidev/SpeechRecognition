"""System tray icon (T-108 to T-112).

Wraps ``pystray`` to provide the right-click context menu, minimize-to-tray
behaviour, and tray balloon notifications.

The ``TrayIcon`` class communicates with the main application via callbacks.
All UI updates must be dispatched back to the Tk main thread.
"""

from __future__ import annotations

import threading
from typing import Callable

try:
    import pystray
    from PIL import Image, ImageDraw
    _PYSTRAY_AVAILABLE = True
except ImportError:
    _PYSTRAY_AVAILABLE = False


def _make_icon_image(recording: bool = False) -> "Image.Image":
    """Create a simple 64×64 icon image.  Red when recording, grey otherwise."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colour = (200, 30, 30, 255) if recording else (100, 100, 100, 255)
    draw.ellipse([8, 8, size - 8, size - 8], fill=colour)
    return img


class TrayIcon:
    """Manages the Windows system tray icon.

    Parameters
    ----------
    app_title:
        Application name shown in the tray menu.
    on_open:
        Called when the user clicks "Open".
    on_start_recording:
        Called when "Start Recording" is clicked from the tray.
    on_stop_recording:
        Called when "Stop Recording" is clicked from the tray.
    on_exit:
        Called when "Exit" is clicked.  The callback is responsible for
        calling :meth:`stop` and destroying the main window.
    t:
        Translation callable ``t(key, **kwargs) → str``.
    """

    def __init__(
        self,
        app_title: str = "Speech Recognition Program",
        on_open: Callable[[], None] | None = None,
        on_start_recording: Callable[[], None] | None = None,
        on_stop_recording: Callable[[], None] | None = None,
        on_exit: Callable[[], None] | None = None,
        t: Callable[[str], str] | None = None,
    ) -> None:
        self._app_title = app_title
        self._on_open = on_open or (lambda: None)
        self._on_start = on_start_recording or (lambda: None)
        self._on_stop = on_stop_recording or (lambda: None)
        self._on_exit = on_exit or (lambda: None)
        self._t = t or (lambda k, **kw: k)
        self._icon: "pystray.Icon | None" = None
        self._thread: threading.Thread | None = None
        self._recording = False
        self._mode = "Regular"
        self._active = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the tray icon in a daemon thread."""
        if not _PYSTRAY_AVAILABLE or self._active:
            return
        self._active = True
        self._icon = pystray.Icon(
            self._app_title,
            icon=_make_icon_image(False),
            title=self._app_title,
            menu=self._build_menu(),
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop and remove the tray icon."""
        self._active = False
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------

    def set_recording(self, recording: bool) -> None:
        self._recording = recording
        if self._icon and _PYSTRAY_AVAILABLE:
            try:
                self._icon.icon = _make_icon_image(recording)
                self._icon.menu = self._build_menu()
                self._icon.update_menu()
            except Exception:
                pass

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if self._icon and _PYSTRAY_AVAILABLE:
            try:
                self._icon.menu = self._build_menu()
                self._icon.update_menu()
            except Exception:
                pass

    def notify(self, message: str) -> None:
        """Show a balloon notification (T-110)."""
        if self._icon and _PYSTRAY_AVAILABLE:
            try:
                self._icon.notify(message, self._app_title)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Menu construction
    # ------------------------------------------------------------------

    def _build_menu(self) -> "pystray.Menu":
        t = self._t
        items = [
            pystray.MenuItem(t("tray_open"), self._on_open, default=True),
            pystray.MenuItem(
                t("tray_mode", mode=self._mode), None, enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                t("tray_start"),
                self._on_start,
                enabled=not self._recording,
            ),
            pystray.MenuItem(
                t("tray_stop"),
                self._on_stop,
                enabled=self._recording,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t("tray_exit"), self._on_exit),
        ]
        return pystray.Menu(*items)
